"""
camera_manager.py — Kamera Yönetim Modülü

AMAÇ: Her Hikvision kamerayı ayrı thread'te yönet.
      FFmpeg CUDA (NVDEC) ile GPU decode yap.
      Frame'leri FrameBuffer'a koy (eski frame'leri at).
      FPS counter tut.
      Bağlantı kopunca otomatik yeniden bağlan.

KRİTİK NOKTA:
  Queue değil FrameBuffer kullan!
  Queue dolunca bekler → gecikme birikir → FPS düşer.
  FrameBuffer hep en güncel frame'i tutar → sıfır bekleme.
"""

import os
import cv2
import time
import logging
import threading
import numpy as np
from collections import deque
from config import (
    CAMERAS, RTSP_BUFFER_SIZE, RTSP_MAX_DELAY,
    RECONNECT_DELAY_SEC, RECONNECT_MAX_TRIES, RECONNECT_BACKOFF_MAX,
)

logger = logging.getLogger(__name__)


class FrameBuffer:
    """Thread-safe en güncel frame buffer. Queue değil!

    Neden Queue değil:
    - Queue dolarsa put() bekler → gecikme birikir
    - FrameBuffer hep üstüne yazar → hiç bekleme yok
    - Her zaman en güncel frame okunur
    """

    def __init__(self):
        self.frame: np.ndarray | None = None
        self.timestamp: float = 0.0
        self.frame_id: int = 0
        self._lock = threading.Lock()

    def update(self, frame: np.ndarray) -> None:
        with self._lock:
            self.frame = frame
            self.timestamp = time.time()
            self.frame_id += 1

    def get(self) -> tuple[np.ndarray | None, float, int]:
        with self._lock:
            if self.frame is None:
                return None, 0.0, 0
            return self.frame.copy(), self.timestamp, self.frame_id


class FPSCounter:
    """Sliding window FPS hesaplama (son 60 frame)."""

    def __init__(self, window: int = 60):
        self.timestamps: deque = deque(maxlen=window)

    def tick(self) -> None:
        self.timestamps.append(time.time())

    @property
    def fps(self) -> float:
        if len(self.timestamps) < 2:
            return 0.0
        elapsed = self.timestamps[-1] - self.timestamps[0]
        return len(self.timestamps) / elapsed if elapsed > 0 else 0.0


class CameraWorker:
    """
    Tek kamera için decode worker.
    FFmpeg CUDA backend ile NVDEC decode yapar.
    Daemon thread olarak çalışır.
    """

    def __init__(self, camera_config: dict):
        self.config = camera_config
        self.camera_id: int = camera_config["id"]
        self.name: str = camera_config["name"]
        self.url: str = camera_config["url"]
        self.buffer = FrameBuffer()
        self.fps_counter = FPSCounter()
        self._running: bool = False
        self._thread: threading.Thread | None = None
        self._connected: bool = False

    @property
    def connected(self) -> bool:
        return self._connected

    def _build_capture(self) -> cv2.VideoCapture:
        """FFmpeg CUDA decode ile VideoCapture oluştur.

        Hikvision kameralar için optimize edilmiş parametreler:
        - rtsp_transport=tcp: UDP paket kaybını önler
        - hwaccel=cuda: NVDEC GPU decode aktif
        - fflags=nobuffer: gecikme biriktirmez
        - max_delay=0: sıfır gecikme
        """

        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = (
            f"rtsp_transport;tcp|"
            f"buffer_size;{RTSP_BUFFER_SIZE}|"
            f"max_delay;{RTSP_MAX_DELAY}|"
            f"fflags;nobuffer|"
            f"flags;low_delay|"
            f"hwaccel;cuda|"
            f"hwaccel_output_format;cuda"
        )

        cap = cv2.VideoCapture(self.url, cv2.CAP_FFMPEG)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        return cap

    def _decode_loop(self) -> None:
        """Ana decode döngüsü. Bağlantı kopunca exponential backoff ile yeniden bağlan."""

        tries = 0

        while self._running:
            cap = self._build_capture()

            if not cap.isOpened():
                tries += 1
                self._connected = False
                # Exponential backoff: 5, 10, 20, 40, 60, 60, ... sn
                delay = min(RECONNECT_DELAY_SEC * (2 ** (tries - 1)), RECONNECT_BACKOFF_MAX)
                logger.warning(
                    f"Camera {self.camera_id} ({self.name}): "
                    f"baglanamadi (deneme {tries}/{RECONNECT_MAX_TRIES}), "
                    f"{delay:.0f}sn bekleniyor..."
                )
                if tries >= RECONNECT_MAX_TRIES:
                    logger.error(
                        f"Camera {self.camera_id} ({self.name}): "
                        f"{RECONNECT_MAX_TRIES} denemeden sonra baglanti saglanamadi, worker durduruluyor."
                    )
                    break
                time.sleep(delay)
                continue

            logger.info(f"Camera {self.camera_id} ({self.name}): baglandi")
            self._connected = True
            tries = 0
            consecutive_failures = 0

            # Video dosyası için FPS throttle (RTSP'de gerekmez)
            is_file = not (self.url.startswith("rtsp://") or self.url.startswith("http"))
            video_fps = cap.get(cv2.CAP_PROP_FPS) if is_file else 0.0
            frame_interval = 1.0 / video_fps if video_fps > 0 else 0.0
            last_frame_time = time.time()

            while self._running:
                ret, frame = cap.read()

                if not ret:
                    consecutive_failures += 1
                    if consecutive_failures > 10:
                        logger.warning(
                            f"Camera {self.camera_id}: frame alinamiyor, "
                            f"yeniden baglaniliyor..."
                        )
                        self._connected = False
                        break
                    continue

                consecutive_failures = 0

                # Video dosyasını orijinal FPS'inde oynat
                if frame_interval > 0:
                    now = time.time()
                    elapsed = now - last_frame_time
                    sleep_time = frame_interval - elapsed
                    if sleep_time > 0:
                        time.sleep(sleep_time)
                    last_frame_time = time.time()

                self.buffer.update(frame)
                self.fps_counter.tick()

            cap.release()

            if self._running:
                logger.info(f"Camera {self.camera_id}: yeniden baglaniliyor...")
                time.sleep(RECONNECT_DELAY_SEC)

    def start(self) -> None:
        self._running = True
        self._thread = threading.Thread(
            target=self._decode_loop,
            daemon=True,
            name=f"CameraThread-{self.camera_id}",
        )
        self._thread.start()
        logger.info(f"Camera {self.camera_id} ({self.name}): worker baslatildi")

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        self._connected = False


class CameraManager:
    """Tüm kameraları yönetir. start_all / stop_all ile kontrol."""

    def __init__(self):
        self.workers: dict[int, CameraWorker] = {}

    def start_all(self) -> None:
        for cam_config in CAMERAS:
            worker = CameraWorker(cam_config)
            worker.start()
            self.workers[cam_config["id"]] = worker
        logger.info(f"{len(self.workers)} kamera baslatildi")

    def get_frames(self) -> dict:
        """
        Tüm kameralardan en güncel frame'leri al.
        Döndürür: {camera_id: {"frame": np.ndarray, "timestamp": float, "frame_id": int}}
        """
        result = {}
        for cam_id, worker in self.workers.items():
            frame, ts, fid = worker.buffer.get()
            if frame is not None:
                result[cam_id] = {
                    "frame": frame,
                    "timestamp": ts,
                    "frame_id": fid,
                }
        return result

    def get_frame(self, camera_id: int) -> np.ndarray | None:
        """Tek kameradan frame al."""
        if camera_id in self.workers:
            frame, _, _ = self.workers[camera_id].buffer.get()
            return frame
        return None

    def get_fps_all(self) -> dict[int, float]:
        return {cid: round(w.fps_counter.fps, 1) for cid, w in self.workers.items()}

    def get_status_all(self) -> dict[int, dict]:
        return {
            cid: {
                "name": w.name,
                "connected": w.connected,
                "fps": round(w.fps_counter.fps, 1),
            }
            for cid, w in self.workers.items()
        }

    def stop_all(self) -> None:
        for worker in self.workers.values():
            worker.stop()
        logger.info("Tum kameralar durduruldu")
