"""
whitelist_manager.py — Beyaz Liste (İzinli Plakalar)

İzinli araçlar (personel, engelli, VIP) için beyaz liste.
Beyaz listedeki plakalar alarm tetiklemez.
"""

import uuid
import logging
import sqlite3
import threading
from datetime import datetime
from config import DB_PATH

logger = logging.getLogger(__name__)


class WhitelistManager:

    def __init__(self):
        self._lock = threading.Lock()
        self._cache: set[str] = set()
        self._init_db()
        self._load_cache()

    def _init_db(self) -> None:
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS whitelist (
                    id TEXT PRIMARY KEY,
                    plate TEXT UNIQUE NOT NULL,
                    reason TEXT,
                    added_by TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_whitelist_plate ON whitelist(plate)"
            )
            conn.commit()
        logger.info("Whitelist DB hazir")

    def _load_cache(self) -> None:
        """Tüm beyaz listeyi belleğe yükle (hızlı kontrol için)."""
        try:
            with sqlite3.connect(str(DB_PATH)) as conn:
                rows = conn.execute("SELECT plate FROM whitelist").fetchall()
                self._cache = {row[0].upper() for row in rows}
            logger.info(f"Whitelist: {len(self._cache)} plaka yuklendi")
        except Exception as e:
            logger.error(f"Whitelist yuklenemedi: {e}")

    def is_whitelisted(self, plate_text: str) -> bool:
        """Plaka beyaz listede mi? (O(1) bellek kontrolü)"""
        if not plate_text:
            return False
        return plate_text.upper().strip() in self._cache

    def add_plate(self, plate: str, reason: str = "", added_by: str = "operator") -> dict | None:
        """Beyaz listeye plaka ekle."""
        plate_upper = plate.upper().strip()
        if not plate_upper:
            return None

        entry_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        try:
            with sqlite3.connect(str(DB_PATH)) as conn:
                conn.execute(
                    "INSERT INTO whitelist (id, plate, reason, added_by, created_at) VALUES (?,?,?,?,?)",
                    (entry_id, plate_upper, reason, added_by, now),
                )
                conn.commit()

            with self._lock:
                self._cache.add(plate_upper)

            logger.info(f"Whitelist: +{plate_upper} ({reason})")
            return {
                "id": entry_id,
                "plate": plate_upper,
                "reason": reason,
                "added_by": added_by,
                "created_at": now,
            }
        except sqlite3.IntegrityError:
            logger.warning(f"Whitelist: {plate_upper} zaten mevcut")
            return None
        except Exception as e:
            logger.error(f"Whitelist ekleme hatasi: {e}")
            return None

    def remove_plate(self, plate: str) -> bool:
        """Beyaz listeden plaka sil."""
        plate_upper = plate.upper().strip()
        try:
            with sqlite3.connect(str(DB_PATH)) as conn:
                cursor = conn.execute(
                    "DELETE FROM whitelist WHERE plate = ?", (plate_upper,)
                )
                conn.commit()
                deleted = cursor.rowcount > 0

            if deleted:
                with self._lock:
                    self._cache.discard(plate_upper)
                logger.info(f"Whitelist: -{plate_upper}")

            return deleted
        except Exception as e:
            logger.error(f"Whitelist silme hatasi: {e}")
            return False

    def get_all(self) -> list[dict]:
        """Tüm beyaz listeyi döndür."""
        try:
            with sqlite3.connect(str(DB_PATH)) as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    "SELECT * FROM whitelist ORDER BY created_at DESC"
                ).fetchall()
                return [dict(r) for r in rows]
        except Exception as e:
            logger.error(f"Whitelist sorgu hatasi: {e}")
            return []


whitelist_mgr = WhitelistManager()
