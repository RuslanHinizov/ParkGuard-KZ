"""
anomaly_detector.py — Anomali Tespiti

Alarm verilerindeki anormal kalıpları tespit eder:
- Tekrarlayan ihlalciler (aynı plaka, birden fazla gün)
- Ani artışlar (saatlik ortalamanın 2x üzerinde)
"""

import uuid
import json
import logging
import sqlite3
from datetime import datetime
from config import DB_PATH

logger = logging.getLogger(__name__)


class AnomalyDetector:

    def __init__(self):
        self._init_db()

    def _init_db(self) -> None:
        try:
            with sqlite3.connect(str(DB_PATH)) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS anomalies (
                        id TEXT PRIMARY KEY,
                        anomaly_type TEXT,
                        plate TEXT,
                        description TEXT,
                        data TEXT,
                        created_at TEXT NOT NULL,
                        acknowledged INTEGER DEFAULT 0
                    )
                """)
                conn.commit()
            logger.info("Anomaly DB hazir")
        except Exception as e:
            logger.error(f"Anomaly DB init hatasi: {e}")

    def detect_repeat_offenders(self, days: int = 7, min_days: int = 3) -> list[dict]:
        """Son N günde M+ farklı günde ihlal yapan plakalar."""
        try:
            with sqlite3.connect(str(DB_PATH)) as conn:
                rows = conn.execute(
                    """
                    SELECT plate,
                           COUNT(*) as total,
                           COUNT(DISTINCT date(created_at)) as unique_days,
                           GROUP_CONCAT(DISTINCT strftime('%H', created_at)) as hours,
                           MIN(created_at) as first_seen,
                           MAX(created_at) as last_seen
                    FROM alarms
                    WHERE plate IS NOT NULL
                      AND created_at >= date('now', ?)
                    GROUP BY plate
                    HAVING unique_days >= ?
                    ORDER BY total DESC
                    LIMIT 20
                    """,
                    (f"-{days} days", min_days),
                ).fetchall()

            anomalies = []
            for row in rows:
                plate, total, days_count, hours, first, last = row
                anomaly = {
                    "id": str(uuid.uuid4()),
                    "anomaly_type": "repeat_offender",
                    "plate": plate,
                    "description": f"Plaka {plate}: {days_count} gun icinde {total} ihlal ({hours} saatleri)",
                    "data": json.dumps({
                        "total_violations": total,
                        "unique_days": days_count,
                        "hours": hours,
                        "first_seen": first,
                        "last_seen": last,
                    }),
                    "created_at": datetime.utcnow().isoformat(),
                }
                anomalies.append(anomaly)

            return anomalies
        except Exception as e:
            logger.error(f"Repeat offender tespiti hatasi: {e}")
            return []

    def detect_spikes(self, threshold_multiplier: float = 2.0) -> list[dict]:
        """Son 24 saatte saatlik ortalamadan N kat fazla ihlal olan saatler."""
        try:
            with sqlite3.connect(str(DB_PATH)) as conn:
                # Son 7 günün saatlik ortalaması
                avg_rows = conn.execute(
                    """
                    SELECT CAST(strftime('%H', created_at) AS INTEGER) as hour,
                           CAST(COUNT(*) AS REAL) / 7.0 as avg_count
                    FROM alarms
                    WHERE created_at >= date('now', '-7 days')
                    GROUP BY hour
                    """
                ).fetchall()
                averages = {row[0]: row[1] for row in avg_rows}

                # Bugünün saatlik dağılımı
                today_rows = conn.execute(
                    """
                    SELECT CAST(strftime('%H', created_at) AS INTEGER) as hour,
                           COUNT(*) as cnt
                    FROM alarms
                    WHERE created_at >= date('now')
                    GROUP BY hour
                    """
                ).fetchall()

            anomalies = []
            for row in today_rows:
                hour, count = row
                avg = averages.get(hour, 0)
                if avg > 0 and count > avg * threshold_multiplier:
                    anomaly = {
                        "id": str(uuid.uuid4()),
                        "anomaly_type": "spike",
                        "plate": None,
                        "description": f"Saat {hour:02d}:00'da {count} ihlal (ortalama: {avg:.1f}, {count/avg:.1f}x)",
                        "data": json.dumps({
                            "hour": hour,
                            "count": count,
                            "average": round(avg, 1),
                            "multiplier": round(count / avg, 1),
                        }),
                        "created_at": datetime.utcnow().isoformat(),
                    }
                    anomalies.append(anomaly)

            return anomalies
        except Exception as e:
            logger.error(f"Spike tespiti hatasi: {e}")
            return []

    def run_full_scan(self) -> list[dict]:
        """Tüm anomali taramalarını çalıştır ve kaydet."""
        all_anomalies = []
        all_anomalies.extend(self.detect_repeat_offenders())
        all_anomalies.extend(self.detect_spikes())

        # Veritabanına kaydet
        if all_anomalies:
            self._save_anomalies(all_anomalies)
            logger.info(f"Anomali taramasi: {len(all_anomalies)} anomali bulundu")

        return all_anomalies

    def _save_anomalies(self, anomalies: list[dict]) -> None:
        try:
            with sqlite3.connect(str(DB_PATH)) as conn:
                for a in anomalies:
                    conn.execute(
                        "INSERT OR IGNORE INTO anomalies VALUES (?,?,?,?,?,?,?)",
                        (a["id"], a["anomaly_type"], a.get("plate"),
                         a["description"], a.get("data"), a["created_at"], 0),
                    )
                conn.commit()
        except Exception as e:
            logger.error(f"Anomali kaydi hatasi: {e}")

    def get_anomalies(self, limit: int = 50) -> list[dict]:
        """Son anomalileri döndür."""
        try:
            with sqlite3.connect(str(DB_PATH)) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    "SELECT * FROM anomalies ORDER BY created_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()
                return [dict(r) for r in rows]
        except Exception:
            return []

    def get_unacknowledged_count(self) -> int:
        """Görülmemiş anomali sayısı."""
        try:
            with sqlite3.connect(str(DB_PATH)) as conn:
                row = conn.execute(
                    "SELECT COUNT(*) FROM anomalies WHERE acknowledged = 0"
                ).fetchone()
                return row[0] if row else 0
        except Exception:
            return 0

    def acknowledge(self, anomaly_id: str) -> bool:
        """Anomaliyi görüldü olarak işaretle."""
        try:
            with sqlite3.connect(str(DB_PATH)) as conn:
                cursor = conn.execute(
                    "UPDATE anomalies SET acknowledged = 1 WHERE id = ?",
                    (anomaly_id,),
                )
                conn.commit()
                return cursor.rowcount > 0
        except Exception:
            return False


anomaly_detector = AnomalyDetector()
