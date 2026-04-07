"""
reports.py — PDF Rapor API

POST /api/reports/generate — PDF oluştur
GET /api/reports — kayıtlı raporlar
GET /api/reports/{id}/download — PDF indir
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel
from core.report_generator import generate_pdf_report, get_saved_reports, get_report_file

router = APIRouter(tags=["reports"])

class ReportRequest(BaseModel):
    date_from: str
    date_to: str
    camera_id: int | None = None

@router.post("/reports/generate")
async def create_report(req: ReportRequest):
    pdf_bytes, report_id = generate_pdf_report(req.date_from, req.date_to, req.camera_id)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="korgen_report_{report_id[:8]}.pdf"'}
    )

@router.get("/reports")
async def list_reports():
    return {"items": get_saved_reports()}

@router.get("/reports/{report_id}/download")
async def download_report(report_id: str):
    path = get_report_file(report_id)
    if not path:
        raise HTTPException(404, "Rapor dosyasi bulunamadi")
    from fastapi.responses import FileResponse
    return FileResponse(str(path), media_type="application/pdf", filename=f"korgen_report_{report_id[:8]}.pdf")
