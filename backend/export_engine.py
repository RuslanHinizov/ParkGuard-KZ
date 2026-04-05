"""
export_engine.py — YOLOv8n TensorRT FP16 Engine Oluştur

Sadece BİR KERE çalıştırılır. Engine oluşturulunca bu script'e gerek kalmaz.
Engine oluşturma süresi: ~3-5 dakika (ilk seferinde uzun sürer, normaldir)

Çalıştırmak için:
  cd backend
  python export_engine.py
"""

import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent))


def main():
    try:
        import torch
        logger.info(f"PyTorch: {torch.__version__}")
        logger.info(f"CUDA mevcut: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            logger.info(f"GPU: {torch.cuda.get_device_name(0)}")
        else:
            logger.error("CUDA bulunamadi! GPU driver kurulu mu?")
            sys.exit(1)
    except ImportError:
        logger.error("PyTorch kurulu degil.")
        sys.exit(1)

    try:
        import tensorrt
        logger.info(f"TensorRT: {tensorrt.__version__}")
    except ImportError:
        logger.error("TensorRT kurulu degil. Once: pip install tensorrt")
        sys.exit(1)

    from ultralytics import YOLO

    models_dir = Path(__file__).parent / "models"
    pt_path = models_dir / "yolov8n.pt"
    engine_path = models_dir / "yolov8n.engine"

    if engine_path.exists():
        logger.info(f"Engine zaten mevcut: {engine_path}")
        logger.info("Yeniden olusturmak icin engine dosyasini sil ve tekrar calistir.")
        return

    if not pt_path.exists():
        logger.info("yolov8n.pt bulunamadi, indiriliyor...")
        YOLO("yolov8n.pt")

    logger.info("=" * 50)
    logger.info("TensorRT FP16 engine olusturuluyor...")
    logger.info("Bu islem 3-5 dakika surebilir, lutfen bekleyin.")
    logger.info("=" * 50)

    model = YOLO(str(pt_path))
    model.export(
        format="engine",
        device=0,
        half=True,       # FP16 — 2x hiz, minimal dogruluk kaybi
        batch=1,         # Tracker per-frame calisir
        imgsz=640,
        workspace=4,     # 4GB VRAM kullan (RTX 4060 icin ideal)
        simplify=True,
    )

    if engine_path.exists():
        logger.info("=" * 50)
        logger.info(f"Engine basariyla olusturuldu: {engine_path}")
        logger.info("Artik sistemi baslatabilirsiniz.")
        logger.info("=" * 50)
    else:
        logger.error("Engine olusturulamadi. Yukaridaki hatalara bakin.")


if __name__ == "__main__":
    main()
