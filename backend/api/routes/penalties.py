"""
penalties.py — Ceza Kuyruğu API

GET  /api/penalties              → Ceza listesi (filtreli, sayfalı)
GET  /api/penalties/stats        → Durum bazlı özet
POST /api/penalties/{id}/send    → Ceza gönder
POST /api/penalties/{id}/cancel  → Cezayı iptal et
POST /api/penalties/send-all     → Tüm bekleyenleri gönder
"""

import logging
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(tags=["penalties"])


def _mgr():
    from core.penalty_manager import penalty_mgr
    return penalty_mgr


# ─────────────────────────────────────────
#  LİSTELEME
# ─────────────────────────────────────────

@router.get("/penalties")
async def list_penalties(
    status: str | None = Query(None, description="pending | sent | cancelled"),
    plate:  str | None = Query(None, description="Plaka arama"),
    alarm_id: str | None = Query(None, description="Alarm ID"),
    limit:  int        = Query(50, ge=1, le=200),
    offset: int        = Query(0, ge=0),
):
    """Ceza listesi — filtreli, sayfalı."""
    penalties, total = _mgr().get_penalties(
        status=status, plate=plate, alarm_id=alarm_id, limit=limit, offset=offset
    )
    return {"penalties": penalties, "total": total}


@router.get("/penalties/stats")
async def penalty_stats():
    """Durum bazlı özet istatistik."""
    return _mgr().get_stats()


# ─────────────────────────────────────────
#  EYLEMLER
# ─────────────────────────────────────────

@router.post("/penalties/{penalty_id}/send")
async def send_penalty(penalty_id: str):
    """Tek ceza gönder."""
    result = _mgr().send_penalty(penalty_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result


class CancelBody(BaseModel):
    reason: str = ""


@router.post("/penalties/{penalty_id}/cancel")
async def cancel_penalty(penalty_id: str, body: CancelBody):
    """Bekleyen cezayı iptal et."""
    success = _mgr().cancel_penalty(penalty_id, body.reason)
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Ceza bulunamadı veya zaten gönderilmiş/iptal edilmiş",
        )
    return {"success": True}


@router.post("/penalties/send-all")
async def send_all_pending():
    """Tüm bekleyen cezaları toplu gönder."""
    sent = _mgr().send_all_pending()
    return {"sent": sent, "message": f"{sent} ceza başarıyla gönderildi"}
