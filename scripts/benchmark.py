"""
benchmark.py — Performans Benchmark

GPU inference hızını ölçer:
  - Tek frame inference süresi
  - Batch=3 inference süresi
  - FPS hesaplama
  - GPU bellek kullanımı
  - OCR hız testi
"""

import sys
import time
import numpy as np
from pathlib import Path

# Backend dizinini path'e ekle
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))


def benchmark_yolo():
    """YOLOv8s inference hız testi."""
    import torch
    from ultralytics import YOLO
    from config import MODELS_DIR, BATCH_SIZE, IMGSZ

    print("\n--- YOLOv8s Inference Benchmark ---")

    engine_path = MODELS_DIR / "yolov8s.engine"
    pt_path = MODELS_DIR / "yolov8s.pt"

    if engine_path.exists():
        model = YOLO(str(engine_path))
        print(f"  Model: TensorRT FP16")
    elif pt_path.exists():
        model = YOLO(str(pt_path))
        print(f"  Model: PyTorch FP32 (yavaş)")
    else:
        print("  HATA: Model bulunamadi!")
        return

    # Warmup
    dummy = [np.zeros((IMGSZ, IMGSZ, 3), dtype=np.uint8)] * BATCH_SIZE
    for _ in range(10):
        model(dummy, verbose=False)
    torch.cuda.synchronize()

    # Tek frame testi
    single_frame = [np.random.randint(0, 255, (IMGSZ, IMGSZ, 3), dtype=np.uint8)]
    times_single = []
    for _ in range(100):
        start = time.perf_counter()
        model(single_frame, verbose=False)
        torch.cuda.synchronize()
        times_single.append((time.perf_counter() - start) * 1000)

    avg_single = sum(times_single) / len(times_single)
    print(f"  Tek frame:  {avg_single:.2f} ms ({1000/avg_single:.0f} FPS)")

    # Batch=3 testi
    batch_frames = [
        np.random.randint(0, 255, (IMGSZ, IMGSZ, 3), dtype=np.uint8)
        for _ in range(BATCH_SIZE)
    ]
    times_batch = []
    for _ in range(100):
        start = time.perf_counter()
        model(batch_frames, verbose=False)
        torch.cuda.synchronize()
        times_batch.append((time.perf_counter() - start) * 1000)

    avg_batch = sum(times_batch) / len(times_batch)
    per_frame = avg_batch / BATCH_SIZE
    print(f"  Batch={BATCH_SIZE}:     {avg_batch:.2f} ms (frame basi {per_frame:.2f} ms)")
    print(f"  Toplam FPS: {1000/avg_batch * BATCH_SIZE:.0f} (3 kamera)")

    # GPU bellek
    if torch.cuda.is_available():
        allocated = torch.cuda.memory_allocated(0) / (1024**3)
        reserved = torch.cuda.memory_reserved(0) / (1024**3)
        total = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        print(f"\n  GPU: {torch.cuda.get_device_name(0)}")
        print(f"  VRAM Kullanim: {allocated:.2f} GB / {total:.1f} GB")
        print(f"  VRAM Reserved: {reserved:.2f} GB")
        print(f"  Bos VRAM: {total - reserved:.2f} GB")


def benchmark_ocr():
    """PaddleOCR hız testi."""
    print("\n--- PaddleOCR Benchmark ---")

    try:
        from paddleocr import PaddleOCR

        ocr = PaddleOCR(use_angle_cls=True, lang="ru", use_gpu=True, show_log=False)

        # Sahte plaka görseli
        test_img = np.random.randint(100, 200, (64, 200, 3), dtype=np.uint8)

        # Warmup
        for _ in range(5):
            ocr.ocr(test_img, cls=True)

        # Benchmark
        times = []
        for _ in range(50):
            start = time.perf_counter()
            ocr.ocr(test_img, cls=True)
            times.append((time.perf_counter() - start) * 1000)

        avg = sum(times) / len(times)
        print(f"  OCR suresi: {avg:.2f} ms/islem")
        print(f"  OCR FPS:    {1000/avg:.0f}")

    except ImportError:
        print("  PaddleOCR yuklu degil, atlanıyor.")


def main():
    print("=" * 50)
    print("  ParkGuard KZ — Performans Benchmark")
    print("=" * 50)

    try:
        import torch
        if torch.cuda.is_available():
            print(f"\n  GPU: {torch.cuda.get_device_name(0)}")
            print(f"  CUDA: {torch.version.cuda}")
            print(f"  PyTorch: {torch.__version__}")
        else:
            print("\n  UYARI: CUDA kulanilamıyor!")
    except ImportError:
        print("\n  HATA: PyTorch yuklu degil!")
        return

    benchmark_yolo()
    benchmark_ocr()

    print("\n" + "=" * 50)
    print("  Benchmark tamamlandi")
    print("=" * 50)


if __name__ == "__main__":
    main()
