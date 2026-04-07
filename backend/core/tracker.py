"""
tracker.py - Arac Takip Modulu (ByteTrack)

AMAC: Her kamera icin ayri ByteTrack tracker.
      Araclara benzersiz track_id ata.
      Ultralytics built-in tracker kullanilir.

ByteTrack neden:
  - SORT'tan daha iyi: dusuk confidence tespitleri de kullanir
  - Occlusion durumunda ID kaybetmez
  - Ultralytics ile entegre
"""

import logging
import numpy as np
from ultralytics import YOLO
from config import MODEL_PATH, MODELS_DIR, DETECTION_CONF, NMS_IOU, VEHICLE_CLASSES, IMGSZ

logger = logging.getLogger(__name__)


class VehicleTracker:
    """Her kamera icin ayri tracker tutar."""

    def __init__(self):
        self.model_path: str | None = None
        self.models: dict[int, YOLO] = {}
        self._load_model()

    def _load_model(self) -> None:
        engine_path = (MODELS_DIR.parent / MODEL_PATH).resolve()
        if engine_path.exists():
            self.model_path = str(engine_path)
        else:
            self.model_path = str(engine_path.with_suffix(".pt"))
        logger.info("Tracker modeli yuklendi")

    def _get_model(self, camera_id: int) -> YOLO:
        model = self.models.get(camera_id)
        if model is None:
            model = YOLO(self.model_path, task="detect")
            self.models[camera_id] = model
            logger.info(f"Kamera {camera_id} icin ayri tracker olusturuldu")
        return model

    def track(self, frames: dict) -> list[dict]:
        """
        Her kamera frame'i icin track yap.

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
            model = self._get_model(cam_id)

            results = model.track(
                frame,
                persist=True,
                conf=DETECTION_CONF,
                iou=NMS_IOU,
                classes=VEHICLE_CLASSES,
                imgsz=IMGSZ,
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
