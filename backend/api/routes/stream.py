"""
stream.py — WebSocket Stream Endpoints

WS /ws/stream/{camera_id}  → Annotated frame binary stream
WS /ws/alarms              → Gerçek zamanlı alarm JSON
WS /ws/stats               → FPS + sistem metrikleri (her 2sn)
"""

import json
import asyncio
import logging
import psutil
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from api.websocket import ws_manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["stream"])


@router.websocket("/ws/stream/{camera_id}")
async def ws_stream(ws: WebSocket, camera_id: int):
    """
    Kamera stream WebSocket.
    Binary JPEG frame gönderir (960×540, quality=80).
    Annotated: bbox, track_id, plaka, zone.
    Client ping gönderirse pong ile yanıt verir.
    """
    await ws_manager.connect_stream(ws, camera_id)
    try:
        while True:
            msg = await ws.receive_text()
            if msg == "ping":
                await ws.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(ws)
    except Exception as e:
        logger.debug(f"Stream WS kapandi (kamera {camera_id}): {e}")
        ws_manager.disconnect(ws)


@router.websocket("/ws/alarms")
async def ws_alarms(ws: WebSocket):
    """
    Alarm WebSocket.
    Yeni alarm oluştuğunda JSON gönderir.
    Client ping gönderirse pong ile yanıt verir.
    """
    await ws_manager.connect_alarms(ws)
    try:
        while True:
            msg = await ws.receive_text()
            if msg == "ping":
                await ws.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(ws)
    except Exception as e:
        logger.debug(f"Alarm WS kapandi: {e}")
        ws_manager.disconnect(ws)


@router.websocket("/ws/logs")
async def ws_logs(ws: WebSocket):
    """
    Log stream WebSocket.
    İlk bağlantıda son 100 satırı gönderir, sonra her 0.5sn yeni kayıtları gönderir.
    """
    from core.log_buffer import log_buffer
    await ws.accept()
    try:
        # İlk yükleme: son kayıtları gönder
        initial = log_buffer.get_all()[-100:]
        if initial:
            await ws.send_json({"entries": initial})
        last_seq = initial[-1]["seq"] if initial else 0

        while True:
            await asyncio.sleep(0.5)
            new_entries = log_buffer.get_since(last_seq)
            if new_entries:
                await ws.send_json({"entries": new_entries})
                last_seq = new_entries[-1]["seq"]
    except WebSocketDisconnect:
        pass
    except Exception:
        pass


@router.websocket("/ws/stats")
async def ws_stats(ws: WebSocket):
    """
    Sistem metrikleri WebSocket.
    Her 2 saniyede JSON gönderir: fps, gpu, cpu, ram, vram.
    """
    await ws_manager.connect_stats(ws)
    try:
        while True:
            from main import camera_mgr

            stats = {
                "fps": camera_mgr.get_fps_all(),
                "cpu": psutil.cpu_percent(),
                "ram": round(psutil.virtual_memory().used / (1024**3), 1),
                "cameras": camera_mgr.get_status_all(),
            }

            try:
                import torch
                if torch.cuda.is_available():
                    stats["gpu"] = round(torch.cuda.memory_allocated(0) / (1024**3), 2)
                    stats["vram"] = round(
                        torch.cuda.get_device_properties(0).total_memory / (1024**3), 1
                    )
            except ImportError:
                pass

            await ws.send_text(json.dumps(stats))
            await asyncio.sleep(2)

    except WebSocketDisconnect:
        ws_manager.disconnect(ws)
    except Exception:
        # Bağlantı kapandıktan sonra send çağrısı veya başka hata
        ws_manager.disconnect(ws)
