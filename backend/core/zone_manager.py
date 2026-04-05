"""
zone_manager.py — Yasak Park Bölge Yönetimi

AMAÇ: Her kamera için yasak park polygon bölgelerini yönet.
      Araç bbox'ının alt merkezi bölge içinde mi kontrol et.
      Bölgeler zones.json'da saklanır.
      Web arayüzünden anlık değiştirilebilir.

Neden alt merkez noktası (cx, y2):
  Araçlar tekerleklerinin üzerinde durur.
  Araç kısmen bölge dışında ama tekerlekleri içinde olabilir.
  Alt merkez = tekerlek noktası → gerçek ihlali yakalar.
"""

import json
import uuid
import logging
import threading
from shapely.geometry import Point, Polygon
from config import ZONES_PATH

logger = logging.getLogger(__name__)


class ZoneManager:

    def __init__(self):
        self.zones: list[dict] = []
        self._polygon_cache: dict[str, Polygon] = {}  # zone_id → Shapely Polygon
        self._lock = threading.Lock()
        self._load()

    def _build_polygon_cache(self) -> None:
        """Tüm aktif zone'lar için Shapely Polygon nesnelerini önceden oluştur.
        Zone eklendiğinde/güncellendiğinde/silindiğinde çağrılır."""
        self._polygon_cache = {}
        for zone in self.zones:
            if zone.get("active", True) and len(zone.get("polygon", [])) >= 3:
                self._polygon_cache[zone["id"]] = Polygon(zone["polygon"])

    def _load(self) -> None:
        """zones.json'dan bölgeleri yükle."""
        if ZONES_PATH.exists():
            try:
                with open(ZONES_PATH, "r", encoding="utf-8") as f:
                    self.zones = json.load(f)
                self._build_polygon_cache()
                logger.info(f"{len(self.zones)} bolge yuklendi")
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Bolge dosyasi okunamadi: {e}")
                self.zones = []
        else:
            logger.info("Bolge dosyasi bulunamadi, bos baslatiliyor")

    def _save(self) -> None:
        """Bölgeleri zones.json'a kaydet."""
        ZONES_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(ZONES_PATH, "w", encoding="utf-8") as f:
            json.dump(self.zones, f, ensure_ascii=False, indent=2)

    def add_zone(
        self,
        camera_id: int,
        name: str,
        polygon: list[list[int]],
        color: str = "#FF0000",
    ) -> dict:
        """Yeni yasak park bölgesi ekle."""
        zone = {
            "id": str(uuid.uuid4()),
            "camera_id": camera_id,
            "name": name,
            "polygon": polygon,  # [[x,y], [x,y], ...]
            "color": color,
            "active": True,
        }
        with self._lock:
            self.zones.append(zone)
            self._polygon_cache[zone["id"]] = Polygon(polygon)
            self._save()
        logger.info(f"Bolge eklendi: {name} (Kamera {camera_id})")
        return zone

    def check_violation(self, detection: dict) -> dict | None:
        """
        Araç yasak bölgede mi?
        Alt merkez noktası (tekerlekler) polygon içinde mi kontrol eder.
        Polygon nesneleri önbellekten alınır — her frame'de yeniden oluşturulmaz.

        Returns:
            Zone dict veya None
        """

        bbox = detection["bbox"]
        cam_id = detection["camera_id"]

        # Alt merkez noktası (tekerlek pozisyonu)
        cx = (bbox[0] + bbox[2]) / 2
        cy = bbox[3]  # y2 = alt kenar
        point = Point(cx, cy)

        with self._lock:
            for zone in self.zones:
                if not zone.get("active", True):
                    continue
                if zone["camera_id"] != cam_id:
                    continue

                # Önbellekten al — sıfırdan oluşturma yok
                polygon = self._polygon_cache.get(zone["id"])
                if polygon is None:
                    continue

                if polygon.contains(point):
                    return zone

        return None

    def get_all_zones(self) -> list[dict]:
        with self._lock:
            return list(self.zones)

    def get_zones_for_camera(self, camera_id: int) -> list[dict]:
        with self._lock:
            return [z for z in self.zones if z["camera_id"] == camera_id]

    def get_zone(self, zone_id: str) -> dict | None:
        with self._lock:
            for zone in self.zones:
                if zone["id"] == zone_id:
                    return zone
            return None

    def update_zone(self, zone_id: str, updates: dict) -> dict | None:
        """Bölge güncelle (ad, polygon, renk, aktiflik)."""
        with self._lock:
            for zone in self.zones:
                if zone["id"] == zone_id:
                    allowed_fields = {"name", "polygon", "color", "active"}
                    for key, value in updates.items():
                        if key in allowed_fields:
                            zone[key] = value
                    # Polygon veya aktiflik değiştiyse önbelleği güncelle
                    if "polygon" in updates and zone.get("active", True):
                        self._polygon_cache[zone_id] = Polygon(zone["polygon"])
                    elif "active" in updates:
                        if updates["active"]:
                            self._polygon_cache[zone_id] = Polygon(zone["polygon"])
                        else:
                            self._polygon_cache.pop(zone_id, None)
                    self._save()
                    return zone
        return None

    def delete_zone(self, zone_id: str) -> bool:
        with self._lock:
            before = len(self.zones)
            self.zones = [z for z in self.zones if z["id"] != zone_id]
            if len(self.zones) < before:
                self._polygon_cache.pop(zone_id, None)
                self._save()
                return True
        return False
