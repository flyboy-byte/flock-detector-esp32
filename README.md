# flock-detector-esp32

A personal toolkit for passively detecting Flock Safety ALPR cameras and similar roadside surveillance devices. Built around the Xiao ESP32 S3, with a Python TUI for live wardriving use.

This is a from-scratch port, not a fork. Two reference implementations are vendored under `references/` for study.

---

## Current status

**The firmware detection code is written. It has not been flashed or validated on real hardware.**

| Component | Status |
|---|---|
| Detection signatures (WiFi + BLE) | Done |
| WiFi active scan + matching | Written, not hardware-tested |
| WiFi promiscuous (raw 802.11 frames) | Written, not hardware-tested |
| BLE advertisement scan + matching | Written, not hardware-tested |
| Serial JSON output | Written, not hardware-tested |
| MAC dedup / 30 s cooldown | Written, not hardware-tested |
| Python TUI (Textual) | Works in demo mode |
| GPS tagging (TUI-side) | Done |
| CSV / KML / deflock export | Done |
| End-to-end (ESP32 → TUI) | Not tested |
| deflock.me HTTP submission | Stub only — writes a local JSON file |

---

## What this is not

- Not tested on real hardware yet
- Not guaranteed to compile cleanly without adjustment — first flash will find issues
- Not an exploit tool, jamming device, or active transmitter
- Not affiliated with either reference project

---

## Background

Flock Safety ALPR cameras are deployed across thousands of US municipalities, HOAs, and private lots. They run over WiFi and BLE, and their network signatures are identifiable passively. The [deflock.me](https://deflock.me) community project and [GainSec](https://gainsec.com) research have documented those signatures — specific MAC OUI prefixes, SSID patterns, and BLE advertisement names consistent across Flock Safety hardware and their Penguin and Pigvision variants.

This project uses those signatures to build a portable detector that logs what it sees, tags detections with GPS coordinates, and exports to CSV, KML, or the deflock.me crowdsourced database.

---

## Repository layout

```
firmware/             # Arduino IDE sketch (primary build target)
  firmware.ino        # Entry point — setup(), loop()
  config.h            # Board pins, feature flags, timing constants
  wifi_signatures.h   # MAC prefixes, SSID patterns, 5 GHz channel list
  ble_signatures.h    # BLE device name patterns
  sig_match.h         # Shared matching functions (MAC prefix, SSID, BLE name)
  detection_output.h  # JSON serialization to Serial + threat scoring
  seen_cache.h        # 64-slot dedup ring buffer, 30-second TTL
  wifi_scan.h         # Active WiFi scan (every 5 s)
  wifi_promisc.h      # Promiscuous 802.11 frame capture + channel hopping
  ble_scan.h          # NimBLE advertisement scan (1 s per loop)

src/main.cpp          # PlatformIO entry point (identical logic to firmware.ino)
platformio.ini        # Three board envs: xiao_esp32s3, esp32_wroom, esp32_wrover

signatures/
  signatures.json     # Signature data for Python tools / demo mode

tools/                # Python TUI and utilities
  tui.py              # Textual app — live detection table, export buttons
  serial_reader.py    # Background thread: reads JSON from ESP32
  gps_reader.py       # Background thread: NMEA GPS parser
  store.py            # Detection dataclass + thread-safe store
  export.py           # CSV, KML, deflock export
  demo.py             # Fake detections for testing without hardware
  requirements.txt

references/           # Vendored reference projects (read-only)
  flock-you/          # Full-featured reference: Arduino/PIO + Flask dashboard
  Flock-Safety-Trap-Shooter-Sniffer-Alarm/   # Minimal ESP-IDF sniffer

notes/                # Planning and architecture docs
```

---

## How detection works

Three overlapping layers run simultaneously:

**1. Active WiFi scan** — `WiFi.scanNetworks()` every 5 seconds. Each visible AP's SSID and BSSID are checked against known patterns. Catches any Flock camera that is actively beaconing.

**2. WiFi promiscuous mode** — Raw 802.11 management frame capture between active scans. Handles:
- Probe requests (subtype 4): frames sent by Flock cameras scanning for their home network — detectable even when the camera's SSID is hidden
- Beacons / probe responses (subtypes 8/5): same SSID + MAC matching as active scan

Channel hops 1–13 on 2.4 GHz every 2.5 seconds; on S3 (5 GHz capable), interleaves 5 GHz channels from the signature list.

**3. BLE scan** — NimBLE 1-second scan per loop. Checks advertised device names and MAC prefixes against known Flock Safety / Penguin / Pigvision BLE signatures.

Any hit from any layer emits one JSON line to Serial:
```json
{"mac_address":"70:c9:4e:11:22:33","protocol":"wifi","detection_method":"ssid_match","rssi":-62,"device_category":"FLOCK_SAFETY","threat_score":100,"timestamp":12345,"ssid":"flock_cam_01"}
```

A 30-second dedup cache prevents re-emitting the same MAC every scan cycle.

---

## Detection signatures

| Category | Prefixes |
|---|---|
| Flock Safety WiFi | `70:c9:4e` `3c:91:80` `d8:f3:bc` `80:30:49` `14:5a:fc` `74:4c:a1` `08:3a:88` `9c:2f:9d` |
| Flock Ext Battery | `58:8e:81` `ec:1b:bd` `90:35:ea` `04:0d:84` `f0:82:c0` `1c:34:f1` `38:5b:44` `94:34:69` `b4:e3:f9` |
| Penguin / Pigvision | 19 prefixes (see `firmware/wifi_signatures.h`) |
| SSID patterns | `flock` `FS Ext Battery` `Penguin` `Pigvision` |
| BLE name patterns | `FS Ext Battery` `Flock` `Penguin` `Pigvision` |

---

## Python TUI

The TUI works now without hardware (demo mode generates realistic fake detections).

```bash
cd /path/to/flock-detector-esp32
python3 -m venv tools/.venv && source tools/.venv/bin/activate
pip install -r tools/requirements.txt

python tools/tui.py --demo                          # fake detections, no hardware
python tools/tui.py --demo --replay captures/log.json
python tools/tui.py --port /dev/ttyACM0             # live ESP32
python tools/tui.py --port /dev/ttyACM0 --gps /dev/ttyUSB0
```

Keybindings: `c` CSV, `k` KML, `d` deflock export, `x` clear, `r` refresh ports, `q` quit.

Exports land in `exports/` (gitignored).

---

## Building the firmware

### Arduino IDE

Open `firmware/firmware.ino`.

Tools menu settings:
- Board: ESP32 Arduino → XIAO_ESP32S3
- USB CDC on boot: Enabled
- Flash size: 8MB
- Partition scheme: Huge APP

Libraries (Manage Libraries): `NimBLE-Arduino` by h2zero, `ArduinoJson` by Benoit Blanchon.

### PlatformIO

```bash
pio run -e xiao_esp32s3
pio run -e xiao_esp32s3 -t upload
pio device monitor --port /dev/ttyACM0 --config baudrate=115200

# Other supported boards:
pio run -e esp32_wroom
pio run -e esp32_wrover
```

Expected serial output on boot:
```
========================================
  flock-detector-esp32
  version:  0.1.0-dev
  target:   Xiao ESP32 S3
  status:   boot ok
========================================

{"status":"wifi_scan_ready"}
{"status":"wifi_promisc_ready"}
{"status":"ble_scan_ready"}
```

Then JSON detection lines as cameras are found.

---

## What needs hardware validation next

- Boot message prints over USB CDC
- `WiFi.scanNetworks()` + signature match fires correctly
- Promiscuous callback fires on real traffic; 802.11 IE frame offsets need live verification
- NimBLE initializes without conflicting with WiFi coexistence
- Tune `WIFI_SCAN_INTERVAL_MS` and `CHANNEL_HOP_INTERVAL_MS` against real scan timing
- End-to-end: ESP32 → TUI table → GPS tag → export

---

## Hardware

**Primary target: Xiao ESP32 S3** — compact, dual-band WiFi/BLE, USB-C, 8 MB flash.

Also supported via PlatformIO: ESP32-WROOM (`esp32_wroom`), ESP32-WROVER (`esp32_wrover`). These boards are 2.4 GHz only (`BOARD_HAS_5GHZ=0`).

USB GPS dongle: connects to the laptop running the TUI, not to the ESP32.

---

## Reference implementations

**flock-you** — primary reference. Full Arduino/PlatformIO project with Flask + SocketIO dashboard, GPS, CSV/KML export. Datasets from deflock.me included.
```bash
cd references/flock-you && pio run --target upload && pio device monitor
cd references/flock-you/api && pip install -r requirements.txt && python flockyou.py
```

**Flock-Safety-Trap-Shooter-Sniffer-Alarm** — minimal ESP-IDF one-shot sniffer for ESP32-C6.
```bash
cd references/Flock-Safety-Trap-Shooter-Sniffer-Alarm && idf.py build && idf.py flash
```

---

## Credits

- **flock-you** — primary reference firmware and dashboard
- **Flock-Safety-Trap-Shooter-Sniffer-Alarm** by [Jon Gaines / GainSec](https://gainsec.com); original acknowledgement to [dj1ch](https://github.com/dj1ch)
- **[deflock.me](https://deflock.me)** — crowdsourced ALPR location database; MAC prefix and SSID patterns trace back to their dataset work

---

## Legal

Passive and receive-only. No transmission, no jamming, no network association.

WiFi promiscuous mode captures unencrypted 802.11 management frames (probe requests, beacons) that devices broadcast publicly. Verify local regulations before use. Don't use this to track people.
