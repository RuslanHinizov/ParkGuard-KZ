"""
night_detector.py — Gece Modu Tespiti

Kamera frame parlaklığına göre gece modunu tespit eder.
Gece modunda detection eşikleri ayarlanır.
"""

import cv2
import logging
import numpy as np

logger = logging.getLogger(__name__)

# Varsayılan eşikler
NIGHT_BRIGHTNESS_THRESHOLD = 60   # Bu değerin altı = gece
NIGHT_CONF_REDUCTION = 0.10       # Gece modunda confidence %10 düşür
CHECK_EVERY_N_FRAMES = 30         # Her 30 frame'de bir kontrol et (performans)

_current_mode: dict[int, bool] = {}  # camera_id → is_night
_frame_counter: dict[int, int] = {}  # camera_id → frame count


def is_night(frame: np.ndarray, camera_id: int = 0) -> bool:
    """
    Frame'in gece modunda olup olmadığını kontrol et.
    Her N frame'de bir hesaplar, arada cache kullanır.
    """
    global _frame_counter

    # Frame counter
    _frame_counter[camera_id] = _frame_counter.get(camera_id, 0) + 1

    # Her N frame'de bir kontrol
    if _frame_counter[camera_id] % CHECK_EVERY_N_FRAMES != 0:
        return _current_mode.get(camera_id, False)

    try:
        # Grayscale'e çevir ve ortalama parlaklığı hesapla
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        brightness = float(np.mean(gray))

        night = brightness < NIGHT_BRIGHTNESS_THRESHOLD
        prev = _current_mode.get(camera_id)
        _current_mode[camera_id] = night

        # Mod değiştiğinde logla
        if prev is not None and prev != night:
            mode_str = "GECE" if night else "GUNDUZ"
            logger.info(
                f"Kamera {camera_id}: {mode_str} modu (parlaklik: {brightness:.0f})"
            )

        return night
    except Exception:
        return _current_mode.get(camera_id, False)


def get_adjusted_conf(base_conf: float, frame: np.ndarray, camera_id: int = 0) -> float:
    """
    Gece modunda confidence eşiğini ayarla.
    Gece → eşiği yükselt (daha az false positive).
    """
    if is_night(frame, camera_id):
        return min(0.95, base_conf + NIGHT_CONF_REDUCTION)
    return base_conf


def get_night_status() -> dict:
    """Tüm kameraların gece modu durumu."""
    return {cam_id: mode for cam_id, mode in _current_mode.items()}
