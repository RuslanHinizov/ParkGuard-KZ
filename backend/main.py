"""
main.py — ParkGuard KZ Ana Pipeline

AMAÇ: Tüm modülleri birleştir. Ana inference döngüsünü çalıştır.
      FastAPI + WebSocket server'ı başlat.
      Process priority'yi yükselt (Windows).

Çalışma sırası:
  1. Kameraları başlat (her biri ayrı daemon thread)
  2. Inference loop (async task):
     Frame al → Detect → Track → Zone check → OCR → Alarm → WS broadcast
  3. FastAPI server (async HTTP + WebSocket)
"""

import os

# PaddleOCR baslangic yavasligi onleme
os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"

import sys
import asyncio
import logging
import psutil
import torch
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Backend modülünün kendi dizinini Python path'e ekle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.log_buffer import log_buffer
from core.camera_manager import CameraManager
from core.tracker import VehicleTracker
from core.zone_manager import ZoneManager
from core.plate_ocr import PlateOCR
from core.alarm_manager import AlarmManager
from api.routes import alarms, zones, stats, stream, settings
from api.websocket import ws_manager
from config import (
    HOST, PORT, OCR_EVERY_N_FRAMES, CAMERAS,
)

# Logging ayarı
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
# Bellek içi log tamponu (Log Viewer WebSocket için)
logging.getLogger().addHandler(log_buffer)
logger = logging.getLogger(__name__)

# === GLOBAL MODÜLLER ===
camera_mgr = CameraManager()
tracker: VehicleTracker | None = None
zone_mgr = ZoneManager()
plate_ocr: PlateOCR | None = None
alarm_mgr = AlarmManager()


def set_high_priority() -> None:
    """Windows'ta process önceliğini yükselt. Daha stabil FPS sağlar."""
    try:
        p = psutil.Process(os.getpid())
        p.nice(psutil.HIGH_PRIORITY_CLASS)
        logger.info("Process priority: HIGH")
    except Exception as e:
        logger.warning(f"Priority ayarlanamadi: {e}")


async def inference_loop() -> None:
    """
    Ana inference döngüsü:
    1. Tüm kameralardan frame al (FrameBuffer — hep güncel)
    2. Tracking (ByteTrack — araç ID ata)
    3. Zone check (Shapely polygon — ihlal mi?)
    4. OCR (her 10 frame'de bir — performans)
    5. Alarm check (300sn / kamera ayarı bölgede → alarm üret)
    6. WebSocket'e annotated frame gönder
    """

    global tracker, plate_ocr

    frame_counter = 0

    # GPU modüllerini başlat
    try:
        tracker = VehicleTracker()
        plate_ocr = PlateOCR()
    except Exception as e:
        logger.error(f"GPU modulleri baslatilirken hata: {e}")
        logger.info("GPU olmadan devam ediliyor (tespit devre disi)")
        return

    logger.info("Inference loop baslatildi")

    while True:
        try:
            frames = camera_mgr.get_frames()

            if not frames:
                await asyncio.sleep(0.01)
                continue

            # ByteTrack ile araç takibi (detect + track tek adımda)
            detections = tracker.track(frames)

            # Her detection için zone ve OCR kontrolü
            for det in detections:
                track_id = det.get("track_id")  # None = henüz ID atanmamış araç

                # Önce zone kontrolü — sadece ihlaldeki araçlara OCR uygula
                zone = zone_mgr.check_violation(det)
                det["in_violation"] = zone is not None
                det["zone"] = zone
                det["plate"] = None  # Default — aşağıda güncellenebilir

                # Track ID yoksa (ByteTrack henüz onaylamadı) alarm/OCR atla.
                # Görsel annotasyon yine de yapılır (broadcast_detections kullanır).
                if track_id is None:
                    continue

                # Araç zone dışına çıktıysa OCR önbelleğini temizle (bellek koruması)
                if zone is None and plate_ocr:
                    plate_ocr.clear_track(track_id)

                # OCR: sadece ihlaldeki araçlar için çalıştır
                # İhlalde değilse plaka bilmemize gerek yok → CPU tasarrufu
                plate = None
                if zone is not None and plate_ocr:
                    # Önce önbellekte var mı bak (her frame'de OCR çalıştırma)
                    cached = plate_ocr.get_cached(track_id)
                    if cached:
                        plate = cached
                    elif frame_counter % OCR_EVERY_N_FRAMES == 0:
                        plate = plate_ocr.read_plate(det["frame"], det["bbox"])
                        if plate:
                            plate_ocr.cache_result(track_id, plate)

                det["plate"] = plate["text"] if plate else (
                    plate_ocr.get_cached(track_id)["text"]
                    if plate_ocr and plate_ocr.get_cached(track_id) else None
                )

                # Alarm kontrolü
                alarm = alarm_mgr.update(track_id, det, zone, plate)
                if alarm:
                    await ws_manager.broadcast_alarm(alarm)

            # Zone bilgisini al (annotasyon için)
            all_zones = zone_mgr.get_all_zones()

            # WebSocket'e annotated frame gönder
            await ws_manager.broadcast_detections(frames, detections, all_zones)

            frame_counter += 1

            # CPU nefes alsın
            await asyncio.sleep(0.001)

        except torch.cuda.OutOfMemoryError:
            logger.error("GPU bellek doldu! Cache temizleniyor...")
            torch.cuda.empty_cache()
            await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Inference loop hatasi: {e}", exc_info=True)
            await asyncio.sleep(0.1)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Uygulama yaşam döngüsü — başlangıç ve kapanış."""

    # === BAŞLANGIÇ ===
    set_high_priority()

    # Kameraları başlat
    camera_mgr.start_all()

    # Inference döngüsünü arka planda çalıştır
    inference_task = asyncio.create_task(inference_loop())

    logger.info("=" * 50)
    logger.info("ParkGuard KZ baslatildi")
    logger.info(f"Kameralar: {len(CAMERAS)} adet")
    logger.info(f"API: http://{HOST}:{PORT}")
    logger.info(f"Dashboard: http://localhost:5173")
    logger.info("=" * 50)

    yield

    # === KAPANIŞ ===
    inference_task.cancel()
    camera_mgr.stop_all()
    logger.info("ParkGuard KZ durduruldu")


# === FASTAPI UYGULAMASI ===
app = FastAPI(
    title="ParkGuard KZ",
    description="Yaslis Park Tespit Sistemi API",
    version="2.0",
    lifespan=lifespan,
)

# CORS — sadece bilinen frontend origin'lerine izin ver
ALLOWED_ORIGINS = [
    "http://localhost:5173",   # Vite dev server
    "http://localhost:3000",   # alternatif dev port
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)

# API routes
app.include_router(alarms.router, prefix="/api")
app.include_router(zones.router, prefix="/api")
app.include_router(stats.router, prefix="/api")
app.include_router(settings.router, prefix="/api")
app.include_router(stream.router)


@app.get("/")
async def root():
    return {
        "name": "ParkGuard KZ",
        "version": "2.0",
        "status": "running",
        "cameras": len(CAMERAS),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        reload=False,
        log_level="info",
    )
