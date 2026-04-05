"""
detector.py — Araç Tespit Modülü

AMAÇ: YOLOv8n TensorRT FP16 ile batch=3 inference.
      3 kameranın frame'lerini aynı anda GPU'ya gönder.
      GPU warmup yap (ilk frame yavaş olmasın).

Neden batch=3:
  Sıralı: model(f1)→3ms + model(f2)→3ms + model(f3)→3ms = 9ms
  Batch:  model([f1,f2,f3]) → 4ms (GPU parallelism)
"""

import torch
import numpy as np
import logging
import time
from ultralytics import YOLO
from config import (
    MODELS_DIR, BATCH_SIZE, IMGSZ, DETECTION_CONF,
    NMS_IOU, VEHICLE_CLASSES, GPU_DEVICE, GPU_WARMUP_ITERATIONS,
)

logger = logging.getLogger(__name__)


class VehicleDetector:

    def __init__(self):
        self.model: YOLO | None = None
        self._load_model()
        self._warmup()

    def _load_model(self) -> None:
        """TensorRT engine yükle. Yoksa otomatik export et."""

        engine_path = MODELS_DIR / "yolov8n.engine"

        if not engine_path.exists():
            logger.info("TensorRT engine bulunamadi, export ediliyor...")
            self._export_engine()

        self.model = YOLO(str(engine_path))
        logger.info("YOLOv8n TensorRT yuklendi")

    def _export_engine(self) -> None:
        """YOLOv8n → TensorRT FP16 export."""

        pt_path = MODELS_DIR / "yolov8n.pt"
        if not pt_path.exists():
            logger.info("yolov8n.pt indiriliyor...")
            YOLO("yolov8n.pt")  # otomatik indirir

        model = YOLO(str(pt_path))
        model.export(
            format="engine",
            device=GPU_DEVICE,
            half=True,           # FP16: 2x hız, ~%1 accuracy kaybı
            batch=BATCH_SIZE,    # 3 kamera
            imgsz=IMGSZ,
            workspace=6,         # 6GB VRAM
            simplify=True,
            dynamic=False,       # Sabit batch = daha hızlı
        )
        logger.info("TensorRT export tamamlandi")

    def _warmup(self) -> None:
        """GPU warmup — ilk gerçek frame yavaş olmasın.

        CUDA lazy init + kernel compilation burada yapılır.
        Warmup sonrası ilk frame normal hızda işlenir.
        """

        logger.info("GPU warmup baslatildi...")
        dummy = [np.zeros((IMGSZ, IMGSZ, 3), dtype=np.uint8)] * BATCH_SIZE

        for i in range(GPU_WARMUP_ITERATIONS):
            self.model(dummy, verbose=False)

        torch.cuda.synchronize()
        logger.info(f"GPU warmup tamamlandi ({GPU_WARMUP_ITERATIONS} iterasyon)")

    def detect(self, frames: dict) -> list[dict]:
        """
        Batch inference — 3 kamera frame'i aynı anda.

        Args:
            frames: {camera_id: {"frame": np.ndarray, "timestamp": float, ...}}

        Returns:
            list of detection dicts with keys:
            camera_id, bbox, confidence, class_id, class_name, timestamp, frame
        """

        if not frames:
            return []

        cam_ids = list(frames.keys())
        batch = [frames[cid]["frame"] for cid in cam_ids]

        # Batch inference — 3 kamera aynı anda GPU'ya
        results = self.model(
            batch,
            conf=DETECTION_CONF,
            iou=NMS_IOU,
            classes=VEHICLE_CLASSES,
            verbose=False,
            stream=False,
        )

        detections = []

        for result, cam_id in zip(results, cam_ids):
            for box in result.boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                detections.append({
                    "camera_id": cam_id,
                    "bbox": [int(x1), int(y1), int(x2), int(y2)],
                    "confidence": float(box.conf[0]),
                    "class_id": int(box.cls[0]),
                    "class_name": result.names[int(box.cls[0])],
                    "timestamp": frames[cam_id]["timestamp"],
                    "frame": frames[cam_id]["frame"],
                })

        return detections
