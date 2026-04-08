"""
ParkGuard KZ — Merkezi Konfigürasyon Dosyası
Tüm sistem ayarları tek yerden yönetilir.

Kamera URL'leri için ortam değişkenleri kullanılır:
  CAMERA_1_URL=rtsp://admin:sifre@192.168.1.64:554/Streaming/Channels/101
  CAMERA_2_URL=rtsp://admin:sifre@192.168.1.65:554/Streaming/Channels/101
  CAMERA_3_URL=rtsp://admin:sifre@192.168.1.66:554/Streaming/Channels/101
.env dosyasına yazın veya sistem ortam değişkeni olarak tanımlayın.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Proje kökündeki .env dosyasını yükle
load_dotenv(Path(__file__).parent.parent / ".env")


def _get_int_env(name: str, default: int) -> int:
    value = os.environ.get(name)
    if value is None or value == "":
        return default
    try:
        return int(value)
    except ValueError:
        import logging
        logging.getLogger(__name__).warning(
            f"{name} gecersiz: {value!r}. Varsayilan {default} kullaniliyor."
        )
        return default


def _get_float_env(name: str, default: float) -> float:
    value = os.environ.get(name)
    if value is None or value == "":
        return default
    try:
        return float(value)
    except ValueError:
        import logging
        logging.getLogger(__name__).warning(
            f"{name} gecersiz: {value!r}. Varsayilan {default} kullaniliyor."
        )
        return default


def _get_str_env(name: str, default: str) -> str:
    value = os.environ.get(name)
    if value is None or value == "":
        return default
    return value


def _get_active_camera_ids() -> set[int] | None:
    raw = os.environ.get("ACTIVE_CAMERA_IDS", "").strip()
    if not raw:
        return None

    ids: set[int] = set()
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        try:
            ids.add(int(item))
        except ValueError:
            import logging
            logging.getLogger(__name__).warning(
                f"ACTIVE_CAMERA_IDS icindeki deger gecersiz: {item!r}"
            )
    return ids or None

def _get_camera_url(cam_id: int, fallback_ip: str) -> str:
    """Kamera URL'sini env'den oku. Yoksa uyar ve fallback kullan."""
    env_key = f"CAMERA_{cam_id}_URL"
    url = os.environ.get(env_key)
    if url:
        return url
    # .env dosyası yoksa geliştirici ortamı için varsayılan
    import logging
    logging.getLogger(__name__).warning(
        f"{env_key} env değişkeni tanımlı değil. "
        f"Lütfen .env dosyasına ekleyin."
    )
    return f"rtsp://admin:password@{fallback_ip}:554/Streaming/Channels/101"


# === KAMERA AYARLARI ===
_all_cameras = [
    {
        "id": 1,
        "url": _get_camera_url(1, "192.168.1.64"),
        "name": "Giriş Kapısı",
        "resolution": (1920, 1080),
    },
    {
        "id": 2,
        "url": _get_camera_url(2, "192.168.1.65"),
        "name": "Otopark-A",
        "resolution": (1920, 1080),
    },
    {
        "id": 3,
        "url": _get_camera_url(3, "192.168.1.66"),
        "name": "Otopark-B",
        "resolution": (1920, 1080),
    },
]

_active_camera_ids = _get_active_camera_ids()
CAMERAS = [
    cam for cam in _all_cameras
    if _active_camera_ids is None or cam["id"] in _active_camera_ids
]

# === RTSP AYARLARI — HİKVİSİON İÇİN OPTİMAL ===
RTSP_TRANSPORT = "tcp"          # UDP yerine TCP — paket kaybı olmaz
RTSP_BUFFER_SIZE = "1024000"    # 1MB buffer
RTSP_MAX_DELAY = "0"            # Sıfır gecikme
RTSP_FFLAGS = "nobuffer"        # FFmpeg buffer kapalı
RTSP_FLAGS = "low_delay"        # Düşük gecikme modu
RECONNECT_DELAY_SEC = 5         # İlk bağlantı koptuğunda bekleme süresi (sn)
RECONNECT_MAX_TRIES = 20        # Maksimum yeniden deneme (sonra dur, logla)
RECONNECT_BACKOFF_MAX = 60      # Exponential backoff üst sınırı (sn)

# === INFERENCE AYARLARI ===
MODEL_PATH = os.environ.get("MODEL_PATH", "models/yolov8s_1280.engine")  # TensorRT FP16
BATCH_SIZE = _get_int_env("BATCH_SIZE", 1)                          # Aktif pipeline: kamera basi inference
IMGSZ = _get_int_env("IMGSZ", 1280)
DETECTION_CONF = 0.50
NMS_IOU = 0.45
VEHICLE_CLASSES = [2, 5, 7]            # car, bus, truck
GENERIC_VEHICLE_LABEL = "vehicle"
ZONE_ROI_PADDING = _get_int_env("ZONE_ROI_PADDING", 160)

# === OCR AYARLARI ===
OCR_EVERY_N_FRAMES = 5         # Her 5 frame'de bir OCR
OCR_CONF_THRESHOLD = 0.45      # Altında reddet
OCR_MAX_QUEUE = 50
OCR_HISTORY_SIZE = _get_int_env("OCR_HISTORY_SIZE", 8)
OCR_MIN_STABLE_VOTES = _get_int_env("OCR_MIN_STABLE_VOTES", 2)
OCR_STICKY_CONFIDENCE = _get_float_env("OCR_STICKY_CONFIDENCE", 0.82)
OCR_REPLACE_MARGIN = _get_float_env("OCR_REPLACE_MARGIN", 0.05)
OCR_MIN_PLATE_WIDTH = _get_int_env("OCR_MIN_PLATE_WIDTH", 64)
OCR_MIN_PLATE_HEIGHT = _get_int_env("OCR_MIN_PLATE_HEIGHT", 18)
OCR_MIN_PLATE_AREA = _get_int_env("OCR_MIN_PLATE_AREA", 1400)

# === ALARM AYARLARI ===
VIOLATION_MIN_DURATION_SEC = 300   # 5 dakika bölgede kalırsa alarm
ALARM_COOLDOWN_SEC = 600           # Aynı araç için 10 dk bekleme (5dk ihlal + buffer)
REQUIRE_PLATE_FOR_ALARM = False    # Plakasız da alarm üret

# === PATHS ===
BASE_DIR = Path(__file__).parent
MODELS_DIR = BASE_DIR / "models"
DATA_DIR = BASE_DIR / "data"
SCREENSHOTS_DIR = DATA_DIR / "screenshots"
DB_PATH = DATA_DIR / "alarms.db"
ZONES_PATH = DATA_DIR / "zones.json"
TRACKER_CONFIG_PATH = BASE_DIR / "configs" / "bytetrack_vehicle.yaml"

# === SERVER ===
HOST = "0.0.0.0"
PORT = 8000
WS_FRAME_QUALITY = _get_int_env("WS_FRAME_QUALITY", 80)   # JPEG quality (0-100)
WS_FRAME_WIDTH = _get_int_env("WS_FRAME_WIDTH", 960)      # Stream çözünürlüğü (display için)
WS_FRAME_HEIGHT = _get_int_env("WS_FRAME_HEIGHT", 540)
VIDEO_STREAM_MODE = _get_str_env("VIDEO_STREAM_MODE", "webrtc")
VIDEO_STREAM_FALLBACK_MODE = _get_str_env("VIDEO_STREAM_FALLBACK_MODE", "hls")
MEDIA_MTX_RTSP_BASE_URL = _get_str_env("MEDIA_MTX_RTSP_BASE_URL", "rtsp://127.0.0.1:8554")
MEDIA_MTX_HLS_BASE_URL = _get_str_env("MEDIA_MTX_HLS_BASE_URL", "http://127.0.0.1:8888")
MEDIA_MTX_WEBRTC_BASE_URL = _get_str_env("MEDIA_MTX_WEBRTC_BASE_URL", "http://127.0.0.1:8889")
MEDIA_MTX_PATH_PREFIX = _get_str_env("MEDIA_MTX_PATH_PREFIX", "cam")

# === GPU ===
GPU_DEVICE = 0
GPU_WARMUP_ITERATIONS = 10

# === REDIS ===
# Docker ortamında REDIS_URL=redis://redis:6379 env var'ından okunur.
# Yoksa localhost:6379 varsayılanı kullanılır.
_redis_url = os.environ.get("REDIS_URL", "")
if _redis_url:
    try:
        from urllib.parse import urlparse as _urlparse
        _parsed = _urlparse(_redis_url)
        REDIS_HOST = _parsed.hostname or "localhost"
        REDIS_PORT = int(_parsed.port or 6379)
    except Exception:
        REDIS_HOST = "localhost"
        REDIS_PORT = 6379
else:
    REDIS_HOST = "localhost"
    REDIS_PORT = 6379
REDIS_DB = 0
