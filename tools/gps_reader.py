from __future__ import annotations

import threading
import time
from dataclasses import dataclass

import serial


@dataclass
class GPSFix:
    lat: float
    lon: float
    alt: float
    satellites: int
    fix_quality: int
    system_timestamp: float  # time.time() when fix was received


class GPSReader:
    MAX_HISTORY = 100
    MATCH_THRESHOLD = 30.0  # seconds

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._history: list[GPSFix] = []
        self._current: GPSFix | None = None
        self._thread: threading.Thread | None = None
        self._running = False
        self._ser: serial.Serial | None = None
        self.on_fix: callable | None = None  # called with GPSFix on each valid fix

    def connect(self, port: str, baudrate: int = 9600) -> None:
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
                line = self._ser.readline().decode("utf-8", errors="ignore").strip()
                fix = self._parse(line)
                if fix:
                    with self._lock:
                        self._current = fix
                        self._history.append(fix)
                        if len(self._history) > self.MAX_HISTORY:
                            self._history.pop(0)
                    if self.on_fix:
                        self.on_fix(fix)
            except Exception:
                time.sleep(0.1)

    def _parse(self, sentence: str) -> GPSFix | None:
        if not sentence.startswith("$"):
            return None
        parts = sentence.split(",")
        if parts[0] not in ("$GPGGA", "$GNGGA") or len(parts) < 10:
            return None
        try:
            fix_quality = int(parts[6]) if parts[6] else 0
            if fix_quality == 0 or not parts[2] or not parts[4]:
                return None
            lat_raw, lat_dir = parts[2], parts[3]
            lon_raw, lon_dir = parts[4], parts[5]
            lat = int(lat_raw[:2]) + float(lat_raw[2:]) / 60
            lon = int(lon_raw[:3]) + float(lon_raw[3:]) / 60
            if lat_dir == "S":
                lat = -lat
            if lon_dir == "W":
                lon = -lon
            alt = float(parts[9]) if parts[9] else 0.0
            sats = int(parts[7]) if parts[7] else 0
            return GPSFix(
                lat=round(lat, 8),
                lon=round(lon, 8),
                alt=round(alt, 2),
                satellites=sats,
                fix_quality=fix_quality,
                system_timestamp=time.time(),
            )
        except (ValueError, IndexError):
            return None

    def best_fix_at(self, system_time: float) -> GPSFix | None:
        """Return the GPS fix closest in time to system_time, within MATCH_THRESHOLD."""
        with self._lock:
            best: GPSFix | None = None
            best_diff = self.MATCH_THRESHOLD
            for fix in self._history:
                diff = abs(system_time - fix.system_timestamp)
                if diff < best_diff:
                    best_diff = diff
                    best = fix
            return best

    @property
    def current(self) -> GPSFix | None:
        with self._lock:
            return self._current

    @property
    def connected(self) -> bool:
        return self._running and self._ser is not None and self._ser.is_open
