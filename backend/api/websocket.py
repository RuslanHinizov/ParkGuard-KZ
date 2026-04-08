import cv2
import json
import logging
import numpy as np
import time
from fastapi import WebSocket

from config import WS_FRAME_HEIGHT, WS_FRAME_QUALITY, WS_FRAME_WIDTH

logger = logging.getLogger(__name__)

COLORS = {
    "normal": (0, 255, 0),
    "violation": (0, 0, 255),
}


class WSManager:
    def __init__(self):
        self.stream_clients: dict[int, list[WebSocket]] = {}
        self.metadata_clients: dict[int, list[WebSocket]] = {}
        self.alarm_clients: list[WebSocket] = []
        self.stats_clients: list[WebSocket] = []

    async def connect_stream(self, ws: WebSocket, camera_id: int) -> None:
        await ws.accept()
        self.stream_clients.setdefault(camera_id, []).append(ws)
        logger.info(f"Legacy stream client baglandi: Kamera {camera_id}")

    async def connect_metadata(self, ws: WebSocket, camera_id: int) -> None:
        await ws.accept()
        self.metadata_clients.setdefault(camera_id, []).append(ws)
        logger.info(f"Metadata client baglandi: Kamera {camera_id}")

    async def connect_alarms(self, ws: WebSocket) -> None:
        await ws.accept()
        self.alarm_clients.append(ws)
        logger.info("Alarm client baglandi")

    async def connect_stats(self, ws: WebSocket) -> None:
        await ws.accept()
        self.stats_clients.append(ws)
        logger.info("Stats client baglandi")

    def disconnect(self, ws: WebSocket) -> None:
        for cam_id, clients in self.stream_clients.items():
            if ws in clients:
                clients.remove(ws)
                logger.info(f"Legacy stream client ayrildi: Kamera {cam_id}")
        for cam_id, clients in self.metadata_clients.items():
            if ws in clients:
                clients.remove(ws)
                logger.info(f"Metadata client ayrildi: Kamera {cam_id}")
        if ws in self.alarm_clients:
            self.alarm_clients.remove(ws)
            logger.info("Alarm client ayrildi")
        if ws in self.stats_clients:
            self.stats_clients.remove(ws)
            logger.info("Stats client ayrildi")

    def _annotate_frame(
        self,
        frame: np.ndarray,
        detections: list[dict],
        camera_id: int,
        zones: list[dict] | None = None,
    ) -> bytes:
        annotated = cv2.resize(frame, (WS_FRAME_WIDTH, WS_FRAME_HEIGHT))
        scale_x = WS_FRAME_WIDTH / frame.shape[1]
        scale_y = WS_FRAME_HEIGHT / frame.shape[0]

        if zones:
            overlay = annotated.copy()
            for zone in zones:
                if zone["camera_id"] != camera_id or not zone.get("active", True):
                    continue
                pts = np.array(zone["polygon"], dtype=np.float64)
                pts[:, 0] *= scale_x
                pts[:, 1] *= scale_y
                pts = pts.astype(np.int32)

                hex_color = zone.get("color", "#FF0000").lstrip("#")
                r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
                cv2.fillPoly(overlay, [pts], (b, g, r))
                cv2.polylines(annotated, [pts], True, (b, g, r), 2)

            cv2.addWeighted(overlay, 0.3, annotated, 0.7, 0, annotated)

        for det in detections:
            if det["camera_id"] != camera_id:
                continue

            x1, y1, x2, y2 = det["bbox"]
            x1, y1 = int(x1 * scale_x), int(y1 * scale_y)
            x2, y2 = int(x2 * scale_x), int(y2 * scale_y)

            is_violation = det.get("in_violation", False)
            color = COLORS["violation"] if is_violation else COLORS["normal"]
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)

            label = f"ID:{det.get('track_id', '?')} {det.get('class_name', 'vehicle')}"
            if det.get("plate"):
                label += f" | {det['plate']}"

            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(annotated, (x1, y1 - th - 8), (x1 + tw + 4, y1), color, -1)
            cv2.putText(
                annotated,
                label,
                (x1 + 2, y1 - 4),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1,
            )

        _, buffer = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, WS_FRAME_QUALITY])
        return buffer.tobytes()

    def _build_metadata_payload(
        self,
        frame: np.ndarray,
        detections: list[dict],
        camera_id: int,
        zones: list[dict] | None = None,
    ) -> dict:
        filtered_detections = []
        for det in detections:
            if det["camera_id"] != camera_id:
                continue
            filtered_detections.append(
                {
                    "camera_id": det["camera_id"],
                    "bbox": [round(float(v), 1) for v in det["bbox"]],
                    "confidence": round(float(det.get("confidence", 0.0)), 4),
                    "class_id": det.get("class_id"),
                    "class_name": det.get("class_name", "vehicle"),
                    "track_id": det.get("track_id"),
                    "plate": det.get("plate"),
                    "plate_conf": round(float(det.get("plate_conf", 0.0)), 4) if det.get("plate_conf") is not None else None,
                    "in_violation": bool(det.get("in_violation", False)),
                }
            )

        filtered_zones = []
        if zones:
            for zone in zones:
                if zone["camera_id"] != camera_id or not zone.get("active", True):
                    continue
                filtered_zones.append(
                    {
                        "id": zone["id"],
                        "camera_id": zone["camera_id"],
                        "name": zone["name"],
                        "polygon": zone["polygon"],
                        "color": zone.get("color", "#FF0000"),
                        "active": zone.get("active", True),
                    }
                )

        return {
            "camera_id": camera_id,
            "frame_width": int(frame.shape[1]),
            "frame_height": int(frame.shape[0]),
            "timestamp_ms": int(time.time() * 1000),
            "detections": filtered_detections,
            "zones": filtered_zones,
        }

    async def broadcast_detections(
        self,
        frames: dict,
        detections: list[dict],
        zones: list[dict] | None = None,
    ) -> None:
        for cam_id, frame_data in frames.items():
            if cam_id not in self.stream_clients or not self.stream_clients[cam_id]:
                continue

            frame_bytes = self._annotate_frame(frame_data["frame"], detections, cam_id, zones)

            dead: list[WebSocket] = []
            for ws in self.stream_clients[cam_id]:
                try:
                    await ws.send_bytes(frame_bytes)
                except Exception as e:
                    logger.debug(f"Legacy stream client koptu (kamera {cam_id}): {e}")
                    dead.append(ws)

            for ws in dead:
                self.disconnect(ws)

    async def broadcast_metadata(
        self,
        frames: dict,
        detections: list[dict],
        zones: list[dict] | None = None,
    ) -> None:
        for cam_id, frame_data in frames.items():
            if cam_id not in self.metadata_clients or not self.metadata_clients[cam_id]:
                continue

            payload = self._build_metadata_payload(frame_data["frame"], detections, cam_id, zones)
            data = json.dumps(payload)

            dead: list[WebSocket] = []
            for ws in self.metadata_clients[cam_id]:
                try:
                    await ws.send_text(data)
                except Exception as e:
                    logger.debug(f"Metadata client koptu (kamera {cam_id}): {e}")
                    dead.append(ws)

            for ws in dead:
                self.disconnect(ws)

    async def broadcast_alarm(self, alarm: dict) -> None:
        data = json.dumps(alarm, default=str)
        dead: list[WebSocket] = []

        for ws in self.alarm_clients:
            try:
                await ws.send_text(data)
            except Exception as e:
                logger.debug(f"Alarm client koptu: {e}")
                dead.append(ws)

        for ws in dead:
            self.disconnect(ws)

    async def broadcast_stats(self, stats: dict) -> None:
        data = json.dumps(stats)
        dead: list[WebSocket] = []

        for ws in self.stats_clients:
            try:
                await ws.send_text(data)
            except Exception as e:
                logger.debug(f"Stats client koptu: {e}")
                dead.append(ws)

        for ws in dead:
            self.disconnect(ws)


ws_manager = WSManager()
