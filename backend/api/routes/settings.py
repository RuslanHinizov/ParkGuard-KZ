"""
settings.py — Sistem Ayarları API

GET  /api/settings                   → Tüm ayarları getir
PUT  /api/settings/camera/{id}       → Kamera ayarını güncelle
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from core.settings_manager import settings_mgr
from config import CAMERAS

router = APIRouter(tags=["settings"])


class CameraSettingsUpdate(BaseModel):
    violation_duration: int = Field(..., ge=30, le=3600,
                                    description="İhlal süresi (saniye, 30–3600)")


@router.get("/settings")
async def get_settings():
    """Tüm kamera ayarlarını getir."""
    return settings_mgr.get_all()


@router.put("/settings/camera/{camera_id}")
async def update_camera_settings(camera_id: int, body: CameraSettingsUpdate):
    """Kamera ihlal süresini güncelle."""
    valid_ids = {cam["id"] for cam in CAMERAS}
    if camera_id not in valid_ids:
        raise HTTPException(status_code=404, detail=f"Kamera {camera_id} bulunamadi")
    return settings_mgr.update_camera_settings(camera_id, body.violation_duration)
