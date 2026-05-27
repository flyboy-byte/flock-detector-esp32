from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Detection:
    mac: str
    protocol: str           # "wifi" | "bluetooth_le"
    detection_method: str   # "ssid_match" | "mac_prefix" | "ble_name" | "ble_mac"
    rssi: int
    ssid: str | None
    ble_name: str | None
    device_type: str        # "flock_wifi" | "flock_ext" | "penguin" | "pigvision" | "unknown"
    confidence: float       # 0.0–1.0
    first_seen: datetime
    last_seen: datetime
    seen_count: int
    lat: float | None = None
    lon: float | None = None
    alt: float | None = None


class DetectionStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._detections: dict[str, Detection] = {}

    def add_or_update(self, d: Detection) -> tuple[Detection, bool]:
        """Returns (detection, is_new). Thread-safe."""
        with self._lock:
            if d.mac in self._detections:
                existing = self._detections[d.mac]
                existing.seen_count += 1
                existing.last_seen = d.last_seen
                existing.rssi = d.rssi
                if d.lat is not None:
                    existing.lat = d.lat
                    existing.lon = d.lon
                    existing.alt = d.alt
                return existing, False
            self._detections[d.mac] = d
            return d, True

    def all(self) -> list[Detection]:
        with self._lock:
            return sorted(self._detections.values(), key=lambda d: d.last_seen, reverse=True)

    def clear(self) -> None:
        with self._lock:
            self._detections.clear()

    def count(self) -> int:
        with self._lock:
            return len(self._detections)
