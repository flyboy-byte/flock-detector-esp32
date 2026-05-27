# Repo Architecture

Directory layout and rationale. This is the decided structure — don't reorganize without updating this file.

---

## Layout

```
flock-detector-esp32/
├── README.md                   # Project README
│
├── firmware/                   # Arduino IDE sketch
│   ├── firmware.ino            # Entry point: setup() and loop()
│   ├── config.h                # Feature flags, pin defs, timing constants, version
│   ├── wifi_signatures.h       # MAC prefixes and SSID patterns
│   └── ble_signatures.h        # BLE device name patterns and MAC prefixes
│
├── signatures/                 # Detection signatures for Python tools
│   └── signatures.json         # MAC prefixes, SSID patterns, BLE names as JSON
│
├── tools/                      # Python utilities and dashboard
│   ├── requirements.txt        # Python dependencies
│   ├── dashboard/              # Flask + SocketIO web dashboard (Milestone 10)
│   │   └── ...
│   ├── serial_reader.py        # Consume serial JSON from ESP32, write to local log
│   └── export/                 # CSV, KML, analysis tools
│
├── docs/                       # Documentation beyond README
│   ├── detection-approach.md   # How WiFi promiscuous + BLE detection works
│   ├── signatures.md           # Signature provenance and update process
│   └── hardware.md             # Wiring, hardware selection, QEMU/sim notes
│
├── notes/                      # Planning and research (not shipped to users)
│   ├── project-plan.md         # Milestone tracker
│   ├── project-scope.md        # Scope boundaries and locked decisions
│   ├── source-feature-map.md   # Feature comparison from reference implementations
│   ├── repo-architecture.md    # This file
│   └── readme-plan.md          # README planning notes
│
└── references/                 # Reference implementations (read-only, vendored)
    ├── flock-you/              # Arduino/PlatformIO project (Xiao ESP32 S3)
    └── Flock-Safety-Trap-Shooter-Sniffer-Alarm/  # ESP-IDF sniffer (M5NanoC6)
```

---

## Rationale

### `firmware/` — Arduino IDE sketch
All files that belong to the Arduino sketch live here. Arduino IDE requires the `.ino` file to be in a folder with the same name (`firmware/firmware.ino`). Header files in the same directory are automatically visible to the sketch.

`config.h` is included by the sketch and all future `.ino`/`.h` files. Feature flags (`#define FEATURE_WIFI_SCAN`, etc.) live there so individual features can be compiled in/out without modifying the main sketch. This keeps milestone transitions clean.

`wifi_signatures.h` and `ble_signatures.h` are standalone headers included by the sketch — no library installation needed.

**Arduino IDE setup:** Install ESP32 board support via Boards Manager ("esp32 by Espressif Systems"). Then install NimBLE-Arduino and ArduinoJson via Library Manager. Select board "XIAO_ESP32S3".

**arduino-cli equivalent:**
```bash
arduino-cli compile --fqbn esp32:esp32:XIAO_ESP32S3 firmware
arduino-cli upload  --fqbn esp32:esp32:XIAO_ESP32S3 --port /dev/ttyACM0 firmware
arduino-cli monitor --port /dev/ttyACM0 --config baudrate=115200
```

### `signatures/` — Python tools only
`signatures.json` is the authoritative human-readable signature list consumed by Python tools. The C headers in `firmware/` are the firmware-side representation of the same data. When signatures are updated, both need to stay in sync. A future `tools/update_signatures.py` will regenerate the C headers from the JSON.

### `tools/` — Python utilities and dashboard
Anything that runs on the host machine (laptop, Pi, etc.) lives here. The dashboard is a subdirectory, not a top-level peer to `src/`, because it is one tool among several rather than the primary product.

### `docs/` — user-facing documentation
More detailed than the README. Explains the detection approach, signature provenance, and hardware setup in depth. The README links to these files rather than duplicating content.

### `notes/` — planning and research
Not intended for end users. These files track decisions, comparisons, and plans. They stay in the repo for continuity but are not linked from the README.

### `references/` — read-only reference implementations
Vendored copies of the two reference projects. They are not modified. They are not built by default. Their `platformio.ini`/`idf.py` configs are independent of the root `platformio.ini`. They exist so the reference code is always available locally without a network dependency.

---

## What goes where: quick reference

| Thing | Location |
|---|---|
| Firmware entry point | `firmware/firmware.ino` |
| Feature flags, pins, timing | `firmware/config.h` |
| MAC prefix list (firmware) | `firmware/wifi_signatures.h` |
| SSID pattern list (firmware) | `firmware/wifi_signatures.h` |
| BLE name/MAC list (firmware) | `firmware/ble_signatures.h` |
| MAC/SSID/BLE patterns (Python) | `signatures/signatures.json` |
| Flask dashboard | `tools/dashboard/` |
| Serial log consumer | `tools/serial_reader.py` |
| Export utilities | `tools/export/` |
| Detection approach explanation | `docs/detection-approach.md` |
| Hardware/wiring/QEMU notes | `docs/hardware.md` |
| Milestone tracker | `notes/project-plan.md` |
| Reference implementations | `references/` (never modify) |
