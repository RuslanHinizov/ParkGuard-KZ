# ParkGuard KZ / Korgen Vision - Production Yol Haritasi

Son guncelleme: 2026-04-08
Durum: `ACTIVE`

## 1. Amac

Bu dosya, projeyi demo seviyesinden production-grade, dusuk gecikmeli, yuksek FPS'li, stabil ve bakimi yapilabilir bir sisteme tasimak icin ana calisma belgesidir.

Hedef:

- Yerel agdaki IP kameralarla dusuk gecikmeli canli goruntu
- GPU decode + TensorRT inference
- Stabil detection/tracking/OCR/alarm zinciri
- Frontend tarafinda takilmayan, donmayan, akici video
- AI yukunden bagimsiz video/recording mimarisi
- Production icin olculebilir kabul kriterleri

Not:

- "Tam hatasiz" garanti edilmez.
- Hedef, production-grade stabilite, tekrar uretilebilirlik ve kolay debug edilebilirliktir.

## 2. Durum Etiketleri

- `[DONE]` tamamlandi ve temel dogrulamasi yapildi
- `[ACTIVE]` uzerinde aktif calisiliyor
- `[TODO]` sirada, henuz baslanmadi
- `[VERIFY]` implement edildi ama benchmark / saha testi bekliyor
- `[BLOCKED]` harici bagimlilik veya karar bekliyor
- `[DROP]` bu yoldan vazgecildi

Kurala bagli ilerleme:

- Bir is bittiginde etiketi `DONE` yap
- Tarih ekle
- Varsa kisa not dus

Ornek:

- `[DONE][2026-04-08] WebRTC ingest MVP tamamlandi`

## 3. Kuzey Yildizi Mimarisi

Hedef mimari:

```text
Kamera Main Stream
-> MediaMTX
-> WebRTC
-> Frontend <video>

Kamera Main Stream
-> Recorder (stream copy, no re-encode)

Kamera Sub Stream
-> FFmpeg + NVDEC
-> latest-frame ring buffer
-> Detector (TensorRT)
-> Tracker
-> Zone/Event Engine
-> Plate Detector
-> OCR Worker
-> Alarm/Penalty/Whitelist

Metadata
-> FastAPI/WebSocket
-> Frontend Canvas Overlay
```

Bu mimaride kritik kural:

- Video yolu ile AI yolu ayrilacak
- Backend artik video cizip JPEG basmayacak
- Frontend gercek videoyu MediaMTX/WebRTC tarafindan alacak
- Backend sadece metadata uretip yayinlayacak

## 4. Mevcut Durum Ozeti

Bu asamada bilinen mevcut durum:

- `[DONE][2026-04-07]` `fixed.mp4` ile tek kamera test modu calisiyor
- `[DONE][2026-04-07]` yerel video EOF durumunda reconnect yerine basa sarma davranisi eklendi
- `[DONE][2026-04-07]` yerel dosya kaynagi RTSP FFmpeg ayarlarindan ayrildi
- `[DONE][2026-04-07]` kamera basina ayri tracker kuruldu
- `[DONE][2026-04-07]` alarm tarafinda arac screenshot + plate crop birlikte kaydediliyor
- `[DONE][2026-04-07]` frontend alarm kartinda arac screenshot + plate crop birlikte gosteriliyor
- `[DONE][2026-04-07]` tek kamera test moduna uygun dinamik grid davranisi eklendi
- `[DONE][2026-04-08]` `yolov8s.pt/.onnx/.engine` uretildi ve aktif modele cekildi
- `[DONE][2026-04-08]` `imgsz=1280` benchmark edildi
- `[DONE][2026-04-08]` `yolov8s-seg` benchmark ve gorsel karsilastirma tamamlandi
- `[VERIFY][2026-04-08]` zone ROI + padding detect akisi eklendi
- `[VERIFY][2026-04-08]` ozel ByteTrack threshold profili eklendi
- `[VERIFY][2026-04-07]` alarm ve penalty akisi loglarda calisiyor

Bilinen aktif problemler:

- `[ACTIVE]` `yolov8s` tabani `yolov8n`den daha iyi ama yakin/ust uste araclarda halen merge riski var
- `[VERIFY][2026-04-08]` OCR track-bazli voting ve sticky result ile daha kararlı hale getirildi
- `[DONE][2026-04-08]` server-side JPEG websocket stream ana player akisindan cikarildi; metadata WS + gercek video source ayrimi kuruldu
- `[ACTIVE]` frontend halen Vite dev + websocket proxy ile calisiyor; production serve ayri fazda tamamlanacak

## 5. Hedef Kabul Kriterleri

Production kabul kriterleri:

- Canli video local agda kullanici tarafinda akici olmali
- Goruntu AI yukunden bagimsiz olmali
- Frontend tarafinda 2 saat soak testte freeze olmamali
- Kamera reconnect durumunda sistem recover etmeli
- Ayni plaka icin OCR sonucu track bazli tutarli olmali
- Alarm zinciri deterministic olmali
- Whitelist davranisi izlenebilir ve debug edilebilir olmali
- Bellek ve kaynak kullanimi sinirli ve olculebilir olmali

Hedef metrikler:

- `video latency`: local agda algilanan gecikme olabildigince dusuk, hedef `<300ms`
- `AI metadata rate`: 1 kamera icin hedef `10-20 Hz`
- `OCR stability`: ayni track icin finalize edilen plaka ciktisi kararlı olmali
- `memory growth`: uzun kosuda kontrolsuz buyume olmamali

## 6. Faz Bazli Uygulama Plani

### Faz 0 - Baseline ve Olcum

Amac:

- Mevcut sistemi olcmek
- Hangi degisiklikten ne kazanildigini gorebilmek

Isler:

- `[TODO]` Benchmark profili tanimla
- `[TODO]` 1 kamera / 3 kamera FPS olcumu al
- `[TODO]` CPU, GPU, VRAM, OCR latency loglarini standardize et
- `[TODO]` Mevcut false positive / false merge / OCR varyasyon orneklerini dataset klasorune kaydet

Dosyalar:

- [backend/main.py](/C:/Users/rusla/Desktop/Project-university/ParkGuard%20KZ/backend/main.py)
- [backend/api/routes/stream.py](/C:/Users/rusla/Desktop/Project-university/ParkGuard%20KZ/backend/api/routes/stream.py)
- [backend/api/websocket.py](/C:/Users/rusla/Desktop/Project-university/ParkGuard%20KZ/backend/api/websocket.py)

Kabul:

- 3 farkli test senaryosu icin tekrar uretilebilir benchmark raporu cikacak

### Faz 1 - Detection Stabilizasyonu

Amac:

- Yanlis merge
- Yanlis class
- dusuk recall

Isler:

- `[DONE][2026-04-08]` `yolov8n -> yolov8s.engine`
- `[DONE][2026-04-08]` `vehicle-only` mantigina gec
- `[DONE][2026-04-08]` `imgsz=960` yap
- `[DONE][2026-04-08]` `imgsz=1280` benchmark et
- `[VERIFY][2026-04-08]` `zone ROI + padding` detect akisini kur
- `[VERIFY][2026-04-08]` ByteTrack esiklerini sahneye gore tune et
- `[DONE][2026-04-08]` `yolov8s-seg` karsilastir
- `[TODO]` gerekirse `yolov8m-seg` karsilastir

Faz 1 benchmark sonucu:

- `yolov8s.engine @960`: `11.74 ms`, tahmini `85.19 FPS`, ornek detection sayilari `22 / 19 / 18`
- `yolov8s_1280.engine @1280`: `17.35 ms`, tahmini `57.63 FPS`, ornek detection sayilari `23 / 24 / 20`
- `yolov8s-seg.engine @960`: `16.30 ms`, tahmini `61.35 FPS`, ornek detection sayilari `23 / 18 / 19`
- Sonuc: `1280`, `960`a gore kucuk arac recall'ini artiriyor ve maliyeti kabul edilebilir seviyede tutuyor.
- Sonuc: `yolov8s-seg`, mask avantajina ragmen bu sahnede `1280 detect` kadar net bir kazanc vermiyor.
- Karar: Faz 1 icin once `yolov8s + ROI + 1280 benchmark sonucu` uzerinden ilerle; `seg` ancak merge problemi devam ederse ikinci adim olsun.

Baslangic ayarlari:

- `track_high_thresh`: `0.35-0.45`
- `new_track_thresh`: `0.25-0.35`
- `match_thresh`: `0.75-0.85`

Dosyalar:

- [backend/config.py](/C:/Users/rusla/Desktop/Project-university/ParkGuard%20KZ/backend/config.py)
- [backend/core/tracker.py](/C:/Users/rusla/Desktop/Project-university/ParkGuard%20KZ/backend/core/tracker.py)
- [backend/export_engine.py](/C:/Users/rusla/Desktop/Project-university/ParkGuard%20KZ/backend/export_engine.py)

Kabul:

- Iki araci tek bbox alma orani anlamli sekilde duser
- `truck/car` etiketi alarm mantigini etkilemez

### Faz 2 - OCR Yeniden Tasarimi

Amac:

- OCR'yi tek-frame ve generic crop mantigindan cikarmak

Yeni akıs:

`vehicle detect -> plate detect -> plate OCR -> track-level voting -> regex normalization -> whitelist/fuzzy correction`

Isler:

- `[TODO]` ayrik plate detector ekle
- `[DONE][2026-04-08]` plate bbox uzerinden OCR calistir
- `[DONE][2026-04-08]` `track_id` bazli `5-10 frame` voting ekle
- `[DONE][2026-04-08]` KZ plate regex normalization ekle
- `[DONE][2026-04-08]` minimum plate crop boyut eşiği koy
- `[DONE][2026-04-08]` dusuk kalite OCR sonucunun iyi sonucu overwrite etmesini engelle
- `[DONE][2026-04-08]` whitelist/history tabanli conservative fuzzy correction ekle
- `[DONE][2026-04-08]` en iyi crop secim mantigini yaz

- `[DONE][2026-04-08]` ground-truth CSV ile exact accuracy / char accuracy / confusion raporu ureten OCR evaluation script'i eklendi

En iyi crop olcutleri:

- en yuksek confidence
- en buyuk plate area
- en net frame

Dosyalar:

- [backend/core/plate_ocr.py](/C:/Users/rusla/Desktop/Project-university/ParkGuard%20KZ/backend/core/plate_ocr.py)
- [backend/core/alarm_manager.py](/C:/Users/rusla/Desktop/Project-university/ParkGuard%20KZ/backend/core/alarm_manager.py)
- [backend/api/routes/alarms.py](/C:/Users/rusla/Desktop/Project-university/ParkGuard%20KZ/backend/api/routes/alarms.py)
- [frontend/src/components/PlateCard.tsx](/C:/Users/rusla/Desktop/Project-university/ParkGuard%20KZ/frontend/src/components/PlateCard.tsx)

Kabul:

- Ayni track icin finalize edilen plaka kararlı olmali
- Plate crop kalitesi gozle gorulur bicimde iyilesmeli

Faz 2 sonuc notu:

- `fixed.mp4` testinde yeni alarm `348AKB13` olarak finalize edildi
- alarm API sonucu: `plate_conf=0.995`, `plate=348AKB13`
- OCR artik tek-frame cache degil, track-level aggregate sonuc uzerinden alarm uretiyor

### Faz 3 - Stream Mimarisi Refactor

Amac:

- Annotated JPEG websocket stream'i production disina cikarmak

Yeni akıs:

- `MediaMTX` -> `WebRTC` -> frontend video
- backend -> metadata websocket

Isler:

- `[DONE][2026-04-08]` MediaMTX konfigunu production akisina gore MVP seviyesinde netlestir
- `[DONE][2026-04-08]` frontend'e `file / WebRTC / HLS` source negotiation player ekle
- `[DONE][2026-04-08]` mevcut `useStream.ts` mantigini source-based player olarak yeniden yaz
- `[DONE][2026-04-08]` frontend overlay cizimini SVG tabanli olarak kur
- `[DONE][2026-04-08]` metadata formatini standardize et
- `[DONE][2026-04-08]` metadata `timestamp_ms` alanini wall-clock tabanli hale getir
- `[VERIFY][2026-04-08]` RTSP + MediaMTX + WHEP/WebRTC saha testi
- `[VERIFY][2026-04-08]` browser tarafinda HLS fallback davranisi

Dosyalar:

- [backend/api/websocket.py](/C:/Users/rusla/Desktop/Project-university/ParkGuard%20KZ/backend/api/websocket.py)
- [backend/api/routes/stream.py](/C:/Users/rusla/Desktop/Project-university/ParkGuard%20KZ/backend/api/routes/stream.py)
- [frontend/src/hooks/useStream.ts](/C:/Users/rusla/Desktop/Project-university/ParkGuard%20KZ/frontend/src/hooks/useStream.ts)
- [frontend/src/components/VideoPlayer.tsx](/C:/Users/rusla/Desktop/Project-university/ParkGuard%20KZ/frontend/src/components/VideoPlayer.tsx)
- [frontend/src/components/VideoGrid.tsx](/C:/Users/rusla/Desktop/Project-university/ParkGuard%20KZ/frontend/src/components/VideoGrid.tsx)

Kabul:

- Frontend video AI yukunden bagimsiz akmali
- Lokal agda hissedilen gecikme belirgin sekilde dusmeli

Faz 3 sonuc notu:

- `GET /api/stream/source/1` Phase 3 source negotiation endpointi calisiyor
- `GET /api/stream/dev-file/1` test video kaynagi dogrulandi
- `WS /ws/metadata/1` metadata yayini dogrulandi
- Frontend ana player artik backend JPEG stream yerine gercek video source + metadata overlay kullanacak sekilde calisiyor
- Bu asamada `file` modu runtime test edildi
- RTSP + MediaMTX + WHEP/WebRTC zinciri kodlandi ancak saha dogrulamasi ayrica yapilacak

### Faz 4 - Process Ayrimi

Amac:

- Capture/decode, inference, OCR ve API katmanlarini ayirmak

Yeni servisler:

- `media-service`
- `record-service`
- `ai-worker`
- `ocr-worker`
- `event-service`
- `api-service`

Isler:

- `[TODO]` `camera_manager` monolith yapisini parcalamak
- `[TODO]` `latest-frame ring buffer` mantigini netlestirmek
- `[TODO]` OCR'yi ayri event-based worker yapmak
- `[TODO]` servisler arasi metadata tasima katmani eklemek

Yeni dosya onerileri:

- `backend/core/media_ingest.py`
- `backend/core/detection_worker.py`
- `backend/core/ocr_worker.py`
- `backend/core/event_engine.py`

Kabul:

- Bir katmandaki yavaslama tum sistemi bloklamamali

### Faz 5 - Recording ve Production Deployment

Amac:

- Kayit akisini AI'dan tamamen ayirmak
- Vite dev bagimliligini bitirmek

Isler:

- `[TODO]` main stream icin stream-copy recording ekle
- `[TODO]` segmentleme/rotation stratejisi belirle
- `[TODO]` frontend'i `build + nginx` ile calistir
- `[TODO]` production config/env profilleri ayir
- `[TODO]` servis start/stop scriptlerini duzenle

Dosyalar:

- [docker-compose.yml](/C:/Users/rusla/Desktop/Project-university/ParkGuard%20KZ/docker-compose.yml)
- [mediamtx/mediamtx.yml](/C:/Users/rusla/Desktop/Project-university/ParkGuard%20KZ/mediamtx/mediamtx.yml)
- [frontend/vite.config.ts](/C:/Users/rusla/Desktop/Project-university/ParkGuard%20KZ/frontend/vite.config.ts)

Kabul:

- Kayıt akisi AI'dan etkilenmeden surekli devam etmeli

### Faz 6 - Data ve Fine-Tune

Amac:

- Genel COCO + generic OCR sinirlarindan cikmak

Isler:

- `[TODO]` sahadan veri topla
- `[TODO]` false merge / false class / zor OCR orneklerini etiketle
- `[TODO]` custom vehicle detector fine-tune et
- `[TODO]` custom plate detector fine-tune et
- `[TODO]` benchmark ile once/sonra farkini olc

Kabul:

- Kamera acina ozel accuracy artisı net sekilde olculmeli

## 7. Windows Production Karari

Bu proje Windows ortaminda gidecek.

Karar:

- `[DONE][2026-04-08]` `Linux/DeepStream` su an icin hedef disi
- `[ACTIVE]` Windows icin en iyi pratik mimari:
  - `MediaMTX`
  - `WebRTC`
  - `FFmpeg + NVDEC`
  - `TensorRT`
  - `FastAPI + WebSocket metadata`

Bu nedenle:

- `OpenCV VideoCapture` production decode katmani olmayacak
- server-side annotated JPEG stream kademeli olarak kaldirilacak
- frontend video katmani MediaMTX/WebRTC uzerinden beslenecek

## 8. Kamera ve Ag Standarti

AI stream:

- `H.264`
- `1920x1080`
- `15-20 fps`
- `4096-8192 Kbps`
- `H.264+ OFF`
- `Sub Stream`

View/record stream:

- `2560x1440`
- `25/30 fps`
- `H.264`
- `H.264+ OFF`
- `Main Stream`

Ag:

- `[TODO]` kameralar ve AI sunucusu ayni local VLAN/bridge icinde olacak
- `[TODO]` router CPU path'ten kacilacak
- `[TODO]` mumkunse dedicated camera VLAN kullanilacak
- `[TODO]` Wi-Fi kullanilmayacak

## 9. Risk Kaydi

- `[ACTIVE]` `yolov8n` ile devam edilirse accuracy limiti hizli asilamaz
- `[ACTIVE]` OCR generic kalirsa stabilite sorunu surer
- `[ACTIVE]` websocket JPEG kaldikca production latency tavani yuksek kalir
- `[ACTIVE]` Vite dev/proxy ile prod davranisi dogru olculmez

## 10. Bugunden Sonra Is Kurali

Bu dosya artik ana ilerleme kaydi olarak kullanilacak.

Her faz icin:

- baslamadan once etiketi `ACTIVE` yap
- bitirince `DONE` yap
- tarih ekle
- kisa sonuc notu dus

## 11. Simdi Baslanacak Ilk Isler

- `[DONE][2026-04-08]` Faz 1 / `yolov8s.engine + imgsz=960 + vehicle-only`
- `[VERIFY][2026-04-08]` Faz 1 / zone ROI detect
- `[DONE][2026-04-08]` Faz 1 / `imgsz=1280` varsayilan entegrasyon testi
- `[TODO]` Faz 2 / ayrik plate detector (yalniz accuracy daha da gerekirse)
- `[DONE][2026-04-08]` Faz 3 / source-based video + metadata overlay MVP
- `[ACTIVE]` Faz 3 / RTSP + MediaMTX + WHEP saha dogrulamasi

## 12. Beklenen Nihai Sonuc

Bu plan tamamlandiginda hedeflenen sistem:

- goruntu tarafinda akici
- detection tarafinda daha kararlı
- OCR tarafinda daha tutarlı
- alarm zincirinde deterministik
- recording tarafinda guvenilir
- production ortaminda izlenebilir ve bakimi kolay
