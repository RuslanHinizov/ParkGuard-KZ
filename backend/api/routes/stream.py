import asyncio
import json
import logging
import psutil
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse

from api.websocket import ws_manager
from config import (
    CAMERAS,
    DATA_DIR,
    MEDIA_MTX_HLS_BASE_URL,
    MEDIA_MTX_PATH_PREFIX,
    MEDIA_MTX_RTSP_BASE_URL,
    MEDIA_MTX_WEBRTC_BASE_URL,
    VIDEO_STREAM_FALLBACK_MODE,
    VIDEO_STREAM_MODE,
)
from core.system_metrics import get_gpu_metrics

logger = logging.getLogger(__name__)

router = APIRouter(tags=["stream"])


def _get_camera(camera_id: int) -> dict:
    for camera in CAMERAS:
        if camera["id"] == camera_id:
            return camera
    raise HTTPException(status_code=404, detail="Kamera bulunamadi")


def _is_local_file_source(source: str) -> bool:
    if not source:
        return False
    lowered = source.lower()
    if lowered.startswith(("rtsp://", "rtsps://", "http://", "https://")):
        return False
    return Path(source).exists()


def _join_url(base: str, suffix: str) -> str:
    return f"{base.rstrip('/')}/{suffix.lstrip('/')}"


@router.get("/api/stream/source/{camera_id}")
async def get_stream_source(camera_id: int, request: Request):
    camera = _get_camera(camera_id)
    camera_source = camera["url"]
    path_name = f"{MEDIA_MTX_PATH_PREFIX}{camera_id}"

    if _is_local_file_source(camera_source):
        local_source = Path(camera_source)
        source_version = int(local_source.stat().st_mtime)
        return {
            "camera_id": camera_id,
            "mode": "file",
            "fallback_mode": None,
            "label": camera["name"],
            "file_url": f"/api/stream/dev-file/{camera_id}?v={source_version}",
            "hls_url": None,
            "whep_url": None,
            "rtsp_url": None,
            "metadata_ws_url": f"/ws/metadata/{camera_id}",
        }

    return {
        "camera_id": camera_id,
        "mode": VIDEO_STREAM_MODE,
        "fallback_mode": VIDEO_STREAM_FALLBACK_MODE,
        "label": camera["name"],
        "file_url": None,
        "hls_url": _join_url(MEDIA_MTX_HLS_BASE_URL, f"{path_name}/index.m3u8"),
        "whep_url": _join_url(MEDIA_MTX_WEBRTC_BASE_URL, f"{path_name}/whep"),
        "rtsp_url": _join_url(MEDIA_MTX_RTSP_BASE_URL, path_name),
        "metadata_ws_url": f"/ws/metadata/{camera_id}",
    }


@router.get("/api/stream/dev-file/{camera_id}")
async def get_dev_file_stream(camera_id: int):
    camera = _get_camera(camera_id)
    source = Path(camera["url"])
    if not source.exists() or not source.is_file():
        raise HTTPException(status_code=404, detail="Yerel test videosu bulunamadi")
    return FileResponse(path=str(source), media_type="video/mp4", filename=source.name)


@router.websocket("/ws/stream/{camera_id}")
async def ws_stream(ws: WebSocket, camera_id: int):
    await ws_manager.connect_stream(ws, camera_id)
    try:
        while True:
            msg = await ws.receive_text()
            if msg == "ping":
                await ws.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(ws)
    except Exception as e:
        logger.debug(f"Legacy stream WS kapandi (kamera {camera_id}): {e}")
        ws_manager.disconnect(ws)


@router.websocket("/ws/metadata/{camera_id}")
async def ws_metadata(ws: WebSocket, camera_id: int):
    await ws_manager.connect_metadata(ws, camera_id)
    try:
        while True:
            msg = await ws.receive_text()
            if msg == "ping":
                await ws.send_text('{"type":"pong"}')
    except WebSocketDisconnect:
        ws_manager.disconnect(ws)
    except Exception as e:
        logger.debug(f"Metadata WS kapandi (kamera {camera_id}): {e}")
        ws_manager.disconnect(ws)


@router.websocket("/ws/alarms")
async def ws_alarms(ws: WebSocket):
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
    from core.log_buffer import log_buffer

    await ws.accept()
    try:
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

            gpu_metrics = get_gpu_metrics()
            if gpu_metrics["gpu_available"]:
                stats["gpu"] = gpu_metrics["gpu_util_percent"]
                stats["gpu_memory"] = gpu_metrics["gpu_memory_util_percent"]
                stats["vram_used"] = gpu_metrics["vram_used_gb"]
                stats["vram_total"] = gpu_metrics["vram_total_gb"]
                stats["gpu_name"] = gpu_metrics["gpu_name"]

            await ws.send_text(json.dumps(stats))
            await asyncio.sleep(2)

    except WebSocketDisconnect:
        ws_manager.disconnect(ws)
    except Exception:
        ws_manager.disconnect(ws)
