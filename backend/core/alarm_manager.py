"""
alarm_manager.py — Alarm Yönetim Modülü

AMAÇ: Violation logic. Araç N saniye bölgede kalırsa alarm üret.
      Screenshot kaydet.
      Redis pub/sub ile yayınla.
      SQLite'a kaydet.
      Aynı araç için cooldown uygula.

Violation State Machine:
  [None] → araç bölgeye girer → [PENDING - timer başlar]
  [PENDING] → 5 dakika (300sn) geçer → [ALARM OLUŞTUR]
  [ALARM] → araç çıkar → [AUTO_RESOLVED]
  [ALARM] → operatör tıklar → [MANUALLY_RESOLVED]

Cooldown:
  Araç alarm → çıkar → tekrar girer → 600sn cooldown → spam önleme
"""

import uuid
import time
import json
import cv2
import logging
import sqlite3
import threading
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from collections import deque
from config import (
    DB_PATH, SCREENSHOTS_DIR,
    VIOLATION_MIN_DURATION_SEC, ALARM_COOLDOWN_SEC,
    REDIS_HOST, REDIS_PORT, REDIS_DB,
    GENERIC_VEHICLE_LABEL,
    OCR_REPLACE_MARGIN,
    OCR_STICKY_CONFIDENCE,
)
from core.settings_manager import settings_mgr

logger = logging.getLogger(__name__)


class AlarmManager:

    def __init__(self):
        # {track_id: {"first_seen": float, "zone": dict, "detection": dict, "plate": dict|None, "alarm_sent": bool}}
        self.violations: dict[int, dict] = {}
        self.cooldowns: dict[int, float] = {}  # track_id → last_alarm_time
        self.recent_alarms: deque = deque(maxlen=100)  # Son alarmlar (in-memory)
        self._alarm_callback = None  # WebSocket broadcast için callback
        self._lock = threading.Lock()  # violations/cooldowns erişimi için

        self._init_db()
        self._init_redis()

        SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    def set_alarm_callback(self, callback) -> None:
        """Yeni alarm oluştuğunda çağrılacak async callback."""
        self._alarm_callback = callback

    def _init_db(self) -> None:
        """SQLite alarm tablosunu oluştur."""
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS alarms (
                    id TEXT PRIMARY KEY,
                    camera_id INTEGER NOT NULL,
                    track_id INTEGER,
                    plate TEXT,
                    plate_conf REAL,
                    vehicle_class TEXT,
                    zone_id TEXT,
                    zone_name TEXT,
                    duration_sec INTEGER,
                    status TEXT DEFAULT 'active',
                    screenshot TEXT,
                    plate_screenshot TEXT,
                    created_at TEXT NOT NULL,
                    resolved_at TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_alarms_camera ON alarms(camera_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_alarms_status ON alarms(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_alarms_plate ON alarms(plate)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_alarms_created ON alarms(created_at)")
            columns = {
                row[1]
                for row in conn.execute("PRAGMA table_info(alarms)").fetchall()
            }
            if "plate_screenshot" not in columns:
                conn.execute("ALTER TABLE alarms ADD COLUMN plate_screenshot TEXT")
            conn.commit()
        logger.info("Alarm DB hazir")

    def _init_redis(self) -> None:
        """Redis bağlantısı kur. Bağlanamazsa in-memory çalış."""
        try:
            import redis
            self.redis = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
            )
            self.redis.ping()
            logger.info("Redis baglandi")
        except Exception:
            self.redis = None
            logger.warning("Redis baglanamadi, in-memory kullanilacak")

    def update(
        self,
        track_id: int,
        detection: dict,
        zone: dict | None,
        plate: dict | None,
    ) -> dict | None:
        """
        Her frame'de çağrılır. Violation durumunu güncelle.

        Returns:
            Oluşturulan alarm dict veya None
        """

        now = time.time()

        with self._lock:
            # Süresi dolmuş cooldown girişlerini temizle (bellek koruması).
            # Her frame'de değil, yalnızca dict büyüdüğünde çalışır.
            if len(self.cooldowns) > 500:
                expired = [
                    tid for tid, t in self.cooldowns.items()
                    if now - t >= ALARM_COOLDOWN_SEC
                ]
                for tid in expired:
                    del self.cooldowns[tid]

            if zone is None:
                # Bölge dışına çıktı → violation state temizle
                self.violations.pop(track_id, None)
                return None

            # Cooldown kontrolü
            if track_id in self.cooldowns:
                if now - self.cooldowns[track_id] < ALARM_COOLDOWN_SEC:
                    return None

            if track_id not in self.violations:
                self.violations[track_id] = {
                    "first_seen": now,
                    "zone": zone,
                    "detection": detection,
                    "plate": plate,
                    "alarm_sent": False,
                }
            else:
                # Plate güncellemesi (ilk seferde bulunamayabilir)
                current_plate = self.violations[track_id].get("plate")
                if self._should_replace_plate(current_plate, plate):
                    self.violations[track_id]["plate"] = plate
                # Detection güncelle (en güncel frame)
                self.violations[track_id]["detection"] = detection

            duration = now - self.violations[track_id]["first_seen"]

            # Kameraya özel ihlal süresi (settings_manager'dan, yoksa global config)
            camera_id = detection.get("camera_id", 0)
            threshold = settings_mgr.get_camera_violation_duration(camera_id)

            if duration >= threshold and not self.violations[track_id]["alarm_sent"]:
                # Beyaz liste kontrolü
                viol_plate = self.violations[track_id].get("plate")
                if viol_plate:
                    from core.whitelist_manager import whitelist_mgr
                    if whitelist_mgr.is_whitelisted(viol_plate.get("text", "")):
                        logger.info(f"Whitelist: {viol_plate['text']} — alarm atlandı")
                        self.violations[track_id]["alarm_sent"] = True
                        return None

                alarm = self._create_alarm(track_id, duration)
                self.violations[track_id]["alarm_sent"] = True
                self.cooldowns[track_id] = now
                return alarm

        return None

    def _create_alarm(self, track_id: int, duration: float) -> dict:
        """Alarm oluştur, kaydet, yayınla."""

        viol = self.violations[track_id]
        det = viol["detection"]
        plate = viol.get("plate")
        zone = viol["zone"]

        alarm_id = str(uuid.uuid4())

        # Screenshot path'i belirle — disk yazımı arka planda yapılır
        now_utc = datetime.utcnow()
        date_str = now_utc.strftime("%Y-%m-%d")
        filename = f"alarm_{alarm_id[:8]}.jpg"
        plate_filename = f"alarm_{alarm_id[:8]}_plate.jpg"
        abs_screenshot_path = SCREENSHOTS_DIR / date_str / filename
        abs_plate_screenshot_path = SCREENSHOTS_DIR / date_str / plate_filename
        # Göreceli path DB'de saklanır → Docker/Windows/Linux taşınabilirliği
        rel_screenshot_path = f"screenshots/{date_str}/{filename}"
        rel_plate_screenshot_path = f"screenshots/{date_str}/{plate_filename}"

        # Frame kopyasını al (inference loop ilerleyecek, orijinal değişebilir)
        frame_copy = det["frame"].copy()
        bbox_copy = list(det["bbox"])
        plate_copy = self._clone_plate_result(plate)
        has_plate_crop = (
            bool(plate_copy)
            and isinstance(plate_copy.get("plate_crop"), np.ndarray)
            and plate_copy["plate_crop"].size > 0
        ) or (
            bool(plate_copy)
            and plate_copy.get("plate_bbox") is not None
        )

        # Arka planda kaydet — inference loop'u bloklamaz
        threading.Thread(
            target=self._save_images_sync,
            args=(abs_screenshot_path, abs_plate_screenshot_path, frame_copy, bbox_copy, plate_copy),
            daemon=True,
        ).start()

        alarm = {
            "id": alarm_id,
            "camera_id": det["camera_id"],
            "track_id": track_id,
            "plate": plate["text"] if plate else None,
            "plate_conf": plate["confidence"] if plate else None,
            "vehicle_class": det.get("class_name", GENERIC_VEHICLE_LABEL),
            "zone_id": zone["id"],
            "zone_name": zone["name"],
            "duration_sec": int(duration),
            "status": "active",
            "screenshot": rel_screenshot_path,
            "plate_screenshot": rel_plate_screenshot_path if has_plate_crop else None,
            "created_at": now_utc.isoformat(),
            "resolved_at": None,
        }

        # SQLite kaydet
        self._save_to_db(alarm)

        # In-memory listeye ekle
        self.recent_alarms.appendleft(alarm)

        # Redis yayınla (pipeline = tek round-trip)
        if self.redis:
            try:
                pipe = self.redis.pipeline()
                pipe.set(f"alarm:{alarm_id}", json.dumps(alarm))
                pipe.publish("alarms", json.dumps(alarm))
                pipe.lpush("alarm_history", json.dumps(alarm))
                pipe.execute()
            except Exception as e:
                logger.error(f"Redis yayin hatasi: {e}")

        plate_text = plate["text"] if plate else "Plaka yok"
        logger.info(
            f"ALARM: Kamera {det['camera_id']} | {zone['name']} | {plate_text}"
        )

        # Plaka tespit edilmişse ceza kuyruğuna otomatik ekle
        if alarm["plate"]:
            threading.Thread(
                target=self._add_to_penalty_queue,
                args=(alarm,),
                daemon=True,
            ).start()

        return alarm

    def _add_to_penalty_queue(self, alarm: dict) -> None:
        """Alarm'ı ceza kuyruğuna ekle (arka plan thread'inde)."""
        try:
            from core.penalty_manager import penalty_mgr
            penalty_mgr.add_to_queue(alarm)
        except Exception as e:
            logger.error(f"Ceza kuyrugu ekleme hatasi: {e}")

    def _save_images_sync(
        self,
        vehicle_path: Path,
        plate_path: Path,
        frame: np.ndarray,
        bbox: list[int],
        plate: dict | None,
    ) -> None:
        """Araç screenshot ve varsa plaka crop'ını kaydet."""
        try:
            vehicle_path.parent.mkdir(parents=True, exist_ok=True)
            x1, y1, x2, y2 = bbox
            h, w = frame.shape[:2]

            # Araç etrafına %40 padding ekle (en az 80px)
            pad_x = max(int((x2 - x1) * 0.4), 80)
            pad_y = max(int((y2 - y1) * 0.4), 80)
            cx1 = max(0, x1 - pad_x)
            cy1 = max(0, y1 - pad_y)
            cx2 = min(w, x2 + pad_x)
            cy2 = min(h, y2 + pad_y)

            cropped = frame[cy1:cy2, cx1:cx2].copy()
            # Kırpılmış koordinatlara göre bbox çiz
            cv2.rectangle(
                cropped,
                (x1 - cx1, y1 - cy1),
                (x2 - cx1, y2 - cy1),
                (0, 0, 255), 3,
            )
            cv2.imwrite(str(vehicle_path), cropped, [cv2.IMWRITE_JPEG_QUALITY, 90])

            plate_crop = plate.get("plate_crop") if plate else None
            if not (isinstance(plate_crop, np.ndarray) and plate_crop.size > 0) and plate:
                plate_bbox = plate.get("plate_bbox")
                if plate_bbox:
                    vx1, vy1, vx2, vy2 = bbox
                    px1, py1, px2, py2 = plate_bbox
                    vehicle_crop = frame[max(0, vy1):min(h, vy2), max(0, vx1):min(w, vx2)]
                    if vehicle_crop.size > 0:
                        vh, vw = vehicle_crop.shape[:2]
                        px1 = max(0, min(vw, px1))
                        py1 = max(0, min(vh, py1))
                        px2 = max(0, min(vw, px2))
                        py2 = max(0, min(vh, py2))
                        plate_crop = vehicle_crop[py1:py2, px1:px2].copy()

            if isinstance(plate_crop, np.ndarray) and plate_crop.size > 0:
                cv2.imwrite(str(plate_path), plate_crop, [cv2.IMWRITE_JPEG_QUALITY, 95])
        except Exception as e:
            logger.error(f"Screenshot kaydedilemedi ({vehicle_path}): {e}")

    def _clone_plate_result(self, plate: dict | None) -> dict | None:
        if not plate:
            return None
        cloned = {}
        for key, value in plate.items():
            if isinstance(value, np.ndarray):
                cloned[key] = value.copy()
            elif isinstance(value, list):
                cloned[key] = list(value)
            else:
                cloned[key] = value
        return cloned

    def _should_replace_plate(self, current: dict | None, candidate: dict | None) -> bool:
        if not candidate:
            return False
        if not current:
            return True
        if current.get("text") == candidate.get("text"):
            return self._plate_rank(candidate) >= self._plate_rank(current)

        current_score = float(current.get("score", current.get("confidence", 0.0)))
        candidate_score = float(candidate.get("score", candidate.get("confidence", 0.0)))
        current_votes = int(current.get("votes", 1) or 1)
        candidate_votes = int(candidate.get("votes", 1) or 1)

        if (
            current.get("stable")
            and float(current.get("confidence", 0.0)) >= OCR_STICKY_CONFIDENCE
            and candidate_score < current_score + OCR_REPLACE_MARGIN
            and candidate_votes <= current_votes
        ):
            return False

        return self._plate_rank(candidate) > self._plate_rank(current)

    def _plate_rank(self, plate: dict | None) -> tuple:
        if not plate:
            return (0, 0, 0.0, 0.0, 0.0, 0)
        return (
            int(bool(plate.get("stable"))),
            int(plate.get("votes", 1) or 1),
            round(float(plate.get("score", plate.get("confidence", 0.0))), 4),
            round(float(plate.get("confidence", 0.0)), 4),
            round(float(plate.get("quality", 0.0)), 4),
            int(plate.get("plate_area", 0) or 0),
        )

    def _save_to_db(self, alarm: dict) -> None:
        """SQLite'a alarm kaydet."""
        try:
            with sqlite3.connect(str(DB_PATH)) as conn:
                conn.execute(
                    """
                    INSERT INTO alarms (
                        id, camera_id, track_id, plate, plate_conf, vehicle_class,
                        zone_id, zone_name, duration_sec, status, screenshot,
                        plate_screenshot, created_at, resolved_at
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        alarm["id"], alarm["camera_id"], alarm["track_id"],
                        alarm["plate"], alarm["plate_conf"], alarm["vehicle_class"],
                        alarm["zone_id"], alarm["zone_name"], alarm["duration_sec"],
                        alarm["status"], alarm["screenshot"], alarm["plate_screenshot"], alarm["created_at"],
                        alarm["resolved_at"],
                    ),
                )
                conn.commit()
        except Exception as e:
            logger.error(f"DB kayit hatasi: {e}")

    # === QUERY METODLARİ ===

    def get_alarms(
        self,
        camera_id: int | None = None,
        status: str | None = None,
        plate: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        """Alarm listesi sorgula."""
        try:
            with sqlite3.connect(str(DB_PATH)) as conn:
                conn.row_factory = sqlite3.Row

                where_clauses = []
                params = []

                if camera_id is not None:
                    where_clauses.append("camera_id = ?")
                    params.append(camera_id)
                if status:
                    where_clauses.append("status = ?")
                    params.append(status)
                if plate:
                    where_clauses.append("plate LIKE ?")
                    params.append(f"%{plate}%")
                if date_from:
                    where_clauses.append("created_at >= ?")
                    params.append(date_from)
                if date_to:
                    where_clauses.append("created_at <= ?")
                    params.append(date_to)

                where = " AND ".join(where_clauses) if where_clauses else "1=1"

                # Toplam sayı
                count_row = conn.execute(
                    f"SELECT COUNT(*) FROM alarms WHERE {where}", params
                ).fetchone()
                total = count_row[0]

                # Sayfalı sonuçlar
                rows = conn.execute(
                    f"SELECT * FROM alarms WHERE {where} ORDER BY created_at DESC LIMIT ? OFFSET ?",
                    params + [limit, offset],
                ).fetchall()

                alarms = [dict(row) for row in rows]
                return alarms, total

        except Exception as e:
            logger.error(f"DB sorgu hatasi: {e}")
            return [], 0

    def get_alarm(self, alarm_id: str) -> dict | None:
        """Tek alarm detayı."""
        try:
            with sqlite3.connect(str(DB_PATH)) as conn:
                conn.row_factory = sqlite3.Row
                row = conn.execute(
                    "SELECT * FROM alarms WHERE id = ?", (alarm_id,)
                ).fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"DB sorgu hatasi: {e}")
            return None

    def resolve_alarm(self, alarm_id: str) -> dict | None:
        """Alarmı çözüldü olarak işaretle."""
        try:
            resolved_at = datetime.utcnow().isoformat()
            with sqlite3.connect(str(DB_PATH)) as conn:
                conn.execute(
                    "UPDATE alarms SET status = 'resolved', resolved_at = ? WHERE id = ?",
                    (resolved_at, alarm_id),
                )
                conn.commit()
                conn.row_factory = sqlite3.Row
                row = conn.execute(
                    "SELECT * FROM alarms WHERE id = ?", (alarm_id,)
                ).fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"DB guncelleme hatasi: {e}")
            return None

    def delete_alarm(self, alarm_id: str) -> bool:
        """Alarm sil."""
        try:
            with sqlite3.connect(str(DB_PATH)) as conn:
                cursor = conn.execute("DELETE FROM alarms WHERE id = ?", (alarm_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"DB silme hatasi: {e}")
            return False

    def get_today_stats(self) -> dict:
        """Bugünün alarm istatistikleri (UTC tarih bazlı)."""
        try:
            today = datetime.utcnow().strftime("%Y-%m-%d")
            with sqlite3.connect(str(DB_PATH)) as conn:
                total = conn.execute(
                    "SELECT COUNT(*) FROM alarms WHERE created_at >= ? AND created_at < date(?, '+1 day')",
                    (today, today),
                ).fetchone()[0]

                active = conn.execute(
                    "SELECT COUNT(*) FROM alarms WHERE created_at >= ? AND created_at < date(?, '+1 day') AND status = 'active'",
                    (today, today),
                ).fetchone()[0]

                resolved = conn.execute(
                    "SELECT COUNT(*) FROM alarms WHERE created_at >= ? AND created_at < date(?, '+1 day') AND status = 'resolved'",
                    (today, today),
                ).fetchone()[0]

                # Kamera bazlı
                by_camera = {}
                rows = conn.execute(
                    "SELECT camera_id, COUNT(*) as cnt FROM alarms WHERE created_at >= ? AND created_at < date(?, '+1 day') GROUP BY camera_id",
                    (today, today),
                ).fetchall()
                for row in rows:
                    by_camera[row[0]] = row[1]

            return {
                "total_alarms": total,
                "active": active,
                "resolved": resolved,
                "by_camera": by_camera,
            }
        except Exception as e:
            logger.error(f"Istatistik hatasi: {e}")
            return {"total_alarms": 0, "active": 0, "resolved": 0, "by_camera": {}}

    def get_hourly_stats(self, date: str | None = None) -> list[dict]:
        """Saatlik alarm dağılımı (UTC tarih bazlı). Tek GROUP BY sorgusuyla 24 saat."""
        try:
            if not date:
                date = datetime.utcnow().strftime("%Y-%m-%d")

            # Gece yarısı sınırları: < yerine < sonraki günün başı — kesirli saniyeler kaçmaz
            next_date = (
                datetime.strptime(date, "%Y-%m-%d") + timedelta(days=1)
            ).strftime("%Y-%m-%d")

            with sqlite3.connect(str(DB_PATH)) as conn:
                rows = conn.execute(
                    """
                    SELECT CAST(strftime('%H', created_at) AS INTEGER) AS hour,
                           COUNT(*) AS count
                    FROM alarms
                    WHERE created_at >= ? AND created_at < ?
                    GROUP BY hour
                    """,
                    (f"{date}T00:00:00", f"{next_date}T00:00:00"),
                ).fetchall()

            counts = {row[0]: row[1] for row in rows}
            return [{"hour": h, "count": counts.get(h, 0)} for h in range(24)]

        except Exception as e:
            logger.error(f"Saatlik istatistik hatasi: {e}")
            return [{"hour": h, "count": 0} for h in range(24)]

    def get_camera_stats(self) -> list[dict]:
        """Kamera bazlı alarm istatistikleri."""
        try:
            with sqlite3.connect(str(DB_PATH)) as conn:
                rows = conn.execute("""
                    SELECT camera_id, COUNT(*) as alarm_count, MAX(created_at) as last_alarm
                    FROM alarms GROUP BY camera_id
                """).fetchall()

            from config import CAMERAS
            cam_names = {c["id"]: c["name"] for c in CAMERAS}

            return [
                {
                    "camera_id": row[0],
                    "name": cam_names.get(row[0], f"Kamera {row[0]}"),
                    "alarm_count": row[1],
                    "last_alarm": row[2],
                }
                for row in rows
            ]
        except Exception as e:
            logger.error(f"Kamera istatistik hatasi: {e}")
            return []
