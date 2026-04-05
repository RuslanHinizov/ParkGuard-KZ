"""
stats.py — İstatistik ve Sistem API Endpoints

GET /api/stats/today     → Bugün özeti
GET /api/stats/hourly    → Saatlik breakdown
GET /api/stats/cameras   → Kamera bazlı
GET /api/system/fps      → Anlık FPS
GET /api/system/health   → GPU, CPU, RAM durumu
GET /api/system/snapshot/{camera_id} → Son frame (zone editor için)
"""

import cv2
import logging
import psutil
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import Response

logger = logging.getLogger(__name__)

router = APIRouter(tags=["stats"])


def _get_managers():
    from main import alarm_mgr, camera_mgr
    return alarm_mgr, camera_mgr


@router.get("/stats/today")
async def today_stats():
    """Bugünün alarm istatistikleri."""
    alarm_mgr, _ = _get_managers()
    return alarm_mgr.get_today_stats()


@router.get("/stats/hourly")
async def hourly_stats(date: str | None = Query(None, description="YYYY-MM-DD")):
    """Saatlik alarm dağılımı (24 kayıt)."""
    alarm_mgr, _ = _get_managers()
    return alarm_mgr.get_hourly_stats(date)


@router.get("/stats/cameras")
async def camera_stats():
    """Kamera bazlı alarm istatistikleri."""
    alarm_mgr, _ = _get_managers()
    return alarm_mgr.get_camera_stats()


@router.get("/system/fps")
async def system_fps():
    """Tüm kameraların anlık FPS değerleri."""
    _, camera_mgr = _get_managers()
    return camera_mgr.get_fps_all()


@router.get("/system/health")
async def system_health():
    """Sistem sağlık bilgileri: GPU, CPU, RAM."""

    health = {
        "cpu_percent": psutil.cpu_percent(),
        "ram_used_gb": round(psutil.virtual_memory().used / (1024**3), 1),
        "ram_total_gb": round(psutil.virtual_memory().total / (1024**3), 1),
        "ram_percent": psutil.virtual_memory().percent,
    }

    # GPU bilgisi (opsiyonel — nvidia-smi yoksa hata verme)
    try:
        import torch
        if torch.cuda.is_available():
            health["gpu_name"] = torch.cuda.get_device_name(0)
            health["vram_used_gb"] = round(torch.cuda.memory_allocated(0) / (1024**3), 2)
            health["vram_total_gb"] = round(torch.cuda.get_device_properties(0).total_memory / (1024**3), 1)
            health["gpu_available"] = True
        else:
            health["gpu_available"] = False
    except ImportError:
        health["gpu_available"] = False

    # Kamera durumları
    _, camera_mgr = _get_managers()
    health["cameras"] = camera_mgr.get_status_all()

    return health


@router.get("/system/snapshot/{camera_id}")
async def camera_snapshot(camera_id: int):
    """Kameradan son frame'i JPEG olarak döndür (zone editor için)."""
    _, camera_mgr = _get_managers()

    frame = camera_mgr.get_frame(camera_id)
    if frame is None:
        raise HTTPException(status_code=404, detail="Kamera frame alinamadi")

    _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 90])

    return Response(
        content=buffer.tobytes(),
        media_type="image/jpeg",
    )
