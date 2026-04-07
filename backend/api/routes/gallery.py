"""
gallery.py — Ekran Görüntüsü Galeri API

GET /api/gallery — screenshot listesi (filtreli, sayfalı)
"""
import sqlite3
from fastapi import APIRouter, Query
from config import DB_PATH

router = APIRouter(tags=["gallery"])

@router.get("/gallery")
async def gallery(
    camera_id: int | None = Query(None),
    date: str | None = Query(None, description="YYYY-MM-DD"),
    plate: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    try:
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.row_factory = sqlite3.Row
            where_parts = ["screenshot IS NOT NULL"]
            params = []

            if camera_id is not None:
                where_parts.append("camera_id = ?")
                params.append(camera_id)
            if date:
                where_parts.append("date(created_at) = ?")
                params.append(date)
            if plate:
                where_parts.append("plate LIKE ?")
                params.append(f"%{plate.upper()}%")

            where = " AND ".join(where_parts)

            # Toplam sayı
            total = conn.execute(
                f"SELECT COUNT(*) FROM alarms WHERE {where}", params
            ).fetchone()[0]

            # Sayfalı sonuçlar
            rows = conn.execute(
                f"""SELECT id, plate, plate_conf, camera_id, zone_name, duration_sec,
                           status, screenshot, created_at
                    FROM alarms WHERE {where}
                    ORDER BY created_at DESC LIMIT ? OFFSET ?""",
                params + [limit, offset]
            ).fetchall()

            return {
                "items": [dict(r) for r in rows],
                "total": total,
            }
    except Exception as e:
        return {"items": [], "total": 0, "error": str(e)}
