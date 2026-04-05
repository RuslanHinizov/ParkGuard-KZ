"""
zones.py — Bölge Yönetimi API Endpoints

GET    /api/zones                   → Tüm bölgeler
GET    /api/zones/camera/{cam_id}   → Kameraya göre
POST   /api/zones                   → Yeni bölge
PUT    /api/zones/{id}              → Güncelle
DELETE /api/zones/{id}              → Sil
"""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(tags=["zones"])


class ZoneCreate(BaseModel):
    camera_id: int
    name: str
    polygon: list[list[int]]
    color: str = "#FF0000"


class ZoneUpdate(BaseModel):
    name: str | None = None
    polygon: list[list[int]] | None = None
    color: str | None = None
    active: bool | None = None


def _get_zone_manager():
    from main import zone_mgr
    return zone_mgr


@router.get("/zones")
async def list_zones():
    """Tüm bölgeleri listele."""
    zone_mgr = _get_zone_manager()
    return zone_mgr.get_all_zones()


@router.get("/zones/camera/{camera_id}")
async def get_zones_by_camera(camera_id: int):
    """Kameraya ait bölgeleri listele."""
    zone_mgr = _get_zone_manager()
    return zone_mgr.get_zones_for_camera(camera_id)


def _validate_polygon(polygon: list[list[int]]) -> str | None:
    """
    Polygon geçerlilik kontrolü.
    Hata varsa hata mesajı döner, geçerliyse None.
    """
    if len(polygon) < 3:
        return "Polygon en az 3 nokta icermeli"

    seen = set()
    for point in polygon:
        if len(point) != 2:
            return "Her nokta [x, y] formatinda olmali"
        x, y = point
        if not (0 <= x <= 10000 and 0 <= y <= 10000):
            return f"Gecersiz koordinat: [{x}, {y}] — 0-10000 araliginda olmali"
        key = (x, y)
        if key in seen:
            return f"Tekrar eden nokta: [{x}, {y}]"
        seen.add(key)

    return None


@router.post("/zones")
async def create_zone(body: ZoneCreate):
    """Yeni yasak park bölgesi oluştur."""
    zone_mgr = _get_zone_manager()

    error = _validate_polygon(body.polygon)
    if error:
        raise HTTPException(status_code=400, detail=error)

    zone = zone_mgr.add_zone(
        camera_id=body.camera_id,
        name=body.name,
        polygon=body.polygon,
        color=body.color,
    )
    return zone


@router.put("/zones/{zone_id}")
async def update_zone(zone_id: str, body: ZoneUpdate):
    """Bölge güncelle."""
    zone_mgr = _get_zone_manager()
    updates = body.model_dump(exclude_none=True)

    if "polygon" in updates:
        error = _validate_polygon(updates["polygon"])
        if error:
            raise HTTPException(status_code=400, detail=error)

    zone = zone_mgr.update_zone(zone_id, updates)
    if not zone:
        raise HTTPException(status_code=404, detail="Bolge bulunamadi")
    return zone


@router.delete("/zones/{zone_id}")
async def delete_zone(zone_id: str):
    """Bölge sil."""
    zone_mgr = _get_zone_manager()
    success = zone_mgr.delete_zone(zone_id)
    if not success:
        raise HTTPException(status_code=404, detail="Bolge bulunamadi")
    return {"success": True}
