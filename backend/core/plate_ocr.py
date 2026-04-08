import logging
import re
import sqlite3
import time
from collections import defaultdict, deque

import cv2
import numpy as np

from config import (
    DB_PATH,
    OCR_CONF_THRESHOLD,
    OCR_HISTORY_SIZE,
    OCR_MAX_QUEUE,
    OCR_MIN_PLATE_AREA,
    OCR_MIN_PLATE_HEIGHT,
    OCR_MIN_PLATE_WIDTH,
    OCR_MIN_STABLE_VOTES,
    OCR_REPLACE_MARGIN,
    OCR_STICKY_CONFIDENCE,
)

logger = logging.getLogger(__name__)

KZ_PLATE_RE = re.compile(r"^\d{3}[A-Z]{3}\d{2}$")
ALNUM_RE = re.compile(r"[^A-Z0-9А-ЯЁІҮҰҚӨҺ]")

CYRILLIC_TO_LATIN = {
    "А": "A",
    "В": "B",
    "С": "C",
    "Е": "E",
    "Н": "H",
    "І": "I",
    "К": "K",
    "М": "M",
    "О": "O",
    "Р": "P",
    "Т": "T",
    "У": "Y",
    "Х": "X",
    "Ё": "E",
}

LETTER_TO_DIGIT = {
    "O": "0",
    "Q": "0",
    "D": "0",
    "I": "1",
    "L": "1",
    "Z": "2",
    "S": "5",
    "G": "6",
    "T": "7",
    "B": "8",
}

DIGIT_TO_LETTER = {
    "0": "O",
    "1": "I",
    "2": "Z",
    "4": "A",
    "5": "S",
    "6": "G",
    "7": "T",
    "8": "B",
}


class PlateOCR:
    def __init__(self):
        logger.info("nomeroff-net baslatiliyor...")
        try:
            from nomeroff_net import pipeline
            from nomeroff_net.tools import unzip

            self._pipeline = pipeline("number_plate_detection_and_reading")
            self._unzip = unzip
            self._backend = "nomeroff"
            logger.info("nomeroff-net hazir (KZ plaka modeli aktif)")
        except Exception as e:
            logger.warning(f"nomeroff-net baslatma hatasi: {e} - PaddleOCR'a geciliyor")
            self._pipeline = None
            self._backend = "paddle"
            self._init_paddle_fallback()

        self.results: dict[int, dict] = {}
        self._known_plates_cache: set[str] = set()
        self._known_plates_loaded_at = 0.0

    def _init_paddle_fallback(self) -> None:
        try:
            from paddleocr import PaddleOCR

            self._paddle = PaddleOCR(
                use_angle_cls=True,
                lang="en",
                use_gpu=True,
                gpu_mem=500,
                show_log=False,
            )
            logger.info("PaddleOCR yedek olarak baslatildi")
        except Exception as e:
            logger.error(f"PaddleOCR da baslanamadi: {e}")
            self._paddle = None

    def read_plate(self, vehicle_frame: np.ndarray, bbox: list[int]) -> dict | None:
        if self._backend == "nomeroff":
            return self._read_nomeroff(vehicle_frame, bbox)
        return self._read_paddle(vehicle_frame, bbox)

    def _read_nomeroff(self, vehicle_frame: np.ndarray, bbox: list[int]) -> dict | None:
        try:
            h, w = vehicle_frame.shape[:2]
            x1 = max(0, bbox[0])
            y1 = max(0, bbox[1])
            x2 = min(w, bbox[2])
            y2 = min(h, bbox[3])

            vehicle_crop = vehicle_frame[y1:y2, x1:x2]
            if vehicle_crop.size == 0:
                return None

            payload = self._extract_nomeroff_outputs(self._unzip(self._pipeline([vehicle_crop])))
            texts = payload["texts"]
            confidences = payload["confidences"]
            points = payload["points"]
            zones = payload["zones"]

            raw_texts = texts if isinstance(texts, list) else [texts] if isinstance(texts, str) else []
            candidates = []
            for idx, text in enumerate(raw_texts):
                conf = self._extract_confidence(confidences, idx)
                if conf < OCR_CONF_THRESHOLD:
                    continue

                plate_points = points[idx] if idx < len(points) else None
                plate_bbox = self._points_to_bbox(plate_points)
                plate_crop = zones[idx] if idx < len(zones) else None
                candidate = self._build_candidate(
                    raw_text=text,
                    confidence=conf,
                    plate_bbox=plate_bbox,
                    plate_points=plate_points,
                    plate_crop=plate_crop,
                )
                if candidate:
                    candidates.append(candidate)

            if not candidates:
                return None

            return max(candidates, key=self._plate_rank)

        except Exception as e:
            logger.error(f"nomeroff-net OCR hatasi: {e}")
            return None

    def _read_paddle(self, vehicle_frame: np.ndarray, bbox: list[int]) -> dict | None:
        if not self._paddle:
            return None

        try:
            h, w = vehicle_frame.shape[:2]
            x1, y1 = max(0, bbox[0]), max(0, bbox[1])
            x2, y2 = min(w, bbox[2]), min(h, bbox[3])
            vehicle_crop = vehicle_frame[y1:y2, x1:x2]
            if vehicle_crop.size == 0:
                return None

            result = self._paddle.ocr(vehicle_crop, cls=True)
            if not result or not result[0]:
                return None

            best_text, best_conf = "", 0.0
            for line in result[0]:
                text, conf = line[1]
                if conf > best_conf:
                    best_conf, best_text = conf, text

            if best_conf < max(0.70, OCR_CONF_THRESHOLD):
                return None

            plate_crop = self._fallback_plate_crop(vehicle_crop)
            return self._build_candidate(
                raw_text=best_text,
                confidence=round(float(best_conf), 3),
                plate_bbox=None,
                plate_points=None,
                plate_crop=plate_crop,
            )

        except Exception as e:
            logger.error(f"PaddleOCR hatasi: {e}")
            return None

    def _extract_nomeroff_outputs(self, payload) -> dict:
        texts = []
        confidences = []
        points = []
        zones = []

        if isinstance(payload, dict):
            texts = payload.get("texts") or payload.get("text") or []
            confidences = payload.get("confidences") or payload.get("scores") or []
            points = payload.get("points") or payload.get("keypoints") or []
            zones = payload.get("zones") or payload.get("images_zones") or []
            return {
                "texts": self._unwrap_single_image(texts),
                "confidences": self._unwrap_single_image(confidences),
                "points": self._unwrap_single_image(points),
                "zones": self._unwrap_single_image(zones),
            }

        if isinstance(payload, (list, tuple)) and len(payload) >= 9:
            points = payload[2] or []
            zones = payload[3] or []
            confidences = payload[7] or []
            texts = payload[8] or []
        elif isinstance(payload, (list, tuple)) and len(payload) == 1:
            texts = payload[0] or []

        return {
            "texts": self._unwrap_single_image(texts),
            "confidences": self._unwrap_single_image(confidences),
            "points": self._unwrap_single_image(points),
            "zones": self._unwrap_single_image(zones),
        }

    def _unwrap_single_image(self, value):
        if isinstance(value, tuple):
            value = list(value)
        if isinstance(value, list) and len(value) == 1:
            return value[0]
        return value or []

    def _extract_confidence(self, confidences, idx: int) -> float:
        conf = 0.0
        if isinstance(confidences, list) and idx < len(confidences):
            numeric = self._flatten_numeric(confidences[idx])
            if numeric:
                conf = float(sum(numeric) / len(numeric))
        if conf <= 0.0:
            conf = 0.90
        return round(conf, 3)

    def _flatten_numeric(self, value) -> list[float]:
        if isinstance(value, (int, float)):
            return [float(value)]
        if isinstance(value, (list, tuple)):
            nums: list[float] = []
            for item in value:
                nums.extend(self._flatten_numeric(item))
            return nums
        return []

    def _build_candidate(
        self,
        raw_text: str,
        confidence: float,
        plate_bbox: list[int] | None,
        plate_points,
        plate_crop,
    ) -> dict | None:
        normalized_text = self._normalize_plate_text(raw_text)
        if not normalized_text:
            return None

        plate_crop = self._normalize_plate_crop(plate_crop)
        width, height = self._resolve_plate_size(plate_bbox, plate_crop)
        plate_area = width * height
        if width < OCR_MIN_PLATE_WIDTH or height < OCR_MIN_PLATE_HEIGHT or plate_area < OCR_MIN_PLATE_AREA:
            return None

        sharpness = self._estimate_sharpness(plate_crop)
        quality = self._estimate_quality(width, height, sharpness)
        score = round((confidence * 0.68) + (quality * 0.32), 4)

        return {
            "text": normalized_text,
            "raw_text": (raw_text or "").upper().strip(),
            "confidence": round(float(confidence), 3),
            "score": score,
            "quality": quality,
            "sharpness": round(sharpness, 2),
            "plate_bbox": list(plate_bbox) if plate_bbox else None,
            "plate_points": self._clone_points(plate_points),
            "plate_crop": plate_crop,
            "plate_width": width,
            "plate_height": height,
            "plate_area": plate_area,
            "votes": 1,
            "stable": False,
            "updated_at": time.time(),
        }

    def _normalize_plate_text(self, text: str | None) -> str | None:
        if not text:
            return None

        cleaned = ALNUM_RE.sub("", text.upper().strip())
        if len(cleaned) < 8:
            return None

        cleaned = "".join(CYRILLIC_TO_LATIN.get(ch, ch) for ch in cleaned)

        candidates: list[tuple[float, str]] = []
        for start in range(0, len(cleaned) - 7):
            segment = cleaned[start:start + 8]
            normalized, fitness = self._normalize_kz_segment(segment)
            if normalized:
                candidates.append((fitness, normalized))

        if not candidates:
            return None

        candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
        return candidates[0][1]

    def _normalize_kz_segment(self, segment: str) -> tuple[str | None, float]:
        if len(segment) != 8:
            return None, -1.0

        out: list[str] = []
        fitness = 0.0

        for ch in segment[:3]:
            digit, fit = self._to_digit(ch)
            if not digit:
                return None, -1.0
            out.append(digit)
            fitness += fit

        for ch in segment[3:6]:
            letter, fit = self._to_letter(ch)
            if not letter:
                return None, -1.0
            out.append(letter)
            fitness += fit

        for ch in segment[6:8]:
            digit, fit = self._to_digit(ch)
            if not digit:
                return None, -1.0
            out.append(digit)
            fitness += fit

        candidate = "".join(out)
        if not KZ_PLATE_RE.match(candidate):
            return None, -1.0

        substitutions = sum(1 for src, dst in zip(segment, candidate) if src != dst)
        return candidate, fitness - (substitutions * 0.15)

    def _to_digit(self, ch: str) -> tuple[str | None, float]:
        if ch.isdigit():
            return ch, 1.0
        ch = CYRILLIC_TO_LATIN.get(ch, ch)
        mapped = LETTER_TO_DIGIT.get(ch)
        if mapped:
            return mapped, 0.55
        return None, 0.0

    def _to_letter(self, ch: str) -> tuple[str | None, float]:
        ch = CYRILLIC_TO_LATIN.get(ch, ch)
        if "A" <= ch <= "Z":
            return ch, 1.0
        mapped = DIGIT_TO_LETTER.get(ch)
        if mapped:
            return mapped, 0.55
        return None, 0.0

    def _normalize_plate_crop(self, plate_crop) -> np.ndarray | None:
        if isinstance(plate_crop, np.ndarray):
            if plate_crop.size == 0:
                return None
            return plate_crop.copy()
        return None

    def _resolve_plate_size(
        self,
        plate_bbox: list[int] | None,
        plate_crop: np.ndarray | None,
    ) -> tuple[int, int]:
        if isinstance(plate_crop, np.ndarray) and plate_crop.size > 0:
            h, w = plate_crop.shape[:2]
            return int(w), int(h)
        if plate_bbox and len(plate_bbox) == 4:
            return max(0, int(plate_bbox[2] - plate_bbox[0])), max(0, int(plate_bbox[3] - plate_bbox[1]))
        return 0, 0

    def _estimate_sharpness(self, plate_crop: np.ndarray | None) -> float:
        if not isinstance(plate_crop, np.ndarray) or plate_crop.size == 0:
            return 0.0
        gray = cv2.cvtColor(plate_crop, cv2.COLOR_BGR2GRAY) if plate_crop.ndim == 3 else plate_crop
        return float(cv2.Laplacian(gray, cv2.CV_64F).var())

    def _estimate_quality(self, width: int, height: int, sharpness: float) -> float:
        if width <= 0 or height <= 0:
            return 0.0
        area_norm = min(1.0, (width * height) / 7000.0)
        sharpness_norm = min(1.0, sharpness / 350.0)
        aspect = width / max(height, 1)
        if 2.4 <= aspect <= 6.4:
            aspect_score = 1.0
        elif 1.9 <= aspect <= 7.0:
            aspect_score = 0.6
        else:
            aspect_score = 0.2
        return round((area_norm * 0.45) + (sharpness_norm * 0.35) + (aspect_score * 0.20), 4)

    def _fallback_plate_crop(self, vehicle_crop: np.ndarray) -> np.ndarray | None:
        if vehicle_crop.size == 0:
            return None
        h, w = vehicle_crop.shape[:2]
        y1 = int(h * 0.45)
        y2 = int(h * 0.82)
        x1 = int(w * 0.18)
        x2 = int(w * 0.88)
        fallback = vehicle_crop[y1:y2, x1:x2]
        return fallback.copy() if fallback.size > 0 else None

    def _points_to_bbox(self, points) -> list[int] | None:
        if points is None:
            return None
        arr = np.asarray(points)
        if arr.size == 0 or arr.ndim != 2 or arr.shape[1] < 2:
            return None
        x1 = int(np.min(arr[:, 0]))
        y1 = int(np.min(arr[:, 1]))
        x2 = int(np.max(arr[:, 0]))
        y2 = int(np.max(arr[:, 1]))
        return [x1, y1, x2, y2]

    def _clone_points(self, points):
        if points is None:
            return None
        arr = np.asarray(points)
        return arr.tolist() if arr.size else None

    def get_cached(self, track_id: int) -> dict | None:
        state = self.results.get(track_id)
        if not state:
            return None
        return state.get("best")

    def cache_result(self, track_id: int, result: dict) -> dict | None:
        state = self.results.get(track_id)
        if state is None:
            state = {
                "history": deque(maxlen=OCR_HISTORY_SIZE),
                "best": None,
                "updated_at": time.time(),
            }
            self.results[track_id] = state

        state["history"].append(self._clone_result(result))
        state["updated_at"] = time.time()
        state["best"] = self._build_stable_result(list(state["history"]), state.get("best"))

        while len(self.results) > OCR_MAX_QUEUE:
            oldest_track_id = min(
                self.results.items(),
                key=lambda item: item[1].get("updated_at", 0.0),
            )[0]
            self.results.pop(oldest_track_id, None)

        return state["best"]

    def clear_track(self, track_id: int) -> None:
        self.results.pop(track_id, None)

    def _build_stable_result(self, history: list[dict], current_best: dict | None) -> dict | None:
        if not history:
            return current_best

        candidate_text = self._aggregate_plate_text(history)
        if candidate_text:
            matching = [obs for obs in history if obs["text"] == candidate_text]
            if not matching:
                distances = [self._hamming_distance(obs["text"], candidate_text) for obs in history]
                min_distance = min(distances) if distances else 99
                matching = [
                    obs for obs in history
                    if self._hamming_distance(obs["text"], candidate_text) == min_distance
                ]
        else:
            matching = history
            candidate_text = max(history, key=self._plate_rank)["text"]

        visual_source = max(matching, key=self._plate_rank)
        total_weight = sum(max(obs["score"], 0.01) for obs in matching)
        weighted_conf = sum(obs["confidence"] * max(obs["score"], 0.01) for obs in matching) / total_weight
        weighted_quality = sum(obs["quality"] * max(obs["score"], 0.01) for obs in matching) / total_weight
        weighted_sharpness = sum(obs["sharpness"] * max(obs["score"], 0.01) for obs in matching) / total_weight
        avg_score = sum(obs["score"] for obs in matching) / len(matching)
        votes = max(1, len(matching))
        stable = votes >= OCR_MIN_STABLE_VOTES or weighted_conf >= OCR_STICKY_CONFIDENCE
        candidate_text = self._apply_known_plate_correction(candidate_text, weighted_conf, votes)

        candidate = self._clone_result(visual_source)
        candidate.update(
            {
                "text": candidate_text,
                "confidence": round(float(weighted_conf), 3),
                "quality": round(float(weighted_quality), 4),
                "sharpness": round(float(weighted_sharpness), 2),
                "score": round(float(avg_score + min(0.12, 0.03 * max(votes - 1, 0))), 4),
                "votes": votes,
                "stable": stable,
                "updated_at": time.time(),
            }
        )

        return self._prefer_plate(current_best, candidate)

    def _aggregate_plate_text(self, history: list[dict]) -> str | None:
        weighted_positions: list[dict[str, float]] = [defaultdict(float) for _ in range(8)]
        for obs in history:
            text = obs.get("text")
            if not isinstance(text, str) or len(text) != 8:
                continue
            weight = max(float(obs.get("score", 0.0)), 0.01)
            for idx, ch in enumerate(text):
                weighted_positions[idx][ch] += weight

        if not all(weighted_positions):
            return None

        chars = [max(position.items(), key=lambda item: item[1])[0] for position in weighted_positions]
        candidate = "".join(chars)
        normalized, _ = self._normalize_kz_segment(candidate)
        return normalized

    def _apply_known_plate_correction(self, text: str, confidence: float, votes: int) -> str:
        if not text:
            return text
        if confidence < OCR_STICKY_CONFIDENCE and votes < OCR_MIN_STABLE_VOTES:
            return text

        candidates = [
            plate for plate in self._get_known_plates()
            if len(plate) == 8 and plate[:3] == text[:3] and plate[6:] == text[6:]
        ]
        matches = [plate for plate in candidates if self._hamming_distance(plate, text) == 1]
        return matches[0] if len(matches) == 1 else text

    def _get_known_plates(self) -> set[str]:
        now = time.time()
        if now - self._known_plates_loaded_at < 60 and self._known_plates_cache:
            return self._known_plates_cache

        plates: set[str] = set()
        try:
            from core.whitelist_manager import whitelist_mgr

            plates.update({plate.upper().strip() for plate in getattr(whitelist_mgr, "_cache", set())})
        except Exception:
            pass

        try:
            with sqlite3.connect(str(DB_PATH)) as conn:
                rows = conn.execute(
                    """
                    SELECT DISTINCT plate
                    FROM alarms
                    WHERE plate IS NOT NULL AND LENGTH(plate) = 8
                    ORDER BY created_at DESC
                    LIMIT 200
                    """
                ).fetchall()
                plates.update(row[0].upper().strip() for row in rows if row and row[0])
        except Exception:
            pass

        self._known_plates_cache = plates
        self._known_plates_loaded_at = now
        return self._known_plates_cache

    def _prefer_plate(self, current: dict | None, candidate: dict) -> dict:
        if current is None:
            return candidate

        if current.get("text") == candidate.get("text"):
            return candidate if self._plate_rank(candidate) >= self._plate_rank(current) else current

        current_score = float(current.get("score", current.get("confidence", 0.0)))
        candidate_score = float(candidate.get("score", candidate.get("confidence", 0.0)))
        current_votes = int(current.get("votes", 1) or 1)
        candidate_votes = int(candidate.get("votes", 1) or 1)

        if (
            current.get("stable")
            and float(current.get("confidence", 0.0)) >= OCR_STICKY_CONFIDENCE
            and candidate_score < current_score + OCR_REPLACE_MARGIN
            and candidate_votes <= current_votes
        ):
            return current

        return candidate if self._plate_rank(candidate) > self._plate_rank(current) else current

    def _plate_rank(self, plate: dict) -> tuple:
        return (
            int(bool(plate.get("stable"))),
            int(plate.get("votes", 1) or 1),
            round(float(plate.get("score", 0.0)), 4),
            round(float(plate.get("confidence", 0.0)), 4),
            round(float(plate.get("quality", 0.0)), 4),
            int(plate.get("plate_area", 0) or 0),
        )

    def _hamming_distance(self, left: str, right: str) -> int:
        if len(left) != len(right):
            return 99
        return sum(1 for a, b in zip(left, right) if a != b)

    def _clone_result(self, result: dict | None) -> dict | None:
        if not result:
            return None
        cloned = {}
        for key, value in result.items():
            if isinstance(value, np.ndarray):
                cloned[key] = value.copy()
            elif isinstance(value, list):
                cloned[key] = list(value)
            else:
                cloned[key] = value
        return cloned
