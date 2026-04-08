@echo off
setlocal

set "REPO=C:\Users\rusla\Desktop\Project-university\ParkGuard KZ"
set "BACKEND_DIR=%REPO%\backend"
set "PYTHON_EXE=%BACKEND_DIR%\venv\Scripts\python.exe"
set "OUT_LOG=%REPO%\backend_1280_live.out.log"
set "ERR_LOG=%REPO%\backend_1280_live.err.log"

cd /d "%BACKEND_DIR%"

set "CAMERA_1_URL=%REPO%\videos\fixed.mp4"
set "ACTIVE_CAMERA_IDS=1"
set "WS_FRAME_WIDTH=1280"
set "WS_FRAME_HEIGHT=720"
set "WS_FRAME_QUALITY=92"

"%PYTHON_EXE%" main.py 1>"%OUT_LOG%" 2>"%ERR_LOG%"

