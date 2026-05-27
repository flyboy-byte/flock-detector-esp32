# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Where things stand

All firmware detection code is written through Milestone 8. **Nothing has been flashed or validated on real hardware.** The Python TUI works in demo mode. The project is paused at the hardware validation stage.

See `notes/project-plan.md` for the full milestone breakdown and known risks.

---

## Repository layout

```
firmware/             # Arduino IDE sketch (primary build target)
  firmware.ino        # Entry point
  config.h            # Feature flags, board detection, timing constants
  wifi_signatures.h   # MAC prefixes, SSID patterns, 5 GHz channels
  ble_signatures.h    # BLE device name patterns
  sig_match.h         # Shared matching functions
  detection_output.h  # ArduinoJson JSON serialization, threat scoring
  seen_cache.h        # 30-second MAC dedup ring buffer
  wifi_scan.h         # Active WiFi scan (every 5 s)
  wifi_promisc.h      # Promiscuous 802.11 frame capture + channel hopping
  ble_scan.h          # NimBLE BLE advertisement scan

src/main.cpp          # PlatformIO entry point — identical logic to firmware.ino
platformio.ini        # Envs: xiao_esp32s3, esp32_wroom, esp32_wrover

signatures/
  signatures.json     # Signature data for Python tools

tools/                # Python TUI (works in demo mode now)
  tui.py              # Textual app
  serial_reader.py    # Background thread: ESP32 serial JSON reader
  gps_reader.py       # Background thread: NMEA GPS parser
  store.py            # Detection dataclass + thread-safe store
  export.py           # CSV, KML, deflock export
  demo.py             # Fake detections without hardware
  requirements.txt

references/           # Read-only reference implementations
notes/                # Planning docs
```

---

## Build systems

**This project supports both Arduino IDE and PlatformIO from the same C++ source.**

- Arduino IDE: open `firmware/firmware.ino`. Headers live in `firmware/`.
- PlatformIO: `src/main.cpp` includes the same headers via `-I firmware` in `platformio.ini`.

Do not duplicate headers between `firmware/` and `src/`. Headers belong in `firmware/` only.

### Arduino IDE settings (XIAO ESP32 S3)
- Board: ESP32 Arduino → XIAO_ESP32S3
- USB CDC on boot: Enabled
- Flash size: 8MB
- Partition scheme: Huge APP
- Libraries: `NimBLE-Arduino` by h2zero, `ArduinoJson` by Benoit Blanchon

### PlatformIO
```bash
pio run -e xiao_esp32s3
pio run -e xiao_esp32s3 -t upload
pio device monitor --port /dev/ttyACM0 --config baudrate=115200

pio run -e esp32_wroom    # WROOM (2.4 GHz only)
pio run -e esp32_wrover   # WROVER (2.4 GHz only, has PSRAM)
```

### arduino-cli
```bash
arduino-cli compile --fqbn esp32:esp32:XIAO_ESP32S3 firmware
arduino-cli upload  --fqbn esp32:esp32:XIAO_ESP32S3 --port /dev/ttyACM0 firmware
arduino-cli monitor --port /dev/ttyACM0 --config baudrate=115200
```

---

## TUI (tools/)

```bash
python3 -m venv tools/.venv && source tools/.venv/bin/activate
pip install -r tools/requirements.txt

python tools/tui.py --demo                          # no hardware needed
python tools/tui.py --demo --replay captures/log.json
python tools/tui.py --port /dev/ttyACM0             # live ESP32
python tools/tui.py --port /dev/ttyACM0 --gps /dev/ttyUSB0
```

Keybindings: `c` CSV, `k` KML, `d` deflock, `x` clear, `r` refresh ports, `q` quit.

`tools/.venv/` and `exports/` are gitignored.

**Note:** Arch Linux blocks system pip (PEP 668). Always use the venv.

---

## Firmware architecture

### Detection pipeline

Three overlapping layers, all gated by feature flags in `config.h`:

1. **`FEATURE_WIFI_SCAN`** — `wifi_scan_run()` calls `WiFi.scanNetworks()` every `WIFI_SCAN_INTERVAL_MS` (5 s). Checks SSID and BSSID against signatures. Pauses promiscuous mode during scan, resumes after.

2. **`FEATURE_WIFI_PROMISCUOUS`** — `wifi_promisc_update()` called every loop iteration. `IRAM_ATTR` callback fires on every management frame. Extracts:
   - Probe requests (subtype 4): IEs start at byte 24 (no fixed params)
   - Beacons / probe responses (subtypes 8/5): IEs start at byte 36 (12 B fixed params)
   - addr2 (bytes 10–15) = transmitter MAC

3. **`FEATURE_BLE_SCAN`** — `ble_scan_run()` blocks for `BLE_SCAN_DURATION_S` (1 s) each loop. NimBLE callbacks check name and MAC.

All three use `seen_cache_suppress()` before calling `emit_detection()` to prevent flooding serial with repeat detections.

### JSON output format
```json
{"mac_address":"70:c9:4e:11:22:33","protocol":"wifi","detection_method":"ssid_match","rssi":-62,"device_category":"FLOCK_SAFETY","threat_score":100,"timestamp":12345,"ssid":"flock_cam_01"}
```

`detection_method` values: `ssid_match`, `mac_prefix`, `ble_name`, `ble_mac`

### Loop timing (approximate, all features on)
- 0–5 s: promiscuous running, BLE scan every ~1.1 s (1 s scan + 100 ms delay)
- At 5 s mark: pause promiscuous → WiFi active scan (~2–3 s blocking) → resume promiscuous
- Repeat

### Feature flags
All in `firmware/config.h`. Currently all three detection features are enabled. Comment out to disable at compile time — safe to do for debugging.

---

## Known issues / hardware risks

1. `wifi_promisc_pause/resume` interleave with active scan — untested, may need timing adjustment
2. NimBLE + WiFi promiscuous coexistence — should work via ESP-IDF coexistence layer, unverified
3. 5 GHz promiscuous mode on S3 — depends on ESP-IDF version in Arduino core
4. IE frame offsets — byte 24 vs 36 based on management subtype — needs live 802.11 traffic to verify
5. `strcasestr` — available in ESP-IDF libc, same as reference code, but confirm on first build

---

## Reference implementations (read-only)

### flock-you firmware (`references/flock-you/src/main.cpp`)
Single-file Arduino sketch. Two concurrent detection paths:
1. WiFi promiscuous — `wifi_sniffer_packet_handler` on management frames, channel hops 1–13 every 2.5 s
2. BLE — 1-second `NimBLEScan` each loop

State machine: `device_in_range` flag prevents re-alerting; resets after 30 s silence.

### flock-you web API (`references/flock-you/api/flockyou.py`)
Flask + Flask-SocketIO. Key: `add_detection_from_serial()` does GPS temporal matching (30 s window, prefer <5 s), OUI lookup, MAC dedup.
```bash
cd references/flock-you/api && pip install -r requirements.txt && python flockyou.py
# http://localhost:5000
```

### Sniffer-Alarm (`references/Flock-Safety-Trap-Shooter-Sniffer-Alarm/main/sniffer.c`)
Minimal ESP-IDF. One-shot: first detection stops channel hopping and exits. 2.4 + 5 GHz channels. No BLE.
```bash
cd references/Flock-Safety-Trap-Shooter-Sniffer-Alarm && idf.py build && idf.py flash
```
