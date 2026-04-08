import json
import shutil
import time
from pathlib import Path

import cv2
import numpy as np
import torch
from ultralytics import YOLO


REPO_DIR = Path(__file__).resolve().parents[1]
MODELS_DIR = REPO_DIR / "backend" / "models"
OUTPUT_DIR = REPO_DIR / "backend" / "artifacts" / "phase1_compare"
VIDEO_PATH = REPO_DIR / "videos" / "fixed.mp4"

CONF = 0.50
IOU = 0.45
CLASSES = [2, 5, 7]
TIMESTAMPS_SEC = [55, 72, 96]


def ensure_downloaded(weight_name: str, target_path: Path) -> Path:
    if target_path.exists():
        return target_path

    YOLO(weight_name)
    downloaded = Path(weight_name)
    if downloaded.exists():
        MODELS_DIR.mkdir(parents=True, exist_ok=True)
        shutil.move(str(downloaded), str(target_path))
        return target_path

    raise FileNotFoundError(f"{weight_name} indirilemedi")


def ensure_alias_copy(source: Path, alias: Path) -> Path:
    if alias.exists():
        return alias
    shutil.copy2(source, alias)
    return alias


def export_engine_if_missing(pt_path: Path, imgsz: int, batch: int = 1) -> Path:
    engine_path = pt_path.with_suffix(".engine")
    if engine_path.exists():
        return engine_path

    model = YOLO(str(pt_path))
    model.export(
        format="engine",
        device=0,
        half=True,
        batch=batch,
        imgsz=imgsz,
        workspace=6,
        simplify=True,
        dynamic=False,
    )
    if not engine_path.exists():
        raise FileNotFoundError(f"Engine olusmadi: {engine_path}")
    return engine_path


def extract_frame(video_path: Path, timestamp_sec: float) -> np.ndarray:
    cap = cv2.VideoCapture(str(video_path))
    cap.set(cv2.CAP_PROP_POS_MSEC, timestamp_sec * 1000)
    ok, frame = cap.read()
    cap.release()
    if not ok or frame is None:
        raise RuntimeError(f"Frame okunamadi: {timestamp_sec} sn")
    return frame


def run_benchmark(model_path: Path, imgsz: int, frames: list[np.ndarray]) -> dict:
    model = YOLO(str(model_path))

    warmup = [frames[0]]
    for _ in range(5):
        model(warmup, imgsz=imgsz, conf=CONF, iou=IOU, classes=CLASSES, verbose=False)
    if torch.cuda.is_available():
        torch.cuda.synchronize()

    times_ms: list[float] = []
    sample_results = []

    for idx, frame in enumerate(frames):
        start = time.perf_counter()
        results = model(
            frame,
            imgsz=imgsz,
            conf=CONF,
            iou=IOU,
            classes=CLASSES,
            verbose=False,
        )
        if torch.cuda.is_available():
            torch.cuda.synchronize()
        times_ms.append((time.perf_counter() - start) * 1000)

        result = results[0]
        boxes = result.boxes
        sample_results.append(
            {
                "frame_index": idx,
                "detections": int(len(boxes)),
                "boxes": [
                    {
                        "xyxy": [round(float(v), 1) for v in box.xyxy[0].cpu().tolist()],
                        "conf": round(float(box.conf[0]), 4),
                        "cls": int(box.cls[0]),
                    }
                    for box in boxes
                ],
            }
        )

    return {
        "model_path": str(model_path),
        "imgsz": imgsz,
        "avg_ms": round(sum(times_ms) / len(times_ms), 2),
        "min_ms": round(min(times_ms), 2),
        "max_ms": round(max(times_ms), 2),
        "fps_estimate": round(1000.0 / (sum(times_ms) / len(times_ms)), 2),
        "samples": sample_results,
        "model": model,
    }


def save_visuals(model_name: str, model: YOLO, imgsz: int, frames: list[np.ndarray]) -> list[str]:
    saved = []
    for idx, frame in enumerate(frames):
        results = model(
            frame,
            imgsz=imgsz,
            conf=CONF,
            iou=IOU,
            classes=CLASSES,
            verbose=False,
        )
        plotted = results[0].plot()
        out_path = OUTPUT_DIR / f"{model_name}_sample_{idx + 1}.jpg"
        cv2.imwrite(str(out_path), plotted)
        saved.append(str(out_path))
    return saved


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    base_pt = ensure_downloaded("yolov8s.pt", MODELS_DIR / "yolov8s.pt")
    seg_pt = ensure_downloaded("yolov8s-seg.pt", MODELS_DIR / "yolov8s-seg.pt")
    alias_1280_pt = ensure_alias_copy(base_pt, MODELS_DIR / "yolov8s_1280.pt")

    base_engine = export_engine_if_missing(base_pt, imgsz=960, batch=1)
    engine_1280 = export_engine_if_missing(alias_1280_pt, imgsz=1280, batch=1)
    seg_engine = export_engine_if_missing(seg_pt, imgsz=960, batch=1)

    frames = [extract_frame(VIDEO_PATH, ts) for ts in TIMESTAMPS_SEC]

    runs = {
        "yolov8s_960": {"path": base_engine, "imgsz": 960},
        "yolov8s_1280": {"path": engine_1280, "imgsz": 1280},
        "yolov8s_seg_960": {"path": seg_engine, "imgsz": 960},
    }

    report = {
        "video": str(VIDEO_PATH),
        "timestamps_sec": TIMESTAMPS_SEC,
        "results": {},
    }

    for name, cfg in runs.items():
        bench = run_benchmark(cfg["path"], cfg["imgsz"], frames)
        visuals = save_visuals(name, bench.pop("model"), cfg["imgsz"], frames)
        bench["visuals"] = visuals
        report["results"][name] = bench

    report_path = OUTPUT_DIR / "report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
