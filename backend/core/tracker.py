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
from config import (
    MODEL_PATH,
    MODELS_DIR,
    DETECTION_CONF,
    NMS_IOU,
    VEHICLE_CLASSES,
    IMGSZ,
    GENERIC_VEHICLE_LABEL,
    ZONE_ROI_PADDING,
    TRACKER_CONFIG_PATH,
)

logger = logging.getLogger(__name__)


class VehicleTracker:
    """Her kamera icin ayri tracker tutar."""

    def __init__(self):
        self.model_path: str | None = None
        self.models: dict[int, YOLO] = {}
        self._roi_logged_cameras: set[int] = set()
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

    def _get_camera_roi(
        self,
        camera_id: int,
        frame_shape: tuple[int, int, int],
        zones: list[dict] | None,
    ) -> tuple[int, int, int, int] | None:
        if not zones:
            return None

        polygons = [
            zone.get("polygon", [])
            for zone in zones
            if zone.get("active", True) and zone.get("camera_id") == camera_id
        ]
        polygons = [poly for poly in polygons if len(poly) >= 3]
        if not polygons:
            return None

        frame_h, frame_w = frame_shape[:2]
        xs = [pt[0] for poly in polygons for pt in poly]
        ys = [pt[1] for poly in polygons for pt in poly]

        x1 = max(0, int(min(xs) - ZONE_ROI_PADDING))
        y1 = max(0, int(min(ys) - ZONE_ROI_PADDING))
        x2 = min(frame_w, int(max(xs) + ZONE_ROI_PADDING))
        y2 = min(frame_h, int(max(ys) + ZONE_ROI_PADDING))

        if x2 - x1 < 32 or y2 - y1 < 32:
            return None

        if (x2 - x1) >= int(frame_w * 0.95) and (y2 - y1) >= int(frame_h * 0.95):
            return None

        return x1, y1, x2, y2

    def track(self, frames: dict, zones: list[dict] | None = None) -> list[dict]:
        """
        Her kamera frame'i icin track yap.

        Args:
            frames: {camera_id: {"frame": np.ndarray, ...}}
            zones: aktif zone listesi. Varsa zone ROI + padding uzerinden detect yapilir.

        Returns:
            list of detection dicts with track_id
        """
        if not frames:
            return []

        all_detections = []

        for cam_id, frame_data in frames.items():
            frame = frame_data["frame"]
            model = self._get_model(cam_id)
            roi = self._get_camera_roi(cam_id, frame.shape, zones)
            crop_x1 = crop_y1 = 0
            inference_frame = frame

            if roi is not None:
                crop_x1, crop_y1, crop_x2, crop_y2 = roi
                inference_frame = frame[crop_y1:crop_y2, crop_x1:crop_x2]
                if cam_id not in self._roi_logged_cameras:
                    logger.info(
                        f"Kamera {cam_id} ROI detect aktif: "
                        f"({crop_x1}, {crop_y1}) - ({crop_x2}, {crop_y2})"
                    )
                    self._roi_logged_cameras.add(cam_id)

            results = model.track(
                inference_frame,
                persist=True,
                conf=DETECTION_CONF,
                iou=NMS_IOU,
                classes=VEHICLE_CLASSES,
                imgsz=IMGSZ,
                verbose=False,
                tracker=str(TRACKER_CONFIG_PATH),
            )

            if not results or not results[0].boxes:
                continue

            result = results[0]

            for box in result.boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                x1 += crop_x1
                x2 += crop_x1
                y1 += crop_y1
                y2 += crop_y1
                track_id = int(box.id[0]) if box.id is not None else None

                raw_class_name = result.names[int(box.cls[0])]

                all_detections.append({
                    "camera_id": cam_id,
                    "bbox": [int(x1), int(y1), int(x2), int(y2)],
                    "confidence": float(box.conf[0]),
                    "class_id": int(box.cls[0]),
                    "class_name": GENERIC_VEHICLE_LABEL,
                    "raw_class_name": raw_class_name,
                    "track_id": track_id,
                    "timestamp": frame_data["timestamp"],
                    "frame": frame,
                })

        return all_detections
