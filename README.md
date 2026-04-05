# ParkGuard KZ — Yasadışı Park Tespit Sistemi / Система обнаружения нарушений парковки

> [🇹🇷 Türkçe](#-türkçe) | [🇷🇺 Русский](#-русский)

---

# 🇹🇷 TÜRKÇE

Yapay zeka destekli, gerçek zamanlı yasadışı park tespit sistemi.
**YOLOv8 + ByteTrack + nomeroff-net + React Dashboard.**

---

## Ne Yapar?

- Hikvision IP kameralara RTSP üzerinden bağlanır
- YOLOv8 ile araçları GPU'da tespit eder
- ByteTrack ile her araca benzersiz ID atar
- Shapely ile aracın yasak bölgede olup olmadığını kontrol eder
- nomeroff-net ile plaka okur (KZ modeli)
- Araç **5 dakikadan fazla** bölgede kalırsa alarm üretir
- Her şeyi web dashboardda gerçek zamanlı gösterir

---

## Sistem Gereksinimleri

| Bileşen | Minimum | Önerilen |
|---------|---------|----------|
| İşletim Sistemi | Windows 10 x64 | Windows 11 |
| GPU | NVIDIA CUDA 12.x | RTX 4060+ |
| VRAM | 4 GB | 8 GB |
| RAM | 8 GB | 16 GB |
| Python | 3.10 | 3.10 / 3.11 |
| Node.js | 18+ | 20 LTS |

---

## Sıfırdan Kurulum (Yeni Bilgisayar)

### Adım 1 — Zorunlu Programları Kur

#### 1.1 NVIDIA Sürücüsü
nvidia.com → Drivers → kartını seç → indir ve kur.

Kurulumdan sonra PowerShell'de kontrol et:
```
nvidia-smi
```
`CUDA Version: 12.x` görünmeli. Düşükse sürücüyü güncelle.

#### 1.2 Python 3.10 veya 3.11
python.org/downloads adresinden indir.
Kurulum sırasında **"Add Python to PATH"** kutusunu işaretle.

Kontrol:
```
python --version
```

#### 1.3 Node.js 18+
nodejs.org adresinden LTS sürümü indir.

Kontrol:
```
node --version
```

#### 1.4 Docker Desktop
docker.com/products/docker-desktop adresinden indir.
Kur ve **başlat** (sistem tepsisinde yeşil ikon olmalı).

Kontrol:
```
docker --version
```

---

### Adım 2 — `.env` Dosyası Oluştur

Proje kökünde (`ParkGuard KZ/` içinde) `.env` dosyası oluştur:

```
CAMERA_1_URL=rtsp://admin:SİFRENİZ@192.168.1.64:554/Streaming/Channels/101
CAMERA_2_URL=rtsp://admin:SİFRENİZ@192.168.1.65:554/Streaming/Channels/101
CAMERA_3_URL=rtsp://admin:SİFRENİZ@192.168.1.66:554/Streaming/Channels/101
```

IP adreslerini ve şifreleri gerçek kamera bilgileriyle değiştir.
Kamera yoksa sistem yine çalışır — sadece video gelmez.

---

### Adım 3 — Python Sanal Ortam

`backend/` klasöründe PowerShell aç:

```bash
cd "yol\proje\backend"
python -m venv venv
venv\Scripts\activate
```

Satır başında `(venv)` görünmeli.

---

### Adım 4 — PyTorch CUDA Kur

```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

> ~3 GB indirir, 5–15 dakika sürer.

GPU kontrolü:
```bash
python -c "import torch; print(torch.cuda.is_available())"
```
`True` çıkmalı.

---

### Adım 5 — Diğer Bağımlılıkları Kur

```bash
pip install "ultralytics>=8.3.12" fastapi==0.110.0 "uvicorn[standard]==0.29.0"
pip install opencv-python-headless==4.9.0.80 shapely==2.0.3 redis==5.0.3
pip install numpy==1.26.4 "pydantic>=2.9.2" python-multipart==0.0.9
pip install psutil==5.9.8 python-dotenv==1.0.1
```

---

### Adım 6 — OCR Kütüphanelerini Kur

```bash
pip install paddlepaddle-gpu==2.6.1 paddleocr==2.7.3
pip install nomeroff-net==4.0.1
```

> ~500 MB indirir. nomeroff-net ilk çalıştırmada KZ plaka modellerini otomatik indirir.

---

### Adım 7 — YOLOv8n Modelini İndir

```bash
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"
mkdir models
move yolov8n.pt models\
```

`models/` zaten varsa veya dosya oradaysa hata çıkabilir — görmezden gel.

---

### Adım 8 — (Opsiyonel) TensorRT Export — 2–3x Hız

NVIDIA TensorRT 8.6 kurulu olmalı (developer.nvidia.com/tensorrt).
TensorRT yoksa `.pt` modeliyle çalışır — yavaş ama düzgün.

```bash
cd "yol\proje"
python scripts\export_trt.py
```

---

### Adım 9 — Redis Başlat

```bash
docker run -d -p 6379:6379 --name parkguard-redis redis:alpine
```

Sonraki seferlerde:
```bash
docker start parkguard-redis
```

---

### Adım 10 — Backend Başlat

```bash
cd "yol\proje\backend"
venv\Scripts\activate
python main.py
```

Başarılı çıktı:
```
nomeroff-net hazir (KZ plaka modeli aktif)
Inference loop baslatildi
Uvicorn running on http://0.0.0.0:8000
```

---

### Adım 11 — Frontend Başlat

**Yeni terminal** aç:

```bash
cd "yol\proje\frontend"
npm install
npm run dev
```

Tarayıcıda: **http://localhost:5173**

---

## Her Seferinde Çalıştırma

Kurulum bittikten sonra 3 terminalde sadece bunlar:

```bash
# Terminal 1 — Redis
docker start parkguard-redis

# Terminal 2 — Backend
cd backend
venv\Scripts\activate
python main.py

# Terminal 3 — Frontend
cd frontend
npm run dev
```

---

## Proje Yapısı

```
ParkGuard KZ/
├── .env                     # Kamera şifreleri (GİZLİ — git'e yükleme!)
├── .env.example             # Şablon .env oluşturmak için
├── docker-compose.yml       # Docker servisleri
├── backend/
│   ├── main.py              # Giriş noktası — FastAPI + inference döngüsü
│   ├── config.py            # Tüm sistem ayarları
│   ├── requirements.txt     # Python bağımlılıkları
│   ├── core/
│   │   ├── camera_manager.py   # RTSP kamera bağlantısı
│   │   ├── tracker.py          # YOLOv8 + ByteTrack
│   │   ├── zone_manager.py     # Yasak bölge yönetimi (Shapely)
│   │   ├── plate_ocr.py        # Plaka okuma (nomeroff-net / PaddleOCR)
│   │   ├── alarm_manager.py    # Alarm mantığı + SQLite
│   │   ├── log_buffer.py       # Dashboard için log tamponu
│   │   └── settings_manager.py # Kamera ayarları
│   ├── api/
│   │   ├── websocket.py        # Frame annotasyon + WebSocket
│   │   └── routes/             # HTTP API endpoint'leri
│   ├── models/              # YOLOv8 modeli (.pt veya .engine)
│   └── data/                # Alarm DB, ekran görüntüleri, zone ayarları
├── frontend/
│   └── src/
│       ├── components/      # React dashboard bileşenleri
│       ├── hooks/           # WebSocket hook'ları
│       ├── store/           # Zustand global state
│       └── i18n/            # Çeviriler (RU / KK)
└── scripts/
    ├── setup.bat            # Otomatik kurulum
    ├── export_trt.py        # TensorRT export
    ├── test_cameras.py      # Kamera bağlantı testi
    └── benchmark.py         # GPU performans testi
```

---

## Sorun Giderme

| Hata | Çözüm |
|------|-------|
| `torch.cuda.is_available()` → `False` | NVIDIA sürücüsünü güncelle, CUDA 12.x kur |
| `Redis baglanamadi` | `docker start parkguard-redis` çalıştır |
| Kameralar bağlanamıyor | `.env`'deki IP ve şifreyi kontrol et. `python scripts\test_cameras.py` çalıştır |
| Port 8000 kullanımda | `netstat -ano \| findstr :8000` → işlemi kapat |
| Frontend açılmıyor | Backend'in 8000'de çalıştığından emin ol |
| `FutureWarning` terminalde | Uyarı, hata değil — sistemi etkilemiyor |
| nomeroff-net ilk başlatmada yavaş | Internet gerekli — modeller otomatik indirilir (~500 MB) |

---

## Kamera Testi

Sistemi başlatmadan kamera bağlantısını test et:

```bash
cd backend
venv\Scripts\activate
python ..\scripts\test_cameras.py
```

---

## API

| Metot | Yol | Açıklama |
|-------|-----|----------|
| GET | `/api/alarms` | Alarm listesi (kamera, durum, plaka, tarih filtresi) |
| PUT | `/api/alarms/{id}/resolve` | Alarmı çözüldü işaretle |
| GET | `/api/alarms/{id}/screenshot` | Alarm fotoğrafı |
| DELETE | `/api/alarms/{id}` | Alarm sil |
| GET | `/api/zones` | Tüm yasak bölgeler |
| POST | `/api/zones` | Yeni bölge oluştur |
| PUT | `/api/zones/{id}` | Bölge güncelle |
| DELETE | `/api/zones/{id}` | Bölge sil |
| GET | `/api/stats/today` | Bugünün istatistikleri |
| GET | `/api/system/health` | GPU, CPU, RAM, kamera durumları |
| WS | `/ws/stream/{camera_id}` | Kamera video akışı (JPEG) |
| WS | `/ws/alarms` | Gerçek zamanlı alarmlar |
| WS | `/ws/stats` | FPS + sistem metrikleri |

---

## Alarm Mantığı

- Araç yasak bölgeye girer → timer başlar
- **5 dakika (300 saniye)** geçerse → alarm oluşturulur
- Aynı araç için **10 dakika cooldown** (spam önleme)
- Operatör "Çözüldü" butonuna basarsa alarm kapanır

---

## Önemli Notlar

- `.env` dosyasını asla GitHub'a yükleme (kamera şifresi içerir)
- Redis çalışmıyorsa sistem in-memory modda çalışır (alarmlar kaybolmaz)
- Kamera bağlanamıyorsa 20 deneme, her seferinde bekleme artar (5→10→20→40→60 sn)
- `FutureWarning` mesajları nomeroff-net'ten geliyor — hata değil

---

# 🇷🇺 РУССКИЙ

Система видеонаблюдения на базе ИИ для автоматического обнаружения нарушений парковки.
**YOLOv8 + ByteTrack + nomeroff-net + React Dashboard.**

---

## Что делает система?

- Подключается к IP-камерам Hikvision по RTSP
- Обнаруживает автомобили с помощью YOLOv8 (GPU)
- Отслеживает каждый автомобиль с уникальным ID (ByteTrack)
- Определяет: находится ли автомобиль в запрещённой зоне (Shapely)
- Считывает номерной знак (nomeroff-net — KZ модель)
- Если автомобиль стоит **более 5 минут** — создаёт тревогу
- Показывает всё в реальном времени на веб-дашборде

---

## Системные требования

| Компонент | Минимум | Рекомендуется |
|-----------|---------|---------------|
| ОС | Windows 10 x64 | Windows 11 |
| GPU | NVIDIA CUDA 12.x | RTX 4060+ |
| VRAM | 4 ГБ | 8 ГБ |
| RAM | 8 ГБ | 16 ГБ |
| Python | 3.10 | 3.10 / 3.11 |
| Node.js | 18+ | 20 LTS |

---

## Установка с нуля (новый компьютер)

### Шаг 1 — Установить обязательные программы

#### 1.1 Драйвер NVIDIA
Перейти на сайт nvidia.com → Drivers → выбрать свою видеокарту → скачать и установить.

После установки проверить в PowerShell:
```
nvidia-smi
```
Должна отобразиться строка `CUDA Version: 12.x`. Если версия ниже 12 — обновить драйвер.

#### 1.2 Python 3.10 или 3.11
Скачать с python.org/downloads.
**Важно:** при установке поставить галочку **"Add Python to PATH"**.

Проверка:
```
python --version
```

#### 1.3 Node.js 18+
Скачать LTS версию с nodejs.org.

Проверка:
```
node --version
```

#### 1.4 Docker Desktop
Скачать с docker.com/products/docker-desktop.
Установить и **запустить** (иконка в системном трее должна быть зелёной).

Проверка:
```
docker --version
```

---

### Шаг 2 — Создать файл `.env`

В корне проекта (папка `ParkGuard KZ/`) создать файл `.env` со следующим содержимым:

```
CAMERA_1_URL=rtsp://admin:ВАШ_ПАРОЛЬ@192.168.1.64:554/Streaming/Channels/101
CAMERA_2_URL=rtsp://admin:ВАШ_ПАРОЛЬ@192.168.1.65:554/Streaming/Channels/101
CAMERA_3_URL=rtsp://admin:ВАШ_ПАРОЛЬ@192.168.1.66:554/Streaming/Channels/101
```

Заменить IP-адреса и пароли на реальные данные камер.
Если камер нет — система всё равно запустится, дашборд будет работать.

---

### Шаг 3 — Создать виртуальное окружение Python

Открыть PowerShell в папке `backend/`:

```bash
cd "путь\к\проекту\backend"
python -m venv venv
venv\Scripts\activate
```

В начале строки должно появиться `(venv)`.

---

### Шаг 4 — Установить PyTorch с CUDA

```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

> Загрузка около 3 ГБ, занимает 5–15 минут.

Проверка GPU:
```bash
python -c "import torch; print(torch.cuda.is_available())"
```
Должно вывести `True`.

---

### Шаг 5 — Установить остальные зависимости

```bash
pip install "ultralytics>=8.3.12" fastapi==0.110.0 "uvicorn[standard]==0.29.0"
pip install opencv-python-headless==4.9.0.80 shapely==2.0.3 redis==5.0.3
pip install numpy==1.26.4 "pydantic>=2.9.2" python-multipart==0.0.9
pip install psutil==5.9.8 python-dotenv==1.0.1
```

---

### Шаг 6 — Установить OCR библиотеки

```bash
pip install paddlepaddle-gpu==2.6.1 paddleocr==2.7.3
pip install nomeroff-net==4.0.1
```

> Загрузка около 500 МБ. При первом запуске nomeroff-net автоматически скачает модели для казахстанских номеров.

---

### Шаг 7 — Скачать модель YOLOv8n

```bash
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"
mkdir models
move yolov8n.pt models\
```

Если папка `models/` уже существует или файл уже там — ошибки можно игнорировать.

---

### Шаг 8 — (Опционально) TensorRT — ускорение в 2–3 раза

Требуется установленный NVIDIA TensorRT 8.6 для CUDA 12.x.
Без TensorRT система работает на `.pt` модели — медленнее, но корректно.

```bash
cd "путь\к\проекту"
python scripts\export_trt.py
```

---

### Шаг 9 — Запустить Redis

```bash
docker run -d -p 6379:6379 --name parkguard-redis redis:alpine
```

Проверка:
```bash
docker ps
```
`parkguard-redis` должен отображаться со статусом `Up`.

---

### Шаг 10 — Запустить Backend

```bash
cd "путь\к\проекту\backend"
venv\Scripts\activate
python main.py
```

Успешный запуск:
```
nomeroff-net hazir (KZ plaka modeli aktif)
Inference loop baslatildi
Uvicorn running on http://0.0.0.0:8000
```

---

### Шаг 11 — Запустить Frontend

Открыть **новый** терминал:

```bash
cd "путь\к\проекту\frontend"
npm install
npm run dev
```

Открыть в браузере: **http://localhost:5173**

---

## Каждый раз при запуске

После первой установки достаточно выполнить в трёх терминалах:

```bash
# Терминал 1 — Redis
docker start parkguard-redis

# Терминал 2 — Backend
cd backend
venv\Scripts\activate
python main.py

# Терминал 3 — Frontend
cd frontend
npm run dev
```

---

## Структура проекта

```
ParkGuard KZ/
├── .env                     # Пароли камер (СЕКРЕТ — не загружать в git!)
├── .env.example             # Шаблон для создания .env
├── docker-compose.yml       # Docker сервисы
├── backend/
│   ├── main.py              # Точка входа — FastAPI + цикл инференса
│   ├── config.py            # Все настройки системы
│   ├── requirements.txt     # Зависимости Python
│   ├── core/
│   │   ├── camera_manager.py   # RTSP подключение к камерам
│   │   ├── tracker.py          # YOLOv8 + ByteTrack
│   │   ├── zone_manager.py     # Запрещённые зоны (Shapely)
│   │   ├── plate_ocr.py        # Распознавание номеров
│   │   ├── alarm_manager.py    # Логика тревог + SQLite
│   │   ├── log_buffer.py       # Буфер логов для дашборда
│   │   └── settings_manager.py # Настройки камер
│   ├── api/
│   │   ├── websocket.py        # WebSocket рассылка кадров
│   │   └── routes/             # HTTP API эндпоинты
│   ├── models/              # YOLOv8 модель (.pt или .engine)
│   └── data/                # БД, скриншоты, настройки зон
├── frontend/
│   └── src/
│       ├── components/      # React компоненты дашборда
│       ├── hooks/           # WebSocket хуки
│       ├── store/           # Zustand глобальное состояние
│       └── i18n/            # Переводы (RU / KK)
└── scripts/
    ├── setup.bat            # Автоматическая установка
    ├── export_trt.py        # TensorRT экспорт
    ├── test_cameras.py      # Тест подключения камер
    └── benchmark.py         # Тест производительности GPU
```

---

## Решение проблем

| Проблема | Решение |
|----------|---------|
| `torch.cuda.is_available()` → `False` | Обновить драйвер NVIDIA, проверить CUDA 12.x |
| `Redis baglanamadi` в логах | Выполнить `docker start parkguard-redis` |
| Камеры не подключаются | Проверить IP и пароль в `.env`. Запустить `python scripts\test_cameras.py` |
| Порт 8000 занят | `netstat -ano \| findstr :8000` → завершить процесс |
| Frontend не открывается | Убедиться что backend запущен на порту 8000 |
| `FutureWarning` в терминале | Предупреждение, не ошибка — на работу не влияет |
| `nomeroff-net` ошибка при первом запуске | Нужен интернет — модели скачиваются автоматически (~500 МБ) |

---

## Тест камер

Проверить подключение без запуска всей системы:

```bash
cd backend
venv\Scripts\activate
python ..\scripts\test_cameras.py
```

---

## API

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/alarms` | Список тревог (фильтры: камера, статус, номер, дата) |
| PUT | `/api/alarms/{id}/resolve` | Закрыть тревогу |
| GET | `/api/alarms/{id}/screenshot` | Фото тревоги |
| DELETE | `/api/alarms/{id}` | Удалить тревогу |
| GET | `/api/zones` | Все запрещённые зоны |
| POST | `/api/zones` | Создать зону |
| PUT | `/api/zones/{id}` | Обновить зону |
| DELETE | `/api/zones/{id}` | Удалить зону |
| GET | `/api/stats/today` | Статистика за сегодня |
| GET | `/api/system/health` | GPU, CPU, RAM, камеры |
| WS | `/ws/stream/{camera_id}` | Видеопоток камеры (JPEG) |
| WS | `/ws/alarms` | Тревоги в реальном времени |
| WS | `/ws/stats` | FPS + системные метрики |

---

## Логика тревог

- Автомобиль въезжает в запрещённую зону → запускается таймер
- Прошло **5 минут (300 секунд)** → создаётся тревога
- Для одного автомобиля **перезарядка 10 минут** (защита от дублей)
- Оператор нажимает "Решено" → тревога закрывается

---

## Важно

- Файл `.env` **никогда не загружать в git** — содержит пароли камер
- Если Redis недоступен — система работает в режиме in-memory (тревоги не теряются)
- При недоступности камеры — 20 попыток подключения с нарастающей задержкой (5→10→20→40→60 сек)
- `FutureWarning` от nomeroff-net — нормально, ошибкой не является
