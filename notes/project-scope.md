# Project Scope

What this project is, what it is not, and what decisions are locked vs. open.

---

## What this project is

A personal, passive detection toolkit for identifying Flock Safety ALPR cameras and similar roadside surveillance infrastructure by their wireless signatures. The firmware runs on an ESP32-S3 and outputs structured detection data over serial. The tools layer (Python) consumes that data for logging, analysis, and export.

The goal is to know when you're near surveillance infrastructure and to build a personal log of where it is.

---

## What this project is not

- Not a commercial product
- Not an exploit, jammer, or active attacker
- Not a fork or continuation of flock-you or the sniffer-alarm — it's a new project that studied both
- Not a real-time threat response system — it's a logging/detection tool
- Not dependent on either reference project being maintained

---

## Scope boundaries

### In scope
- ESP32-S3 firmware for passive WiFi and BLE detection
- Serial output of structured detection JSON
- Python tooling for consuming and analyzing that output
- Signature management (MAC prefixes, SSID patterns, BLE names)
- GPS integration for location tagging
- CSV and KML export

### Out of scope (firmware)
- Web dashboard (Python tools layer only)
- OUI database lookup (Python only)
- Persistent storage on-device (SD card is optional and late)
- Display output (optional, late milestone)

### Out of scope (entire project)
- Tracking individuals
- Active injection or transmission of any kind
- Integration with GainSec's exploit tooling
- Real-time alerting infrastructure or notifications

---

## Locked decisions

- **Primary target board:** Xiao ESP32 S3 — small, dual radio, USB-C, 8 MB flash
- **Firmware framework:** Arduino via PlatformIO — not bare ESP-IDF (easier NimBLE, simpler build)
- **Serial baud rate:** 115200
- **Output format:** JSON, one object per line, over USB serial
- **Signature storage:** C header files in `signatures/` for firmware; mirrored as JSON in `signatures/` for tooling
- **Python version target:** 3.10+
- **Channel hop interval:** 2500 ms (matches both reference implementations)

## Open decisions

- Whether to add promiscuous mode at all (Milestone 6 is conditional on Milestone 5 results)
- SD card support (deferred to Milestone 10)
- OLED display (deferred, optional)
- Whether to port the full flock-you dashboard or write a simpler one
- Future hardware targets (Linux, Raspberry Pi, mobile) — architecture should not preclude them
