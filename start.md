# START.md

# Korgen Vision - Быстрый и полный запуск проекта на новом ноутбуке

Этот файл нужен для практического запуска проекта с нуля на другом компьютере.
Ниже описан реальный рабочий порядок: что установить, что скачать, как собрать TensorRT engine и как запустить backend/frontend без лишней теории.

---

## 1. Что это за проект

`Korgen Vision` - это система мониторинга парковки в реальном времени.

Текущий стек проекта:

- Backend: `FastAPI`
- Frontend: `React + Vite`
- Detection/Tracking: `YOLOv8 + ByteTrack`
- OCR: `nomeroff-net` + резервный `PaddleOCR`
- Хранилище/обмен событиями: `SQLite + Redis`
- Дополнительно: `MediaMTX`, `Ollama`, генерация отчётов, аномалии, штрафы

Сейчас проект настроен на работу с:

- `yolov8n.engine`
- Windows
- NVIDIA GPU
- TensorRT

---

## 2. Что обязательно установить на новом ноутбуке

Установи следующее:

1. `Python 3.10`
2. `Node.js 20+`
3. `Docker Desktop`
4. `Git`
5. актуальный `NVIDIA driver`

Если нужен AI Assistant:

6. `Ollama`

Проверка после установки:

```powershell
python --version
node --version
docker --version
git --version
nvidia-smi
```

Если `nvidia-smi` не работает, сначала решай вопрос с драйвером NVIDIA.

---

## 3. Куда класть проект

Не запускай проект из пути вида:

```powershell
\\?\C:\...
```

Это ломает Docker volume mount на Windows.

Нормальный путь:

```powershell
C:\Projects\ParkGuard-KZ
```

Пример:

```powershell
git clone https://github.com/RuslanHinizov/ParkGuard-KZ.git C:\Projects\ParkGuard-KZ
cd C:\Projects\ParkGuard-KZ
```

---

## 4. Создание `.env`

В корне проекта создай файл `.env`.

Пример:

```env
CAMERA_1_URL=rtsp://admin:password@192.168.1.64:554/Streaming/Channels/101
CAMERA_2_URL=rtsp://admin:password@192.168.1.65:554/Streaming/Channels/101
CAMERA_3_URL=rtsp://admin:password@192.168.1.66:554/Streaming/Channels/101
REDIS_URL=redis://localhost:6379
```

Если камеры Hikvision, желательно использовать:

- `H.264`
- substream для AI
- не `H.265`, если важна стабильность

Рекомендуемые параметры камеры:

- Codec: `H.264`
- Resolution: `1280x720` или `960x540`
- FPS: `15` или `20`
- Bitrate: `CBR`
- GOP: `15` или `30`
- `Smart Codec / H.265+` выключить

---

## 5. Установка backend

Открой PowerShell:

```powershell
cd C:\Projects\ParkGuard-KZ\backend
python -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Если `requirements.txt` не поставит `torch` корректно, установи вручную:

```powershell
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements.txt
```

---

## 6. Установка frontend

Во втором окне PowerShell:

```powershell
cd C:\Projects\ParkGuard-KZ\frontend
npm install
```

---

## 7. Запуск Docker-сервисов

Из корня проекта:

```powershell
cd C:\Projects\ParkGuard-KZ
docker compose up -d redis mediamtx
```

Если ты видишь ошибку `too many colons`, значит ты запускаешь проект из неправильного Windows path.
Перейди в обычный путь `C:\...` и запусти команду снова.

Проверка:

```powershell
docker ps
```

Ожидаемо должны быть контейнеры:

- `parkguard-redis`
- `parkguard-mediamtx`

---

## 8. Очень важный момент про TensorRT engine

Файл `yolov8n.engine`, который лежит в репозитории, не стоит считать универсальным.
TensorRT engine нужно собирать на том ноутбуке, на котором проект реально будет запускаться.

Причина:

- engine зависит от GPU
- зависит от драйвера
- зависит от TensorRT
- иногда зависит от версии CUDA/окружения

Поэтому на новом ноутбуке делай так:

```powershell
del C:\Projects\ParkGuard-KZ\backend\models\yolov8n.engine
del C:\Projects\ParkGuard-KZ\backend\models\yolov8n.onnx
```

Если файлов нет, это нормально.

Потом собери engine заново:

```powershell
cd C:\Projects\ParkGuard-KZ\backend
venv\Scripts\activate
python export_engine.py
```

Что делает этот скрипт:

- при необходимости скачивает `yolov8n.pt`
- экспортирует `yolov8n.onnx`
- собирает `yolov8n.engine`

После успешного выполнения в папке `backend\models` должны быть:

- `yolov8n.pt`
- `yolov8n.onnx`
- `yolov8n.engine`

---

## 9. Запуск backend

```powershell
cd C:\Projects\ParkGuard-KZ\backend
venv\Scripts\activate
python main.py
```

Что должно появиться в логах:

- `Tracker modeli yuklendi`
- `nomeroff-net hazir`
- `Inference loop baslatildi`
- `Uvicorn running on http://0.0.0.0:8000`

Если engine реально используется, в runtime-логе появится строка вида:

```text
Loading ...\backend\models\yolov8n.engine for TensorRT inference...
```

---

## 10. Запуск frontend

В отдельном окне:

```powershell
cd C:\Projects\ParkGuard-KZ\frontend
npm run dev -- --host 0.0.0.0
```

Открыть в браузере:

```text
http://127.0.0.1:5173
```

---

## 11. Если нужен AI Assistant

Установи Ollama и запусти:

```powershell
ollama serve
ollama pull gemma4:latest
```

Если AI Assistant не нужен, Ollama можно не запускать.
Это даже лучше для теста FPS, потому что он тоже использует ресурсы.

---

## 12. Минимальный рабочий сценарий запуска

После полной установки тебе обычно нужны 3 окна:

### Окно 1

```powershell
cd C:\Projects\ParkGuard-KZ
docker compose up -d redis mediamtx
```

### Окно 2

```powershell
cd C:\Projects\ParkGuard-KZ\backend
venv\Scripts\activate
python main.py
```

### Окно 3

```powershell
cd C:\Projects\ParkGuard-KZ\frontend
npm run dev -- --host 0.0.0.0
```

---

## 13. Как понять, что всё работает

Проверки:

### Backend health

Открой:

```text
http://127.0.0.1:8000/api/system/health
```

Если backend жив, вернётся JSON.

### Frontend

Открой:

```text
http://127.0.0.1:5173
```

### Проверка engine

Смотри лог backend.
Там должна быть строка загрузки `yolov8n.engine`.

### Проверка камер

В `health` или в UI должны быть:

- `connected: true`
- ненулевой `fps`

---

## 14. Как работает тревога

Общая логика такая:

1. Камера отдаёт frame
2. YOLO обнаруживает машину
3. ByteTrack должен выдать `track_id`
4. Проверяется, находится ли объект в запрещённой зоне
5. Если объект достаточно долго находится в зоне, создаётся alarm
6. Если track подтверждён и OCR сработал, может быть считан номер

Критический момент:

Если `track_id = None`, то:

- OCR не пойдёт
- таймер нарушения не будет считаться правильно
- тревога не появится

То есть detection без стабильного tracking недостаточен.

---

## 15. Почему на другом ноутбуке может не завестись сразу

Основные причины:

1. Неправильный драйвер NVIDIA
2. Не тот Python
3. Не собран локальный TensorRT engine
4. Камеры отдают плохой RTSP поток
5. H.265/HEVC ломает стабильность
6. Docker запускается из `\\?\` path

---

## 16. Частые проблемы и решения

### Проблема: backend запускается, но engine не используется

Проверь:

```powershell
dir C:\Projects\ParkGuard-KZ\backend\models
```

Если `yolov8n.engine` нет:

```powershell
cd C:\Projects\ParkGuard-KZ\backend
venv\Scripts\activate
python export_engine.py
```

---

### Проблема: detection работает, но alarm не появляется

Проверь:

- есть ли `track_id`
- не `ID:None` ли в кадре
- правильно ли нарисована зона
- реально ли объект стоит в зоне достаточно долго

Если на экране `ID:None`, значит проблема в tracking, а не в таймере тревоги.

---

### Проблема: камеры часто отваливаются

Обычно это:

- RTSP поток плохого качества
- H.265
- Smart Codec
- нестабильная сеть

Что делать:

- переключить на `H.264`
- использовать substream
- уменьшить разрешение
- поставить `15 FPS`

---

### Проблема: Docker `too many colons`

Это Windows path issue.
Не запускай compose из:

```powershell
\\?\C:\...
```

Запускай только из обычного:

```powershell
C:\Projects\ParkGuard-KZ
```

---

### Проблема: `torch.cuda.is_available()` возвращает `False`

Проверь:

```powershell
nvidia-smi
```

Если не работает, сначала почини драйвер.

---

### Проблема: frontend открывается, но данных нет

Проверь:

- работает ли backend на `8000`
- отвечает ли `/api/system/health`
- есть ли подключение к камерам

---

## 17. Полезные команды

### Проверить backend

```powershell
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/api/system/health
```

### Проверить frontend

```powershell
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:5173
```

### Посмотреть Docker-контейнеры

```powershell
docker ps
```

### Остановить backend по порту 8000

```powershell
$p = Get-NetTCPConnection -LocalPort 8000 -State Listen | Select-Object -First 1 -ExpandProperty OwningProcess
Stop-Process -Id $p -Force
```

### Остановить frontend по порту 5173

```powershell
$p = Get-NetTCPConnection -LocalPort 5173 -State Listen | Select-Object -First 1 -ExpandProperty OwningProcess
Stop-Process -Id $p -Force
```

---

## 18. Итоговый короткий сценарий

Если всё уже установлено, то каждый раз достаточно:

```powershell
cd C:\Projects\ParkGuard-KZ
docker compose up -d redis mediamtx
```

```powershell
cd C:\Projects\ParkGuard-KZ\backend
venv\Scripts\activate
python main.py
```

```powershell
cd C:\Projects\ParkGuard-KZ\frontend
npm run dev -- --host 0.0.0.0
```

И открыть:

```text
http://127.0.0.1:5173
```

---

## 19. Что важно помнить

- На новом ноутбуке engine лучше пересобрать заново
- Для стабильности камер лучше использовать `H.264`
- Для AI не нужен основной тяжёлый stream, лучше substream
- Если нужен максимальный FPS, не запускай лишние GPU-процессы параллельно
- Если нет `track_id`, alarm не будет работать корректно

