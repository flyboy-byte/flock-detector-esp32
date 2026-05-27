# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Structure

This repo contains two independent surveillance-detection tools targeting Flock Safety cameras:

- **`flock-you/`** — Full-featured detector for the Xiao ESP32 S3 (PlatformIO/Arduino), with a Flask+SocketIO web dashboard
- **`Flock-Safety-Trap-Shooter-Sniffer-Alarm/`** — Minimal sniffer for the M5NanoC6 (ESP32-C6), built with ESP-IDF

---

## flock-you

### Firmware (PlatformIO)

```bash
cd flock-you

# Build and flash to Xiao ESP32 S3 (connected via USB-C)
pio run --target upload

# Monitor serial output at 115200 baud
pio device monitor

# Build only (no flash)
pio run
```

Target board is `seeed_xiao_esp32s3` with 8MB flash (`huge_app.csv` partition table). Dependencies: `NimBLE-Arduino@^1.4.0`, `ArduinoJson@^6.21.0`.

### Web Dashboard API (Python)

```bash
cd flock-you/api

# First-time setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run the server (http://localhost:5000)
python flockyou.py
```

---

## Flock-Safety-Trap-Shooter-Sniffer-Alarm (ESP-IDF)

Requires ESP-IDF toolchain installed and `IDF_PATH` set.

```bash
cd Flock-Safety-Trap-Shooter-Sniffer-Alarm

idf.py build
idf.py flash
idf.py monitor
```

---

## Architecture

### flock-you firmware (`src/main.cpp`)

Single-file Arduino sketch with two concurrent detection paths:

1. **WiFi promiscuous mode** — installs `wifi_sniffer_packet_handler` as a raw 802.11 callback. Parses probe requests (subtype 0x04) and beacons (subtype 0x08) directly from the frame payload. Hops channels 1–13 every 2.5 seconds.
2. **BLE scanning** — uses NimBLE-Arduino's `NimBLEScan` with `AdvertisedDeviceCallbacks::onResult` running a 1-second scan each loop iteration.

Both paths check against hardcoded `mac_prefixes[]` and `wifi_ssid_patterns[]`/`device_name_patterns[]` arrays. On hit, the firmware emits a JSON detection object over `Serial` (115200 baud) and plays a buzzer sequence. A `device_in_range`/`triggered` state machine gates repeated alerts and fires heartbeat beeps every 10 s while the device is in range.

### flock-you web API (`api/flockyou.py`)

Flask app with Flask-SocketIO (threading async mode). Key global state: `detections` (session), `cumulative_detections` (persisted via pickle to `data/cumulative_detections.pkl`), `gps_history` (ring buffer of 100 NMEA fixes).

Three background threads:
- **`flock_reader`** — reads JSON lines from the ESP32 serial port, calls `add_detection_from_serial()` for lines containing `detection_method`
- **`gps_reader`** — reads NMEA sentences from a separate GPS serial port, parses `$GPGGA`/`$GNGGA`, updates `gps_data` and `gps_history`
- **`connection_monitor`** — polls both serial connections every 2 s and triggers `attempt_reconnect_flock()`/`attempt_reconnect_gps()` on failure

`add_detection_from_serial()` is the core aggregation function: it deduplicates by MAC address (incrementing `detection_count` on repeat), performs temporal GPS matching against `gps_history` (threshold: 30 s, prefers matches <5 s), looks up the OUI manufacturer, and emits `new_detection` or `detection_updated` via SocketIO.

Export routes (`/api/export/csv`, `/api/export/kml`) flatten the nested `gps` dict into per-row columns. KML export includes only detections that have GPS coordinates.

### Flock-Safety-Trap-Shooter-Sniffer-Alarm (`main/sniffer.c`)

Minimal ESP-IDF app. Installs a promiscuous callback that scans beacon (subtype 8), probe response (subtype 5), and probe request (subtype 4) frames for the string "flock" (case-insensitive). On first match it sets `triggered = true`, disables promiscuous mode, and halts. Channel hopping covers both 2.4 GHz (1–13) and 5 GHz (36–165) channels.
