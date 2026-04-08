@echo off
echo ============================================
echo   ParkGuard KZ — Kurulum Scripti
echo   Windows 11 + RTX 4060 Mobile
echo ============================================
echo.

:: Python sanal ortam
echo [1/7] Python sanal ortam olusturuluyor...
cd /d "%~dp0\..\backend"
python -m venv venv
call venv\Scripts\activate

:: PyTorch CUDA 12.1
echo.
echo [2/7] PyTorch CUDA 12.1 yukleniyor...
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121

:: Ana bagimliliklar
echo.
echo [3/7] Backend bagimliliklari yukleniyor...
pip install ultralytics fastapi "uvicorn[standard]" redis opencv-python-headless
pip install shapely pydantic python-multipart psutil python-dotenv

:: PaddleOCR + nomeroff-net (KZ plaka OCR)
echo.
echo [4/7] OCR kutuphaneleri yukleniyor...
pip install paddlepaddle-gpu paddleocr
pip install nomeroff-net==4.0.1

:: YOLOv8s model indir
echo.
echo [5/7] YOLOv8s modeli indiriliyor...
python -c "from ultralytics import YOLO; YOLO('yolov8s.pt')"
if not exist "models" mkdir models
move yolov8s.pt models\ 2>nul

:: TensorRT export
echo.
echo [6/7] TensorRT FP16 export yapiliyor...
python "%~dp0\export_trt.py"

:: Frontend
echo.
echo [7/7] Frontend bagimliliklari yukleniyor...
cd /d "%~dp0\..\frontend"
call npm install

:: Redis (Docker)
echo.
echo Redis baslatiliyor (Docker)...
docker run -d -p 6379:6379 --name parkguard-redis redis:alpine 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Redis zaten calisiyor veya Docker bulunamadi.
    echo Redis olmadan da calisabilir (in-memory mode).
)

echo.
echo ============================================
echo   Kurulum tamamlandi!
echo ============================================
echo.
echo Baslatmak icin:
echo   1. cd backend ^&^& call venv\Scripts\activate
echo   2. python main.py
echo   3. cd frontend ^&^& npm run dev
echo   4. Tarayici: http://localhost:5173
echo.
pause
