"""
stats.py - Sistem API Endpoints

GET /api/system/fps      -> Anlik FPS
GET /api/system/health   -> GPU, CPU, RAM durumu
GET /api/system/snapshot/{camera_id} -> Son frame
"""

import cv2
import logging
import psutil
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from core.system_metrics import get_gpu_metrics

logger = logging.getLogger(__name__)

router = APIRouter(tags=["stats"])


def _get_managers():
    from main import alarm_mgr, camera_mgr

    return alarm_mgr, camera_mgr


@router.get("/system/fps")
async def system_fps():
    _, camera_mgr = _get_managers()
    return camera_mgr.get_fps_all()


@router.get("/system/health")
async def system_health():
    health = {
        "cpu_percent": psutil.cpu_percent(),
        "ram_used_gb": round(psutil.virtual_memory().used / (1024**3), 1),
        "ram_total_gb": round(psutil.virtual_memory().total / (1024**3), 1),
        "ram_percent": psutil.virtual_memory().percent,
    }

    gpu_metrics = get_gpu_metrics()
    health["gpu_name"] = gpu_metrics["gpu_name"]
    health["gpu_percent"] = gpu_metrics["gpu_util_percent"]
    health["gpu_memory_percent"] = gpu_metrics["gpu_memory_util_percent"]
    health["vram_used_gb"] = gpu_metrics["vram_used_gb"]
    health["vram_total_gb"] = gpu_metrics["vram_total_gb"]
    health["gpu_available"] = gpu_metrics["gpu_available"]

    _, camera_mgr = _get_managers()
    health["cameras"] = camera_mgr.get_status_all()

    return health


@router.get("/system/snapshot/{camera_id}")
async def camera_snapshot(camera_id: int):
    _, camera_mgr = _get_managers()

    frame = camera_mgr.get_frame(camera_id)
    if frame is None:
        raise HTTPException(status_code=404, detail="Kamera frame alinamadi")

    _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 90])

    return Response(
        content=buffer.tobytes(),
        media_type="image/jpeg",
    )
