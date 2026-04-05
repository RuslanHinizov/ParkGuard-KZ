"""
settings_manager.py — Kamera Ayarları Yöneticisi

Her kamera için bağımsız ihlal süresi ayarı.
Ayarlar data/settings.json dosyasında saklanır.
"""

import json
import threading
import logging
from pathlib import Path
from config import DATA_DIR, VIOLATION_MIN_DURATION_SEC, CAMERAS

logger = logging.getLogger(__name__)

SETTINGS_PATH = DATA_DIR / "settings.json"


class SettingsManager:

    def __init__(self):
        self._lock = threading.Lock()
        self._settings = self._load()

    def _load(self) -> dict:
        if SETTINGS_PATH.exists():
            try:
                with open(SETTINGS_PATH, encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"settings.json okunamadi, varsayilan kullanilacak: {e}")

        # Varsayılan: tüm kameralar global config değerini kullanır
        return {
            "cameras": {
                str(cam["id"]): {"violation_duration": VIOLATION_MIN_DURATION_SEC}
                for cam in CAMERAS
            }
        }

    def _save(self) -> None:
        SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(self._settings, f, indent=2, ensure_ascii=False)

    def get_camera_violation_duration(self, camera_id: int) -> int:
        """Kameraya özel ihlal süresi (saniye). Ayarsızsa global değer döner."""
        with self._lock:
            return (
                self._settings
                .get("cameras", {})
                .get(str(camera_id), {})
                .get("violation_duration", VIOLATION_MIN_DURATION_SEC)
            )

    def update_camera_settings(self, camera_id: int, violation_duration: int) -> dict:
        """Kamera ayarını güncelle ve kaydet."""
        with self._lock:
            if "cameras" not in self._settings:
                self._settings["cameras"] = {}
            self._settings["cameras"][str(camera_id)] = {
                "violation_duration": violation_duration
            }
            self._save()
            logger.info(f"Kamera {camera_id} ihlal suresi guncellendi: {violation_duration}sn")
            return dict(self._settings)

    def get_all(self) -> dict:
        with self._lock:
            return dict(self._settings)


# Singleton
settings_mgr = SettingsManager()
