"""
plates.py — Plaka Geçmişi API

GET /api/plates/{plate}/history — plakanın tüm ihlalleri
GET /api/plates/top — en çok ihlal yapan plakalar
"""
import sqlite3
from fastapi import APIRouter, Query
from config import DB_PATH

router = APIRouter(tags=["plates"])

@router.get("/plates/top")
async def top_plates(limit: int = Query(10, ge=1, le=50)):
    try:
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """SELECT plate, COUNT(*) as total_violations,
                          COUNT(DISTINCT camera_id) as cameras,
                          COUNT(DISTINCT date(created_at)) as days,
                          MIN(created_at) as first_seen,
                          MAX(created_at) as last_seen
                   FROM alarms WHERE plate IS NOT NULL
                   GROUP BY plate ORDER BY total_violations DESC LIMIT ?""",
                (limit,)
            ).fetchall()
            return {"plates": [dict(r) for r in rows]}
    except Exception as e:
        return {"plates": [], "error": str(e)}

@router.get("/plates/{plate}/history")
async def plate_history(plate: str, limit: int = Query(100, ge=1, le=500)):
    plate_upper = plate.upper().strip()
    try:
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.row_factory = sqlite3.Row

            # İstatistikler
            stats_row = conn.execute(
                """SELECT COUNT(*) as total,
                          COUNT(DISTINCT camera_id) as cameras,
                          COUNT(DISTINCT date(created_at)) as days,
                          AVG(duration_sec) as avg_duration,
                          MIN(created_at) as first_seen,
                          MAX(created_at) as last_seen
                   FROM alarms WHERE plate LIKE ?""",
                (f"%{plate_upper}%",)
            ).fetchone()
            stats = dict(stats_row) if stats_row else {}

            # Kamera bazlı dağılım
            cam_rows = conn.execute(
                """SELECT camera_id, COUNT(*) as count
                   FROM alarms WHERE plate LIKE ?
                   GROUP BY camera_id ORDER BY count DESC""",
                (f"%{plate_upper}%",)
            ).fetchall()

            # Alarm listesi
            alarm_rows = conn.execute(
                """SELECT id, camera_id, zone_name, duration_sec, status, screenshot, created_at, resolved_at
                   FROM alarms WHERE plate LIKE ?
                   ORDER BY created_at DESC LIMIT ?""",
                (f"%{plate_upper}%", limit)
            ).fetchall()

            return {
                "plate": plate_upper,
                "stats": stats,
                "by_camera": [dict(r) for r in cam_rows],
                "alarms": [dict(r) for r in alarm_rows],
            }
    except Exception as e:
        return {"plate": plate_upper, "stats": {}, "by_camera": [], "alarms": [], "error": str(e)}
