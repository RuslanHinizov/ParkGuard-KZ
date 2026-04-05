"""
tracker.py — Araç Takip Modülü (ByteTrack)

AMAÇ: Her kamera için ayrı ByteTrack tracker.
      Araçlara benzersiz track_id ata.
      Ultralytics built-in tracker kullanılır.

ByteTrack neden:
  - SORT'tan daha iyi: düşük confidence tespitleri de kullanır
  - Occlusion (araç arkasına geçme) durumunda ID kaybetmez
  - Ultralytics ile entegre — ek bağımlılık yok
"""

import logging
import numpy as np
from ultralytics import YOLO
from config import MODELS_DIR, DETECTION_CONF, NMS_IOU, VEHICLE_CLASSES, IMGSZ

logger = logging.getLogger(__name__)


class VehicleTracker:
    """Her kamera için ayrı tracker tutar."""

    def __init__(self):
        self.model: YOLO | None = None
        self._load_model()

    def _load_model(self) -> None:
        engine_path = MODELS_DIR / "yolov8n.engine"
        if engine_path.exists():
            self.model = YOLO(str(engine_path))
        else:
            pt_path = MODELS_DIR / "yolov8n.pt"
            self.model = YOLO(str(pt_path))
        logger.info("Tracker modeli yuklendi")

    def track(self, frames: dict) -> list[dict]:
        """
        Her kamera frame'i için track yap.

        Args:
            frames: {camera_id: {"frame": np.ndarray, ...}}

        Returns:
            list of detection dicts with track_id
        """
        if not frames:
            return []

        all_detections = []

        for cam_id, frame_data in frames.items():
            frame = frame_data["frame"]

            results = self.model.track(
                frame,
                persist=True,
                conf=DETECTION_CONF,
                iou=NMS_IOU,
                classes=VEHICLE_CLASSES,
                verbose=False,
                tracker="bytetrack.yaml",
            )

            if not results or not results[0].boxes:
                continue

            result = results[0]

            for box in result.boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                track_id = int(box.id[0]) if box.id is not None else None

                all_detections.append({
                    "camera_id": cam_id,
                    "bbox": [int(x1), int(y1), int(x2), int(y2)],
                    "confidence": float(box.conf[0]),
                    "class_id": int(box.cls[0]),
                    "class_name": result.names[int(box.cls[0])],
                    "track_id": track_id,
                    "timestamp": frame_data["timestamp"],
                    "frame": frame,
                })

        return all_detections
