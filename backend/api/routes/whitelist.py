"""
whitelist.py — Beyaz Liste API

GET /api/whitelist — tüm liste
POST /api/whitelist — plaka ekle {plate, reason}
DELETE /api/whitelist/{plate} — plaka sil
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core.whitelist_manager import whitelist_mgr

router = APIRouter(tags=["whitelist"])

class WhitelistEntry(BaseModel):
    plate: str
    reason: str = ""

@router.get("/whitelist")
async def list_whitelist():
    return {"items": whitelist_mgr.get_all()}

@router.post("/whitelist")
async def add_to_whitelist(entry: WhitelistEntry):
    result = whitelist_mgr.add_plate(entry.plate, entry.reason)
    if not result:
        raise HTTPException(400, "Plaka eklenemedi (zaten mevcut?)")
    return result

@router.delete("/whitelist/{plate}")
async def remove_from_whitelist(plate: str):
    if not whitelist_mgr.remove_plate(plate):
        raise HTTPException(404, "Plaka bulunamadi")
    return {"success": True}
