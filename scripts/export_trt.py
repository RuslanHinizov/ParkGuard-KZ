"""
export_trt.py — YOLOv8s TensorRT FP16 Export

RTX 4060 Mobile için optimize edilmiş ayarlar:
  - FP16: 2x hız, ~%1 accuracy kaybı
  - batch=1: kamera basi inference ile uyumlu
  - imgsz=960: uzak arac ayrimi icin daha iyi
  - workspace=6: 6GB VRAM (8GB'ın 75%'i)
  - dynamic=False: sabit batch = daha hızlı kernel
"""

import sys
import os
from pathlib import Path

# Backend dizinini path'e ekle
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from ultralytics import YOLO

MODELS_DIR = backend_dir / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)


def main():
    pt_path = MODELS_DIR / "yolov8s.pt"

    # Model yoksa indir
    if not pt_path.exists():
        print("yolov8s.pt indiriliyor...")
        model = YOLO("yolov8s.pt")
        # İndirilen dosyayı models/ altına taşı
        downloaded = Path("yolov8s.pt")
        if downloaded.exists():
            downloaded.rename(pt_path)
    else:
        model = YOLO(str(pt_path))

    print("TensorRT FP16 export baslatiliyor...")
    print(f"  Model: {pt_path}")
    print(f"  Batch: 1")
    print(f"  ImgSz: 960")
    print(f"  FP16:  Evet")
    print(f"  VRAM:  6GB workspace")
    print()

    model.export(
        format="engine",
        device=0,
        half=True,
        batch=1,
        imgsz=960,
        workspace=6,
        simplify=True,
        dynamic=False,
    )

    engine_path = MODELS_DIR / "yolov8s.engine"
    if engine_path.exists():
        size_mb = engine_path.stat().st_size / (1024 * 1024)
        print(f"\nExport basarili!")
        print(f"  Engine: {engine_path}")
        print(f"  Boyut:  {size_mb:.1f} MB")
    else:
        print("\nUYARI: Engine dosyasi bulunamadi!")
        print("TensorRT kurulu oldugundan emin olun.")


if __name__ == "__main__":
    main()
