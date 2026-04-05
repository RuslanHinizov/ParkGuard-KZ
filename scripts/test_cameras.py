"""
test_cameras.py — Kamera Bağlantı Testi

Her kameraya bağlan, 5 frame al, FPS ölç.
RTSP URL'lerinin doğruluğunu ve ağ bağlantısını test eder.
"""

import sys
import os
import cv2
import time
from pathlib import Path

# Backend dizinini path'e ekle
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from config import CAMERAS, RTSP_BUFFER_SIZE, RTSP_MAX_DELAY


def test_single_camera(cam_config: dict) -> bool:
    """Tek kamera testi: bağlan, 5 frame al, FPS ölç."""

    cam_id = cam_config["id"]
    url = cam_config["url"]
    name = cam_config["name"]

    print(f"\n--- Kamera {cam_id}: {name} ---")
    print(f"  URL: {url}")

    os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = (
        f"rtsp_transport;tcp|"
        f"buffer_size;{RTSP_BUFFER_SIZE}|"
        f"max_delay;{RTSP_MAX_DELAY}|"
        f"fflags;nobuffer|"
        f"flags;low_delay"
    )

    cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    if not cap.isOpened():
        print(f"  HATA: Baglanamadi!")
        return False

    print(f"  Baglanti: OK")

    # 5 frame al ve süreyi ölç
    frame_count = 5
    start = time.time()
    frames_ok = 0

    for i in range(frame_count):
        ret, frame = cap.read()
        if ret:
            frames_ok += 1
            if i == 0:
                h, w = frame.shape[:2]
                print(f"  Cozunurluk: {w}x{h}")
        else:
            print(f"  Frame {i}: BASARISIZ")

    elapsed = time.time() - start
    fps = frames_ok / elapsed if elapsed > 0 else 0

    cap.release()

    print(f"  Frame: {frames_ok}/{frame_count} basarili")
    print(f"  FPS: {fps:.1f}")
    print(f"  Sonuc: {'BASARILI' if frames_ok == frame_count else 'KISMI BASARISIZ'}")

    return frames_ok == frame_count


def main():
    print("=" * 50)
    print("  ParkGuard KZ — Kamera Baglanti Testi")
    print("=" * 50)

    results = {}
    for cam in CAMERAS:
        success = test_single_camera(cam)
        results[cam["id"]] = success

    print("\n" + "=" * 50)
    print("  OZET")
    print("=" * 50)

    all_ok = True
    for cam_id, success in results.items():
        status = "OK" if success else "HATA"
        icon = "[+]" if success else "[-]"
        print(f"  {icon} Kamera {cam_id}: {status}")
        if not success:
            all_ok = False

    if all_ok:
        print("\n  Tum kameralar calisiyor!")
    else:
        print("\n  Bazi kameralarda sorun var!")
        print("  Kontrol et:")
        print("    1. Kamera IP adresleri dogru mu?")
        print("    2. Kullanici adi/sifre dogru mu?")
        print("    3. Kameralar ayni agda mi?")
        print("    4. RTSP portu (554) acik mi?")


if __name__ == "__main__":
    main()
