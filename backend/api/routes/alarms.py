"""
alarms.py — Alarm API Endpoints

GET  /api/alarms              → Listele (filtre: camera_id, status, plate, date)
GET  /api/alarms/{id}         → Detay
PUT  /api/alarms/{id}/resolve → Çözüldü işaretle
GET  /api/alarms/{id}/screenshot → Görsel
DELETE /api/alarms/{id}       → Sil
"""

import logging
from pathlib import Path
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import FileResponse
from config import DATA_DIR

logger = logging.getLogger(__name__)

router = APIRouter(tags=["alarms"])


def _get_alarm_manager():
    """Lazy import — circular import önleme."""
    from main import alarm_mgr
    return alarm_mgr


@router.get("/alarms")
async def list_alarms(
    camera_id: int | None = Query(None, description="Kamera filtre"),
    status: str | None = Query(None, description="active | resolved"),
    plate: str | None = Query(None, description="Plaka arama"),
    date_from: str | None = Query(None, description="Baslangic tarihi"),
    date_to: str | None = Query(None, description="Bitis tarihi"),
    limit: int = Query(50, ge=1, le=500, description="Sayfa boyutu"),
    offset: int = Query(0, ge=0, description="Sayfalama offset"),
):
    """Alarm listesi — filtreli, sayfalı."""
    alarm_mgr = _get_alarm_manager()
    alarms, total = alarm_mgr.get_alarms(
        camera_id=camera_id,
        status=status,
        plate=plate,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset,
    )
    return {"alarms": alarms, "total": total}


@router.get("/alarms/{alarm_id}")
async def get_alarm(alarm_id: str):
    """Tek alarm detayı."""
    alarm_mgr = _get_alarm_manager()
    alarm = alarm_mgr.get_alarm(alarm_id)
    if not alarm:
        raise HTTPException(status_code=404, detail="Alarm bulunamadi")
    return alarm


@router.put("/alarms/{alarm_id}/resolve")
async def resolve_alarm(alarm_id: str):
    """Alarmı çözüldü olarak işaretle."""
    alarm_mgr = _get_alarm_manager()
    alarm = alarm_mgr.resolve_alarm(alarm_id)
    if not alarm:
        raise HTTPException(status_code=404, detail="Alarm bulunamadi")
    return alarm


@router.get("/alarms/{alarm_id}/screenshot")
async def get_screenshot(alarm_id: str):
    """Alarm screenshot dosyasını döndür."""
    alarm_mgr = _get_alarm_manager()
    alarm = alarm_mgr.get_alarm(alarm_id)
    if not alarm:
        raise HTTPException(status_code=404, detail="Alarm bulunamadi")

    screenshot_path = Path(alarm["screenshot"])
    # Yeni kayıtlar göreceli path içerir — DATA_DIR ile tam path'e çevir
    # Eski kayıtlar mutlak path içerebilir — olduğu gibi kullan (geriye dönük uyum)
    if not screenshot_path.is_absolute():
        screenshot_path = DATA_DIR / screenshot_path
    if not screenshot_path.exists():
        raise HTTPException(status_code=404, detail="Screenshot bulunamadi")

    return FileResponse(
        path=str(screenshot_path),
        media_type="image/jpeg",
        filename=f"alarm_{alarm_id[:8]}.jpg",
    )


@router.get("/alarms/{alarm_id}/plate-screenshot")
async def get_plate_screenshot(alarm_id: str):
    """Alarm plaka crop dosyasını döndür."""
    alarm_mgr = _get_alarm_manager()
    alarm = alarm_mgr.get_alarm(alarm_id)
    if not alarm:
        raise HTTPException(status_code=404, detail="Alarm bulunamadi")

    plate_screenshot = alarm.get("plate_screenshot")
    if not plate_screenshot:
        raise HTTPException(status_code=404, detail="Plate screenshot bulunamadi")

    plate_screenshot_path = Path(plate_screenshot)
    if not plate_screenshot_path.is_absolute():
        plate_screenshot_path = DATA_DIR / plate_screenshot_path
    if not plate_screenshot_path.exists():
        raise HTTPException(status_code=404, detail="Plate screenshot bulunamadi")

    return FileResponse(
        path=str(plate_screenshot_path),
        media_type="image/jpeg",
        filename=f"alarm_{alarm_id[:8]}_plate.jpg",
    )


@router.delete("/alarms/{alarm_id}")
async def delete_alarm(alarm_id: str):
    """Alarm sil."""
    alarm_mgr = _get_alarm_manager()
    success = alarm_mgr.delete_alarm(alarm_id)
    if not success:
        raise HTTPException(status_code=404, detail="Alarm bulunamadi")
    return {"success": True}
