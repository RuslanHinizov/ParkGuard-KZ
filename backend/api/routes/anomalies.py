"""
anomalies.py — Anomali Tespiti API

GET /api/anomalies — son anomaliler
GET /api/anomalies/count — görülmemiş sayı
PUT /api/anomalies/{id}/acknowledge — görüldü işaretle
POST /api/anomalies/scan — manuel tarama tetikle
"""
from fastapi import APIRouter, HTTPException
from core.anomaly_detector import anomaly_detector

router = APIRouter(tags=["anomalies"])

@router.get("/anomalies")
async def list_anomalies():
    return {"items": anomaly_detector.get_anomalies()}

@router.get("/anomalies/count")
async def unacknowledged_count():
    return {"count": anomaly_detector.get_unacknowledged_count()}

@router.put("/anomalies/{anomaly_id}/acknowledge")
async def acknowledge_anomaly(anomaly_id: str):
    if not anomaly_detector.acknowledge(anomaly_id):
        raise HTTPException(404, "Anomali bulunamadi")
    return {"success": True}

@router.post("/anomalies/scan")
async def manual_scan():
    anomalies = anomaly_detector.run_full_scan()
    return {"found": len(anomalies), "items": anomalies}
