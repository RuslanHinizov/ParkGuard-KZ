@echo off
setlocal

set "REPO=C:\Users\rusla\Desktop\Project-university\ParkGuard KZ"
set "FRONTEND_DIR=%REPO%\frontend"
set "NPM_CMD=C:\Program Files\nodejs\npm.cmd"
set "OUT_LOG=%REPO%\frontend_live.out.log"
set "ERR_LOG=%REPO%\frontend_live.err.log"

cd /d "%FRONTEND_DIR%"

call "%NPM_CMD%" run dev -- --host 0.0.0.0 1>"%OUT_LOG%" 2>"%ERR_LOG%"

