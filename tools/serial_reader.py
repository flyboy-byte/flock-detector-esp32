from __future__ import annotations

import json
import threading
import time
from datetime import datetime

import serial

from gps_reader import GPSReader
from store import Detection, DetectionStore


def parse_detection(data: dict, gps_reader: GPSReader | None = None) -> Detection | None:
    """Parse a raw JSON dict from the ESP32 into a Detection. Returns None on bad data."""
    if "detection_method" not in data:
        return None
    try:
        now = time.time()
        lat = lon = alt = None
        if gps_reader:
            fix = gps_reader.best_fix_at(now)
            if fix:
                lat, lon, alt = fix.lat, fix.lon, fix.alt

        ts = datetime.now()
        return Detection(
            mac=data.get("mac_address", "unknown"),
            protocol=data.get("protocol", "unknown"),
            detection_method=data.get("detection_method", "unknown"),
            rssi=int(data.get("rssi", 0)),
            ssid=data.get("ssid") or None,
            ble_name=data.get("device_name") or None,
            device_type=data.get("device_category", "unknown"),
            confidence=(data.get("threat_score", 0) or 0) / 100.0,
            first_seen=ts,
            last_seen=ts,
            seen_count=1,
            lat=lat,
            lon=lon,
            alt=alt,
        )
    except Exception:
        return None


class SerialReader:
    def __init__(self, store: DetectionStore, gps_reader: GPSReader | None = None) -> None:
        self._store = store
        self._gps = gps_reader
        self._thread: threading.Thread | None = None
        self._running = False
        self._ser: serial.Serial | None = None
        self.on_detection: callable | None = None  # called with (Detection, is_new)
        self.on_raw_line: callable | None = None   # called with raw line string

    def connect(self, port: str, baudrate: int = 115200) -> None:
        self._ser = serial.Serial(port, baudrate, timeout=1)
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def disconnect(self) -> None:
        self._running = False
        if self._ser and self._ser.is_open:
            self._ser.close()

    def _run(self) -> None:
        while self._running:
            try:
                raw = self._ser.readline().decode("utf-8", errors="ignore").strip()
                if not raw:
                    continue
                if self.on_raw_line:
                    self.on_raw_line(raw)
                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                detection = parse_detection(data, self._gps)
                if detection:
                    det, is_new = self._store.add_or_update(detection)
                    if self.on_detection:
                        self.on_detection(det, is_new)
            except Exception:
                time.sleep(0.1)

    @property
    def connected(self) -> bool:
        return self._running and self._ser is not None and self._ser.is_open
