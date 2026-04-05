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
CAMERAS = [
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
MODEL_PATH = "models/yolov8n.engine"    # TensorRT FP16
BATCH_SIZE = 3                          # 3 kamera aynı anda
IMGSZ = 640
DETECTION_CONF = 0.50
NMS_IOU = 0.45
VEHICLE_CLASSES = [2, 3, 5, 7]         # car, motorcycle, bus, truck

# === OCR AYARLARI ===
OCR_EVERY_N_FRAMES = 10        # Her 10 frame'de bir OCR
OCR_CONF_THRESHOLD = 0.70      # Altında reddet
OCR_MAX_QUEUE = 50

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

# === SERVER ===
HOST = "0.0.0.0"
PORT = 8000
WS_FRAME_QUALITY = 80    # JPEG quality (0-100)
WS_FRAME_WIDTH = 960     # Stream çözünürlüğü (display için)
WS_FRAME_HEIGHT = 540

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
