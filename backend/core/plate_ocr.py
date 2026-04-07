"""
plate_ocr.py — Plaka OCR Modülü (nomeroff-net)

AMAÇ: Araç bbox'ından plaka bölgesini tesspit et ve Kazakistan plakasını oku.
      nomeroff-net: plakaya özel eğitilmiş YOLOv8 dedektörü + RNN OCR.
      Sadece ihlaldeki araçlara uygulanır (main.py'de filtrelenir).

Neden nomeroff-net:
  PaddleOCR (genel OCR)  → araç bbox'ı keser, plaka nerede bilmez → hata yüksek
  nomeroff-net (plakaya özel) → önce plakayı bulur, sonra okur → ~%95+ doğruluk
  KZ desteği: Kazakistan plaka modeli dahil
"""

import logging
import numpy as np
from config import OCR_MAX_QUEUE, OCR_CONF_THRESHOLD

logger = logging.getLogger(__name__)


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
            logger.warning(f"nomeroff-net baslatma hatasi: {e} — PaddleOCR'a geciliyor")
            self._pipeline = None
            self._backend = "paddle"
            self._init_paddle_fallback()

        self.results: dict[int, dict] = {}  # track_id → son OCR sonucu (önbellek)

    def _init_paddle_fallback(self) -> None:
        """nomeroff-net yüklenemezse PaddleOCR ile devam et."""
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
        """
        Araç frame'inden plaka oku.

        Args:
            vehicle_frame: Tam kamera frame'i
            bbox: [x1, y1, x2, y2] araç bounding box

        Returns:
            {"text": str, "confidence": float} veya None
        """
        if self._backend == "nomeroff":
            return self._read_nomeroff(vehicle_frame, bbox)
        else:
            return self._read_paddle(vehicle_frame, bbox)

    def _read_nomeroff(self, vehicle_frame: np.ndarray, bbox: list[int]) -> dict | None:
        """nomeroff-net ile plaka oku."""
        try:
            # Araç bölgesini kes
            h, w = vehicle_frame.shape[:2]
            x1 = max(0, bbox[0])
            y1 = max(0, bbox[1])
            x2 = min(w, bbox[2])
            y2 = min(h, bbox[3])

            crop = vehicle_frame[y1:y2, x1:x2]
            if crop.size == 0:
                return None

            # nomeroff-net pipeline: plaka bul + oku
            # Son eleman (confidences): per-karakter güven listesi
            texts, confidences = self._extract_nomeroff_outputs(
                self._unzip(self._pipeline([crop]))
            )

            if not texts or not texts[0]:
                return None

            # En uzun (en muhtemel tam plaka) sonucu al
            plate_text = max(texts[0], key=len) if texts[0] else None
            if not plate_text or len(plate_text) < 4:
                return None

            plate_text = plate_text.upper().strip()

            # Gerçek güven skorunu hesapla — per-karakter ortalaması
            conf = 0.90  # nomeroff-net pipeline varsayılan (iyi model)
            try:
                if confidences and confidences[0]:
                    char_confs = confidences[0]
                    # Nested liste olabilir: [[c1, c2, ...]]
                    if isinstance(char_confs, (list, tuple)) and char_confs:
                        first = char_confs[0]
                        if isinstance(first, (list, tuple)) and first:
                            char_confs = first
                        numeric = [c for c in char_confs if isinstance(c, (int, float))]
                        if numeric:
                            conf = round(sum(numeric) / len(numeric), 3)
            except Exception:
                pass  # Parse hatasında varsayılan değer geçerli

            if conf < OCR_CONF_THRESHOLD:
                return None

            return {"text": plate_text, "confidence": conf}

        except Exception as e:
            logger.error(f"nomeroff-net OCR hatasi: {e}")
            return None

    def _extract_nomeroff_outputs(self, payload) -> tuple[list, list]:
        texts = []
        confidences = []

        if isinstance(payload, dict):
            texts = payload.get("texts") or payload.get("text") or []
            confidences = payload.get("confidences") or payload.get("scores") or []
            return texts, confidences

        if isinstance(payload, (list, tuple)):
            if len(payload) >= 2:
                texts = payload[-2] or []
                confidences = payload[-1] or []
            elif len(payload) == 1:
                texts = payload[0] or []

        return texts, confidences

    def _read_paddle(self, vehicle_frame: np.ndarray, bbox: list[int]) -> dict | None:
        """PaddleOCR yedek ile plaka oku."""
        if not self._paddle:
            return None
        try:
            import re
            KZ_PATTERNS = [
                r'[А-ЯA-Z]{3}\s?\d{3}\s?[А-ЯA-Z]{2}',
                r'\d{3}[А-ЯA-Z]{3}\d{2}',
                r'[А-ЯA-Z]{2}\d{4}[А-ЯA-Z]{2}',
            ]
            h, w = vehicle_frame.shape[:2]
            x1, y1 = max(0, bbox[0]), max(0, bbox[1])
            x2, y2 = min(w, bbox[2]), min(h, bbox[3])
            crop = vehicle_frame[y1:y2, x1:x2]
            if crop.size == 0:
                return None

            result = self._paddle.ocr(crop, cls=True)
            if not result or not result[0]:
                return None

            best_text, best_conf = "", 0.0
            for line in result[0]:
                text, conf = line[1]
                if conf > best_conf:
                    best_conf, best_text = conf, text

            if best_conf < 0.70:
                return None

            text = best_text.upper().strip()
            text = re.sub(r'\s+', ' ', text)
            for pattern in KZ_PATTERNS:
                if re.search(pattern, text):
                    return {"text": text, "confidence": round(best_conf, 3)}
            return None

        except Exception as e:
            logger.error(f"PaddleOCR hatasi: {e}")
            return None

    def get_cached(self, track_id: int) -> dict | None:
        """Önbellekten plaka sonucu al."""
        return self.results.get(track_id)

    def cache_result(self, track_id: int, result: dict) -> None:
        """OCR sonucunu önbelleğe yaz. Dolunca en eski girdiyi sil."""
        if track_id in self.results:
            del self.results[track_id]
        self.results[track_id] = result
        while len(self.results) > OCR_MAX_QUEUE:
            self.results.pop(next(iter(self.results)))

    def clear_track(self, track_id: int) -> None:
        """Track kaybolunca önbellekten sil."""
        self.results.pop(track_id, None)
