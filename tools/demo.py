"""Demo mode: generate fake detections or replay a JSON file.
Used for building and testing the TUI without hardware."""

from __future__ import annotations

import json
import random
import time
from datetime import datetime
from pathlib import Path

_SIG_PATH = Path(__file__).parent.parent / "signatures" / "signatures.json"


def _load_prefixes() -> list[str]:
    try:
        with open(_SIG_PATH) as f:
            sigs = json.load(f)
        prefixes: list[str] = []
        for group in sigs["mac_prefixes"].values():
            prefixes.extend(group)
        return prefixes
    except Exception:
        return ["70:c9:4e", "cc:09:24", "58:8e:81"]


def _random_mac(prefix: str) -> str:
    tail = ":".join(f"{random.randint(0, 255):02x}" for _ in range(3))
    return f"{prefix}:{tail}"


def _fake_detection(prefixes: list[str]) -> dict:
    prefix = random.choice(prefixes)
    protocol = random.choice(["wifi", "bluetooth_le"])
    ssids = ["flock_cam_01", "FS Ext Battery", "Penguin_node", "FLOCK_CAM", None]
    ble_names = ["FS Ext Battery", "Flock", "Penguin", None]

    if protocol == "wifi":
        method = random.choice(["ssid_match", "mac_prefix"])
        ssid = random.choice(ssids)
        ble_name = None
    else:
        method = random.choice(["ble_name", "ble_mac"])
        ssid = None
        ble_name = random.choice(ble_names)

    return {
        "detection_method": method,
        "protocol": protocol,
        "mac_address": _random_mac(prefix),
        "ssid": ssid,
        "device_name": ble_name,
        "rssi": random.randint(-90, -40),
        "threat_score": random.choice([70, 85, 100]),
        "device_category": "FLOCK_SAFETY",
        "timestamp": datetime.now().isoformat(),
    }


def generate(callback: callable, interval: float = 1.5, count: int | None = None) -> None:
    """Call callback(json_line) at interval. Runs until count reached or forever."""
    prefixes = _load_prefixes()
    i = 0
    while count is None or i < count:
        det = _fake_detection(prefixes)
        callback(json.dumps(det))
        time.sleep(interval)
        i += 1


def replay(path: str, callback: callable, interval: float = 1.0) -> None:
    """Replay detections from a newline-delimited JSON file."""
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                callback(line)
                time.sleep(interval)
