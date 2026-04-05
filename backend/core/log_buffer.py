"""
log_buffer.py — Döngüsel bellek içi log tamponu

Logging handler olarak çalışır. Son N log kaydını bellekte tutar.
/ws/logs WebSocket endpoint'i buradan okur.
"""

import logging
import threading
from collections import deque
from datetime import datetime
from typing import TypedDict


class LogEntry(TypedDict):
    seq: int
    time: str
    level: str
    name: str
    message: str


class LogBuffer(logging.Handler):
    """Thread-safe döngüsel log tamponu (maks. 500 satır)."""

    MAX_SIZE = 500

    def __init__(self) -> None:
        super().__init__()
        self._lock = threading.Lock()
        self._buffer: deque[LogEntry] = deque(maxlen=self.MAX_SIZE)
        self._seq = 0

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
        except Exception:
            msg = record.getMessage()

        with self._lock:
            self._seq += 1
            entry: LogEntry = {
                "seq": self._seq,
                "time": datetime.fromtimestamp(record.created).strftime("%H:%M:%S"),
                "level": record.levelname,
                "name": record.name,
                "message": msg,
            }
            self._buffer.append(entry)

    def get_since(self, last_seq: int) -> list[LogEntry]:
        """last_seq'den sonraki tüm kayıtları döndür."""
        with self._lock:
            return [e for e in self._buffer if e["seq"] > last_seq]

    def get_all(self) -> list[LogEntry]:
        with self._lock:
            return list(self._buffer)


# Singleton
log_buffer = LogBuffer()
log_buffer.setFormatter(
    logging.Formatter("%(asctime)s [%(name)s] %(levelname)s: %(message)s",
                      datefmt="%Y-%m-%d %H:%M:%S")
)
