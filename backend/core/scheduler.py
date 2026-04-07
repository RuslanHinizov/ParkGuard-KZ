"""
scheduler.py — Zamanlı Görevler (APScheduler)

Günlük görevler:
- 00:00 → AI otomatik rapor oluştur
- 01:00 → Anomali taraması çalıştır
"""

import logging
import sqlite3
import json
import uuid
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import DB_PATH

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def start_scheduler() -> None:
    """Zamanlayıcıyı başlat."""
    # Her gün 00:00'da AI rapor oluştur (UTC+5 Kazakistan)
    scheduler.add_job(
        daily_ai_report_job,
        "cron",
        hour=0,
        minute=0,
        id="daily_ai_report",
        replace_existing=True,
    )

    # Her gün 01:00'da anomali taraması
    scheduler.add_job(
        daily_anomaly_scan_job,
        "cron",
        hour=1,
        minute=0,
        id="daily_anomaly_scan",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Scheduler baslatildi (daily report: 00:00, anomaly scan: 01:00)")


def stop_scheduler() -> None:
    """Zamanlayıcıyı durdur."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler durduruldu")


async def daily_ai_report_job() -> None:
    """Dünün verilerini AI ile analiz et ve rapor oluştur."""
    try:
        from core.ollama_service import generate_daily_report

        yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
        logger.info(f"AI gunluk rapor olusturuluyor: {yesterday}")

        report_text = await generate_daily_report(yesterday)

        if report_text:
            # Veritabanına kaydet
            _init_reports_table()
            report_id = str(uuid.uuid4())
            with sqlite3.connect(str(DB_PATH)) as conn:
                conn.execute(
                    "INSERT INTO reports VALUES (?,?,?,?,?,?,?,?)",
                    (
                        report_id,
                        f"AI Otchet: {yesterday}",
                        "daily_auto",
                        report_text,
                        None,
                        f"{yesterday}T00:00:00",
                        f"{yesterday}T23:59:59",
                        datetime.utcnow().isoformat(),
                    ),
                )
                conn.commit()
            logger.info(f"AI rapor kaydedildi: {report_id}")
        else:
            logger.warning("AI rapor olusturulamadi (bos yanit)")

    except Exception as e:
        logger.error(f"AI rapor gorevi hatasi: {e}")


async def daily_anomaly_scan_job() -> None:
    """Günlük anomali taraması çalıştır."""
    try:
        from core.anomaly_detector import anomaly_detector

        logger.info("Anomali taramasi baslatildi")
        anomalies = anomaly_detector.run_full_scan()
        logger.info(f"Anomali taramasi tamamlandi: {len(anomalies)} anomali")
    except Exception as e:
        logger.error(f"Anomali tarama gorevi hatasi: {e}")


def _init_reports_table():
    """Reports tablosunu oluştur (yoksa)."""
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
            conn.commit()
    except Exception:
        pass
