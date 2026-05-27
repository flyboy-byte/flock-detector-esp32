from __future__ import annotations

import csv
import json
import os
from datetime import datetime

from store import Detection

EXPORT_DIR = "exports"


def _ensure_dir() -> None:
    os.makedirs(EXPORT_DIR, exist_ok=True)


def _filename(prefix: str, ext: str) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(EXPORT_DIR, f"{prefix}_{ts}.{ext}")


def export_csv(detections: list[Detection]) -> str:
    _ensure_dir()
    path = _filename("flock_session", "csv")
    fields = [
        "mac", "protocol", "detection_method", "device_type",
        "ssid", "ble_name", "rssi", "confidence",
        "seen_count", "first_seen", "last_seen",
        "lat", "lon", "alt",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for d in detections:
            writer.writerow({
                "mac": d.mac,
                "protocol": d.protocol,
                "detection_method": d.detection_method,
                "device_type": d.device_type,
                "ssid": d.ssid or "",
                "ble_name": d.ble_name or "",
                "rssi": d.rssi,
                "confidence": f"{d.confidence:.2f}",
                "seen_count": d.seen_count,
                "first_seen": d.first_seen.isoformat(),
                "last_seen": d.last_seen.isoformat(),
                "lat": d.lat if d.lat is not None else "",
                "lon": d.lon if d.lon is not None else "",
                "alt": d.alt if d.alt is not None else "",
            })
    return path


def export_kml(detections: list[Detection]) -> str:
    _ensure_dir()
    path = _filename("flock_session", "kml")
    gps_hits = [d for d in detections if d.lat is not None]

    placemarks = ""
    for d in gps_hits:
        label = d.ssid or d.ble_name or d.mac
        placemarks += f"""
  <Placemark>
    <name>{label}</name>
    <description><![CDATA[
      <b>MAC:</b> {d.mac}<br/>
      <b>Protocol:</b> {d.protocol}<br/>
      <b>Method:</b> {d.detection_method}<br/>
      <b>RSSI:</b> {d.rssi} dBm<br/>
      <b>Seen:</b> {d.seen_count}x<br/>
      <b>First seen:</b> {d.first_seen.strftime('%Y-%m-%d %H:%M:%S')}<br/>
      <b>Confidence:</b> {d.confidence:.0%}
    ]]></description>
    <Point>
      <coordinates>{d.lon},{d.lat},{d.alt or 0}</coordinates>
    </Point>
  </Placemark>"""

    kml = f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document>
  <name>Flock Detections {datetime.now().strftime('%Y-%m-%d')}</name>
  <description>{len(detections)} total detections, {len(gps_hits)} with GPS</description>
  {placemarks}
</Document>
</kml>"""

    with open(path, "w", encoding="utf-8") as f:
        f.write(kml)
    return path


def export_deflock(detections: list[Detection]) -> str:
    """Write detections as JSON for deflock.me submission.
    API format TBD — produces a file for manual review until the API is confirmed."""
    _ensure_dir()
    path = _filename("flock_deflock", "json")
    records = [
        {
            "mac": d.mac,
            "ssid": d.ssid,
            "lat": d.lat,
            "lon": d.lon,
            "first_seen": d.first_seen.isoformat(),
            "last_seen": d.last_seen.isoformat(),
            "protocol": d.protocol,
            "seen_count": d.seen_count,
        }
        for d in detections
        if d.lat is not None  # deflock requires GPS coords
    ]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)
    return path
