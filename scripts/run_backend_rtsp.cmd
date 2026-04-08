@echo off
setlocal

set "REPO=C:\Users\rusla\Desktop\Project-university\ParkGuard KZ"
set "BACKEND_DIR=%REPO%\backend"
set "PYTHON_EXE=%BACKEND_DIR%\venv\Scripts\python.exe"
set "OUT_LOG=%REPO%\backend_rtsp_live.out.log"
set "ERR_LOG=%REPO%\backend_rtsp_live.err.log"

cd /d "%BACKEND_DIR%"

set "VIDEO_STREAM_MODE=webrtc"
set "VIDEO_STREAM_FALLBACK_MODE=hls"
set "MEDIA_MTX_RTSP_BASE_URL=rtsp://127.0.0.1:8554"
set "MEDIA_MTX_HLS_BASE_URL=http://127.0.0.1:8888"
set "MEDIA_MTX_WEBRTC_BASE_URL=http://127.0.0.1:8889"

"%PYTHON_EXE%" main.py 1>"%OUT_LOG%" 2>"%ERR_LOG%"
