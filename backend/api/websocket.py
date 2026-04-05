"""
websocket.py — WebSocket Yönetim Modülü

AMAÇ: React'a annotated frame ve alarm verisi gönder.
      Frame: JPEG binary (960x540, quality=80)
      Alarmlar: JSON
      Stats: FPS + GPU bilgisi (her 2 saniye)

Annotation detayları:
  - Araç bbox (yeşil = normal, kırmızı = ihlal)
  - Track ID (bbox sol üst)
  - Plaka (tespit edilmişse bbox üstü)
  - Zone polygon (yarı saydam renk)
"""

import cv2
import json
import asyncio
import logging
import numpy as np
from fastapi import WebSocket, WebSocketDisconnect
from config import WS_FRAME_QUALITY, WS_FRAME_WIDTH, WS_FRAME_HEIGHT

logger = logging.getLogger(__name__)

COLORS = {
    "normal": (0, 255, 0),      # Yeşil — normal araç
    "violation": (0, 0, 255),    # Kırmızı — ihlal
    "plate": (0, 255, 255),      # Sarı — plaka metni
    "zone": (255, 0, 0),         # Mavi — zone polygon
}


class WSManager:

    def __init__(self):
        self.stream_clients: dict[int, list[WebSocket]] = {}  # cam_id → clients
        self.alarm_clients: list[WebSocket] = []
        self.stats_clients: list[WebSocket] = []

    async def connect_stream(self, ws: WebSocket, camera_id: int) -> None:
        await ws.accept()
        if camera_id not in self.stream_clients:
            self.stream_clients[camera_id] = []
        self.stream_clients[camera_id].append(ws)
        logger.info(f"Stream client baglandi: Kamera {camera_id}")

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
                logger.info(f"Stream client ayrildi: Kamera {cam_id}")
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
        """Frame üzerine bbox, plaka ve zone çiz, JPEG'e dönüştür."""

        annotated = cv2.resize(frame, (WS_FRAME_WIDTH, WS_FRAME_HEIGHT))
        scale_x = WS_FRAME_WIDTH / frame.shape[1]
        scale_y = WS_FRAME_HEIGHT / frame.shape[0]

        # Zone polygonları çiz (yarı saydam)
        if zones:
            overlay = annotated.copy()
            for zone in zones:
                if zone["camera_id"] != camera_id or not zone.get("active", True):
                    continue
                pts = np.array(zone["polygon"], dtype=np.float64)
                pts[:, 0] *= scale_x
                pts[:, 1] *= scale_y
                pts = pts.astype(np.int32)

                # Hex renk → BGR
                hex_color = zone.get("color", "#FF0000").lstrip("#")
                r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)

                cv2.fillPoly(overlay, [pts], (b, g, r))
                cv2.polylines(annotated, [pts], True, (b, g, r), 2)

                # Zone adı
                cx = int(pts[:, 0].mean())
                cy = int(pts[:, 1].mean())
                cv2.putText(
                    annotated, zone["name"], (cx - 30, cy),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1,
                )

            cv2.addWeighted(overlay, 0.3, annotated, 0.7, 0, annotated)

        # Araç tespitlerini çiz
        for det in detections:
            if det["camera_id"] != camera_id:
                continue

            x1, y1, x2, y2 = det["bbox"]
            x1, y1 = int(x1 * scale_x), int(y1 * scale_y)
            x2, y2 = int(x2 * scale_x), int(y2 * scale_y)

            is_violation = det.get("in_violation", False)
            color = COLORS["violation"] if is_violation else COLORS["normal"]

            # Bbox
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)

            # Label: Track ID + sınıf
            label = f"ID:{det.get('track_id', '?')} {det.get('class_name', 'car')}"
            if det.get("plate"):
                label += f" | {det['plate']}"

            # Label arka plan
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(annotated, (x1, y1 - th - 8), (x1 + tw + 4, y1), color, -1)
            cv2.putText(
                annotated, label, (x1 + 2, y1 - 4),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1,
            )

        # JPEG encode
        _, buffer = cv2.imencode(
            ".jpg", annotated,
            [cv2.IMWRITE_JPEG_QUALITY, WS_FRAME_QUALITY],
        )
        return buffer.tobytes()

    async def broadcast_detections(
        self,
        frames: dict,
        detections: list[dict],
        zones: list[dict] | None = None,
    ) -> None:
        """Her kameranın annotated frame'ini ilgili client'lara gönder."""

        for cam_id, frame_data in frames.items():
            if cam_id not in self.stream_clients:
                continue
            if not self.stream_clients[cam_id]:
                continue

            frame_bytes = self._annotate_frame(
                frame_data["frame"], detections, cam_id, zones
            )

            dead: list[WebSocket] = []
            for ws in self.stream_clients[cam_id]:
                try:
                    await ws.send_bytes(frame_bytes)
                except Exception as e:
                    logger.debug(f"Stream client koptu (kamera {cam_id}): {e}")
                    dead.append(ws)

            for ws in dead:
                self.disconnect(ws)

    async def broadcast_alarm(self, alarm: dict) -> None:
        """Yeni alarm tüm alarm client'larına gönder."""

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
        """Sistem metriklerini stats client'larına gönder."""

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
