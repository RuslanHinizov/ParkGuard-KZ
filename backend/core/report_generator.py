"""
report_generator.py — PDF Rapor Oluşturucu

fpdf2 ile profesyonel PDF rapor oluşturur.
Özel tarih/saat aralığı, kamera filtresi destekler.
"""

import io
import uuid
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from fpdf import FPDF

from config import DB_PATH, DATA_DIR

logger = logging.getLogger(__name__)

REPORTS_DIR = DATA_DIR / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


class KorgenPDF(FPDF):
    """Korgen Vision markalı PDF."""

    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 10, "KORGEN VISION", align="L")
        self.set_font("Helvetica", "", 8)
        self.cell(0, 10, self._header_subtitle, align="R", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(30, 80, 180)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Korgen Vision v1.0 | {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC", align="L")
        self.cell(0, 10, f"{self.page_no()}/{{nb}}", align="R")


def generate_pdf_report(
    date_from: str,
    date_to: str,
    camera_id: int | None = None,
) -> tuple[bytes, str]:
    """
    PDF rapor oluştur.

    Returns:
        (pdf_bytes, report_id)
    """
    report_id = str(uuid.uuid4())

    # Veritabanından veri çek
    data = _query_data(date_from, date_to, camera_id)

    pdf = KorgenPDF()
    pdf._header_subtitle = f"Период: {date_from[:10]} — {date_to[:10]}"
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # === Başlık ===
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(20, 60, 150)
    pdf.cell(0, 12, "Otchet o narusheniyah", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(80, 80, 80)
    period_text = f"Period: {date_from} - {date_to}"
    if camera_id:
        period_text += f" | Kamera: {camera_id}"
    pdf.cell(0, 6, period_text, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)

    # === Özet Tablo ===
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 8, "Svodka", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    summary = data["summary"]
    _draw_summary_table(pdf, summary)
    pdf.ln(8)

    # === Kamera bazlı ===
    if data["by_camera"]:
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Po kameram", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
        _draw_camera_table(pdf, data["by_camera"])
        pdf.ln(8)

    # === Saatlik dağılım ===
    if data["hourly"]:
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Pochasovoe raspredelenie", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
        _draw_hourly_chart(pdf, data["hourly"])
        pdf.ln(8)

    # === Top ihlalciler ===
    if data["top_plates"]:
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Top narushiteli", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
        _draw_top_plates(pdf, data["top_plates"])
        pdf.ln(8)

    # === Alarm listesi ===
    if data["alarms"]:
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, f"Spisok narushenij ({len(data['alarms'])})", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
        _draw_alarm_table(pdf, data["alarms"])

    # PDF'i byte olarak döndür
    pdf_bytes = pdf.output()

    # Dosyaya da kaydet
    try:
        file_path = REPORTS_DIR / f"report_{report_id[:8]}.pdf"
        file_path.write_bytes(pdf_bytes)

        # Veritabanına kaydet
        _save_report_record(report_id, date_from, date_to, camera_id, str(file_path))
    except Exception as e:
        logger.error(f"Rapor kaydedilemedi: {e}")

    return bytes(pdf_bytes), report_id


def _query_data(date_from: str, date_to: str, camera_id: int | None) -> dict:
    """Rapor verilerini SQLite'dan çek."""
    try:
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.row_factory = sqlite3.Row

            where = "created_at >= ? AND created_at <= ?"
            params: list = [date_from, date_to]

            if camera_id:
                where += " AND camera_id = ?"
                params.append(camera_id)

            # Özet
            total = conn.execute(
                f"SELECT COUNT(*) FROM alarms WHERE {where}", params
            ).fetchone()[0]
            active = conn.execute(
                f"SELECT COUNT(*) FROM alarms WHERE {where} AND status='active'", params
            ).fetchone()[0]
            resolved = conn.execute(
                f"SELECT COUNT(*) FROM alarms WHERE {where} AND status='resolved'", params
            ).fetchone()[0]

            # Kamera bazlı
            cam_rows = conn.execute(
                f"SELECT camera_id, COUNT(*) as cnt FROM alarms WHERE {where} GROUP BY camera_id",
                params,
            ).fetchall()
            by_camera = [{"camera_id": r["camera_id"], "count": r["cnt"]} for r in cam_rows]

            # Saatlik dağılım
            hourly_rows = conn.execute(
                f"""SELECT CAST(strftime('%H', created_at) AS INTEGER) as hour, COUNT(*) as cnt
                    FROM alarms WHERE {where} GROUP BY hour""",
                params,
            ).fetchall()
            hourly_map = {r["hour"]: r["cnt"] for r in hourly_rows}
            hourly = [{"hour": h, "count": hourly_map.get(h, 0)} for h in range(24)]

            # Top plakalar
            top_rows = conn.execute(
                f"""SELECT plate, COUNT(*) as cnt FROM alarms
                    WHERE {where} AND plate IS NOT NULL
                    GROUP BY plate ORDER BY cnt DESC LIMIT 10""",
                params,
            ).fetchall()
            top_plates = [{"plate": r["plate"], "count": r["cnt"]} for r in top_rows]

            # Alarm listesi (max 200)
            alarm_rows = conn.execute(
                f"""SELECT plate, camera_id, zone_name, duration_sec, status,
                           strftime('%Y-%m-%d %H:%M', created_at) as time
                    FROM alarms WHERE {where}
                    ORDER BY created_at DESC LIMIT 200""",
                params,
            ).fetchall()
            alarms = [dict(r) for r in alarm_rows]

            return {
                "summary": {"total": total, "active": active, "resolved": resolved},
                "by_camera": by_camera,
                "hourly": hourly,
                "top_plates": top_plates,
                "alarms": alarms,
            }
    except Exception as e:
        logger.error(f"Rapor veri sorgusu hatasi: {e}")
        return {
            "summary": {"total": 0, "active": 0, "resolved": 0},
            "by_camera": [],
            "hourly": [],
            "top_plates": [],
            "alarms": [],
        }


def _draw_summary_table(pdf: FPDF, summary: dict):
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(30, 80, 180)
    pdf.set_text_color(255, 255, 255)
    for header in ["Vsego", "Aktivnye", "Zakrytye"]:
        pdf.cell(60, 7, header, border=1, fill=True, align="C")
    pdf.ln()

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(0, 0, 0)
    for val in [summary["total"], summary["active"], summary["resolved"]]:
        pdf.cell(60, 7, str(val), border=1, align="C")
    pdf.ln()


def _draw_camera_table(pdf: FPDF, by_camera: list):
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(30, 80, 180)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(90, 7, "Kamera", border=1, fill=True, align="C")
    pdf.cell(90, 7, "Narushenij", border=1, fill=True, align="C")
    pdf.ln()

    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(0, 0, 0)
    for cam in by_camera:
        pdf.cell(90, 7, f"Kamera {cam['camera_id']}", border=1, align="C")
        pdf.cell(90, 7, str(cam["count"]), border=1, align="C")
        pdf.ln()


def _draw_hourly_chart(pdf: FPDF, hourly: list):
    """Basit ASCII bar chart benzeri çizim."""
    max_count = max((h["count"] for h in hourly), default=1) or 1
    chart_width = 160
    bar_height = 5

    pdf.set_font("Helvetica", "", 7)
    for h in hourly:
        if h["count"] == 0:
            continue
        bar_w = max(2, (h["count"] / max_count) * chart_width)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(15, bar_height, f"{h['hour']:02d}:00", align="R")
        pdf.set_fill_color(30, 100, 220)
        pdf.cell(bar_w, bar_height, "", fill=True)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(20, bar_height, f" {h['count']}")
        pdf.ln()


def _draw_top_plates(pdf: FPDF, plates: list):
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(30, 80, 180)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(10, 7, "#", border=1, fill=True, align="C")
    pdf.cell(90, 7, "Nomer", border=1, fill=True, align="C")
    pdf.cell(80, 7, "Narushenij", border=1, fill=True, align="C")
    pdf.ln()

    pdf.set_font("Courier", "", 9)
    pdf.set_text_color(0, 0, 0)
    for i, p in enumerate(plates, 1):
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(10, 7, str(i), border=1, align="C")
        pdf.set_font("Courier", "B", 10)
        pdf.cell(90, 7, p["plate"] or "-", border=1, align="C")
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(80, 7, str(p["count"]), border=1, align="C")
        pdf.ln()


def _draw_alarm_table(pdf: FPDF, alarms: list):
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(30, 80, 180)
    pdf.set_text_color(255, 255, 255)
    cols = [("Vremya", 35), ("Nomer", 35), ("Kamera", 20), ("Zona", 40), ("Dlitelnost", 25), ("Status", 25)]
    for name, w in cols:
        pdf.cell(w, 6, name, border=1, fill=True, align="C")
    pdf.ln()

    pdf.set_font("Helvetica", "", 7)
    pdf.set_text_color(0, 0, 0)
    for alarm in alarms:
        if pdf.get_y() > 270:
            pdf.add_page()
        pdf.cell(35, 5, alarm.get("time", ""), border=1, align="C")
        pdf.set_font("Courier", "", 7)
        pdf.cell(35, 5, alarm.get("plate") or "-", border=1, align="C")
        pdf.set_font("Helvetica", "", 7)
        pdf.cell(20, 5, str(alarm.get("camera_id", "")), border=1, align="C")
        pdf.cell(40, 5, (alarm.get("zone_name") or "")[:20], border=1, align="C")
        duration = alarm.get("duration_sec", 0)
        pdf.cell(25, 5, f"{duration // 60}m {duration % 60}s", border=1, align="C")
        pdf.cell(25, 5, alarm.get("status", ""), border=1, align="C")
        pdf.ln()


def _save_report_record(report_id: str, date_from: str, date_to: str, camera_id: int | None, file_path: str):
    """Rapor kaydını DB'ye ekle."""
    try:
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS reports (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    report_type TEXT,
                    content TEXT,
                    file_path TEXT,
                    date_from TEXT,
                    date_to TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            cam_text = f" (Kamera {camera_id})" if camera_id else ""
            title = f"Otchet {date_from[:10]} — {date_to[:10]}{cam_text}"
            conn.execute(
                "INSERT INTO reports VALUES (?,?,?,?,?,?,?,?)",
                (report_id, title, "custom", None, file_path, date_from, date_to,
                 datetime.utcnow().isoformat()),
            )
            conn.commit()
    except Exception as e:
        logger.error(f"Rapor kaydi hatasi: {e}")


def get_saved_reports() -> list[dict]:
    """Kayıtlı raporlar listesi."""
    try:
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT id, title, report_type, date_from, date_to, created_at FROM reports ORDER BY created_at DESC LIMIT 50"
            ).fetchall()
            return [dict(r) for r in rows]
    except Exception:
        return []


def get_report_file(report_id: str) -> Path | None:
    """Rapor dosya yolunu döndür."""
    try:
        with sqlite3.connect(str(DB_PATH)) as conn:
            row = conn.execute(
                "SELECT file_path FROM reports WHERE id = ?", (report_id,)
            ).fetchone()
            if row and row[0]:
                p = Path(row[0])
                return p if p.exists() else None
    except Exception:
        return None
