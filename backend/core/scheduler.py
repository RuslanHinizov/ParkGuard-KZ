"""
scheduler.py — Zamanlı Görevler (APScheduler)

Günlük görevler:
- 01:00 → Anomali taraması çalıştır
"""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def start_scheduler() -> None:
    """Zamanlayıcıyı başlat."""
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
    logger.info("Scheduler baslatildi (anomaly scan: 01:00)")


def stop_scheduler() -> None:
    """Zamanlayıcıyı durdur."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler durduruldu")


async def daily_anomaly_scan_job() -> None:
    """Günlük anomali taraması çalıştır."""
    try:
        from core.anomaly_detector import anomaly_detector

        logger.info("Anomali taramasi baslatildi")
        anomalies = anomaly_detector.run_full_scan()
        logger.info(f"Anomali taramasi tamamlandi: {len(anomalies)} anomali")
    except Exception as e:
        logger.error(f"Anomali tarama gorevi hatasi: {e}")
