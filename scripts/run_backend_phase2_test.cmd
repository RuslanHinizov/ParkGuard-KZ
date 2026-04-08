@echo off
setlocal

set "REPO=C:\Users\rusla\Desktop\Project-university\ParkGuard KZ"
set "BACKEND_DIR=%REPO%\backend"
set "PYTHON_EXE=%BACKEND_DIR%\venv\Scripts\python.exe"
set "OUT_LOG=%REPO%\backend_phase2_live.out.log"
set "ERR_LOG=%REPO%\backend_phase2_live.err.log"

cd /d "%BACKEND_DIR%"

set "CAMERA_1_URL=%REPO%\videos\IP_PTZ_Camera_Kazgurt_20260408132837_20260408133259_2678688_browser_trim_fast.mp4"
set "ACTIVE_CAMERA_IDS=1"
set "WS_FRAME_WIDTH=1280"
set "WS_FRAME_HEIGHT=720"
set "WS_FRAME_QUALITY=92"

"%PYTHON_EXE%" main.py 1>"%OUT_LOG%" 2>"%ERR_LOG%"
