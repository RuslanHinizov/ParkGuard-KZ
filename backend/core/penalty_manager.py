"""
penalty_manager.py — Ceza / Para Cezası Yönetimi

Alarm oluştuğunda (plaka tespit edilmişse) ceza kuyruğuna otomatik ekler.
Operatör kuyruğu inceleyip gönderir veya iptal eder.

Ceza durumları:
  pending   → Kuyruğa eklendi, henüz gönderilmedi
  sent      → Başarıyla gönderildi
  cancelled → İptal edildi (operatör kararıyla)

Gelecekte Gemma AI doğrulaması eklendiğinde:
  pending → ai_verified=True  → auto-sent (otomatik)
  pending → ai_verified=False → manuel inceleme
"""

import uuid
import sqlite3
import logging
from datetime import datetime
from config import DB_PATH

logger = logging.getLogger(__name__)

# KZ MRP (Aylık Hesaplama Göstergesi) — 2024 değeri
MRP_2024 = 3_692  # KZT


class PenaltyManager:

    def __init__(self):
        self._init_db()

    def _init_db(self) -> None:
        """SQLite ceza tablosunu oluştur."""
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS penalties (
                    id          TEXT PRIMARY KEY,
                    alarm_id    TEXT NOT NULL UNIQUE,
                    plate       TEXT NOT NULL,
                    camera_id   INTEGER,
                    zone_name   TEXT,
                    duration_sec INTEGER,
                    screenshot  TEXT,
                    status      TEXT DEFAULT 'pending',
                    fine_amount REAL DEFAULT 0,
                    created_at  TEXT NOT NULL,
                    sent_at     TEXT,
                    notes       TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_penalties_status ON penalties(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_penalties_plate  ON penalties(plate)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_penalties_alarm  ON penalties(alarm_id)")
            conn.commit()
        logger.info("Penalty DB hazir")

    # ─────────────────────────────────────────────
    #  YARDIMCI
    # ─────────────────────────────────────────────

    def _calculate_fine(self, duration_sec: int) -> float:
        """
        İhlal süresine göre ceza miktarı hesapla (KZT).
        KZ КоАП Madde 462'ye dayalı basit hesaplama:
          <  10 dak  →  5 MRP
          < 30 dak  → 10 MRP
          ≥ 30 dak  → 15 MRP
        """
        if duration_sec < 600:
            return MRP_2024 * 5
        elif duration_sec < 1800:
            return MRP_2024 * 10
        else:
            return MRP_2024 * 15

    # ─────────────────────────────────────────────
    #  KUYRUK YÖNETİMİ
    # ─────────────────────────────────────────────

    def add_to_queue(self, alarm: dict) -> dict | None:
        """
        Alarm'dan ceza kaydı oluştur ve kuyruğa ekle.
        alarm_id üzerinde UNIQUE kısıtı var — aynı alarm iki kez eklenemez.
        """
        plate = alarm.get("plate")
        if not plate:
            return None  # Plaka yoksa ceza olmaz

        penalty_id = str(uuid.uuid4())
        fine_amount = self._calculate_fine(alarm.get("duration_sec", 0))
        now = datetime.utcnow().isoformat()

        penalty = {
            "id": penalty_id,
            "alarm_id": alarm["id"],
            "plate": plate,
            "camera_id": alarm.get("camera_id"),
            "zone_name": alarm.get("zone_name", ""),
            "duration_sec": alarm.get("duration_sec", 0),
            "screenshot": alarm.get("screenshot", ""),
            "status": "pending",
            "fine_amount": fine_amount,
            "created_at": now,
            "sent_at": None,
            "notes": "",
        }

        try:
            with sqlite3.connect(str(DB_PATH)) as conn:
                cursor = conn.execute(
                    """INSERT OR IGNORE INTO penalties
                       (id, alarm_id, plate, camera_id, zone_name, duration_sec,
                        screenshot, status, fine_amount, created_at, sent_at, notes)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        penalty["id"], penalty["alarm_id"], penalty["plate"],
                        penalty["camera_id"], penalty["zone_name"], penalty["duration_sec"],
                        penalty["screenshot"], penalty["status"], penalty["fine_amount"],
                        penalty["created_at"], penalty["sent_at"], penalty["notes"],
                    ),
                )
                conn.commit()
                if cursor.rowcount == 0:
                    conn.row_factory = sqlite3.Row
                    existing = conn.execute(
                        "SELECT * FROM penalties WHERE alarm_id = ?",
                        (penalty["alarm_id"],),
                    ).fetchone()
                    return dict(existing) if existing else None
            logger.info(
                f"Ceza kuyruğu: {plate} | {fine_amount:,.0f} KZT | "
                f"Kamera {alarm.get('camera_id')} | {alarm.get('zone_name')}"
            )
            return penalty
        except Exception as e:
            logger.error(f"Ceza kuyrugu ekleme hatasi: {e}")
            return None

    def get_penalties(
        self,
        status: str | None = None,
        plate: str | None = None,
        alarm_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        """Ceza listesi sorgula (filtreli, sayfalı)."""
        try:
            with sqlite3.connect(str(DB_PATH)) as conn:
                conn.row_factory = sqlite3.Row
                clauses, params = [], []

                if status:
                    clauses.append("status = ?")
                    params.append(status)
                if plate:
                    clauses.append("plate LIKE ?")
                    params.append(f"%{plate}%")
                if alarm_id:
                    clauses.append("alarm_id = ?")
                    params.append(alarm_id)

                where = " AND ".join(clauses) if clauses else "1=1"
                total = conn.execute(
                    f"SELECT COUNT(*) FROM penalties WHERE {where}", params
                ).fetchone()[0]
                rows = conn.execute(
                    f"SELECT * FROM penalties WHERE {where} ORDER BY created_at DESC LIMIT ? OFFSET ?",
                    params + [limit, offset],
                ).fetchall()
                return [dict(r) for r in rows], total
        except Exception as e:
            logger.error(f"Penalty sorgu hatasi: {e}")
            return [], 0

    def get_penalty(self, penalty_id: str) -> dict | None:
        try:
            with sqlite3.connect(str(DB_PATH)) as conn:
                conn.row_factory = sqlite3.Row
                row = conn.execute(
                    "SELECT * FROM penalties WHERE id = ?", (penalty_id,)
                ).fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Penalty getirme hatasi: {e}")
            return None

    def get_stats(self) -> dict:
        """Durum bazlı özet istatistik."""
        try:
            with sqlite3.connect(str(DB_PATH)) as conn:
                rows = conn.execute(
                    """SELECT status,
                              COUNT(*)        AS cnt,
                              SUM(fine_amount) AS total_amount
                       FROM penalties
                       GROUP BY status"""
                ).fetchall()
                stats = {
                    "pending":   {"count": 0, "total_amount": 0.0},
                    "sent":      {"count": 0, "total_amount": 0.0},
                    "cancelled": {"count": 0, "total_amount": 0.0},
                }
                for row in rows:
                    s = row[0]
                    if s in stats:
                        stats[s] = {"count": row[1], "total_amount": float(row[2] or 0)}
                return stats
        except Exception as e:
            logger.error(f"Penalty stats hatasi: {e}")
            return {}

    # ─────────────────────────────────────────────
    #  EYLEMLER
    # ─────────────────────────────────────────────

    def send_penalty(self, penalty_id: str) -> dict:
        """
        Ceza gönder.

        Şu an: mock gönderim (DB güncelle + log).
        Gerçek entegrasyon için bu fonksiyonda e-gov API çağrısı yapılır:
            response = egov_client.send_fine(plate, amount, evidence_url)
        """
        try:
            with sqlite3.connect(str(DB_PATH)) as conn:
                conn.row_factory = sqlite3.Row
                row = conn.execute(
                    "SELECT * FROM penalties WHERE id = ?", (penalty_id,)
                ).fetchone()
                if not row:
                    return {"success": False, "message": "Ceza bulunamadi"}
                p = dict(row)

                if p["status"] == "sent":
                    return {"success": False, "message": "Bu ceza zaten gönderildi"}
                if p["status"] == "cancelled":
                    return {"success": False, "message": "İptal edilmiş ceza gönderilemez"}

                # ── GERÇEK ENTEGRASYON NOKTASI ──────────────────────────────
                # Buraya Kazakistan e-gov / КоАП API bağlantısı gelecek:
                #
                # result = egov_api.create_fine(
                #     plate_number = p["plate"],
                #     amount_kzt   = p["fine_amount"],
                #     violation_at = p["created_at"],
                #     camera_id    = p["camera_id"],
                #     zone_name    = p["zone_name"],
                #     evidence_url = f"https://korgen.kz/screenshots/{p['screenshot']}",
                # )
                # if not result.success:
                #     return {"success": False, "message": result.error}
                # ─────────────────────────────────────────────────────────────

                sent_at = datetime.utcnow().isoformat()
                conn.execute(
                    "UPDATE penalties SET status = 'sent', sent_at = ? WHERE id = ?",
                    (sent_at, penalty_id),
                )
                conn.commit()

            logger.info(f"Ceza gönderildi: {p['plate']} — {p['fine_amount']:,.0f} KZT")
            return {
                "success": True,
                "message": f"Ceza başarıyla gönderildi: {p['fine_amount']:,.0f} KZT",
                "plate": p["plate"],
                "fine_amount": p["fine_amount"],
                "sent_at": sent_at,
            }
        except Exception as e:
            logger.error(f"Ceza gönderim hatasi: {e}")
            return {"success": False, "message": str(e)}

    def cancel_penalty(self, penalty_id: str, reason: str = "") -> bool:
        """Bekleyen cezayı iptal et."""
        try:
            with sqlite3.connect(str(DB_PATH)) as conn:
                cursor = conn.execute(
                    "UPDATE penalties SET status = 'cancelled', notes = ? "
                    "WHERE id = ? AND status = 'pending'",
                    (reason, penalty_id),
                )
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Ceza iptal hatasi: {e}")
            return False

    def send_all_pending(self) -> int:
        """Tüm bekleyen cezaları gönder. Toplu işlem."""
        sent = 0
        try:
            with sqlite3.connect(str(DB_PATH)) as conn:
                conn.row_factory = sqlite3.Row
                ids = [
                    r["id"]
                    for r in conn.execute(
                        "SELECT id FROM penalties WHERE status = 'pending'"
                    ).fetchall()
                ]
            for pid in ids:
                if self.send_penalty(pid)["success"]:
                    sent += 1
        except Exception as e:
            logger.error(f"Toplu gönderim hatasi: {e}")
        logger.info(f"Toplu gönderim: {sent} ceza gönderildi")
        return sent


# Modül düzeyinde tekil örnek
penalty_mgr = PenaltyManager()
