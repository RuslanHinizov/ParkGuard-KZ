@echo off
setlocal

set "REPO=C:\Users\rusla\Desktop\Project-university\ParkGuard KZ"
set "BACKEND_DIR=%REPO%\backend"
set "PYTHON_EXE=%BACKEND_DIR%\venv\Scripts\python.exe"
set "OUT_LOG=%REPO%\backend_videos_live.out.log"
set "ERR_LOG=%REPO%\backend_videos_live.err.log"

cd /d "%BACKEND_DIR%"

set "CAMERA_1_URL=%REPO%\videos\1_kamera_browser_faststart.mp4"
set "CAMERA_2_URL=%REPO%\videos\2_kamera_browser_faststart.mp4"
set "CAMERA_3_URL=%REPO%\videos\3_kamera_faststart.mp4"
set "FILE_SOURCE_LOOP=true"
set "VIDEO_STREAM_MODE=websocket"
set "WS_FRAME_WIDTH=960"
set "WS_FRAME_HEIGHT=540"
set "WS_FRAME_QUALITY=80"

"%PYTHON_EXE%" main.py 1>"%OUT_LOG%" 2>"%ERR_LOG%"
