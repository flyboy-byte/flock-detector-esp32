# Project Plan

Milestone-based development plan. Checked = code written. Hardware milestones require a physical board.

**Current pause point:** all code through M8 is written. Blocked on hardware for validation.
**Boards on hand:** ESP32-WROOM, ESP32-WROVER (no S3 yet). QEMU/Wokwi being explored.

---

## Milestone 0: Source review and README synthesis ✅
- Inspected both reference implementations
- Created notes/ planning docs
- Drafted initial README

---

## Milestone 1: Repo architecture ✅
- Directory layout established
- Both build systems wired up (Arduino IDE + PlatformIO)

---

## Milestone 2: PlatformIO / Arduino skeleton ✅
- `platformio.ini` with three board envs (xiao_esp32s3, esp32_wroom, esp32_wrover)
- `firmware/config.h` — feature flags, board detection, pin defs
- `src/main.cpp` + `firmware/firmware.ino` — serial boot message skeleton

---

## Milestone 3: Serial boot test 🔲 HARDWARE REQUIRED
**Exit condition:** device prints boot header over USB serial.

- [ ] Flash to WROOM or WROVER (on hand) or get S3
- [ ] `pio device monitor` shows the expected boot header
- [ ] USB CDC works correctly on chosen board

---

## Milestone 4–5: WiFi active scan + signature matching ✅ (code written)
- `firmware/wifi_signatures.h` — 36 MAC prefixes, 4 SSID patterns, 5 GHz channel list
- `firmware/sig_match.h` — shared `sig_match_mac()`, `sig_match_ssid()`, `sig_match_ble_name()`
- `firmware/wifi_scan.h` — `WiFi.scanNetworks()` + dedup cache check + `emit_detection()`
- `firmware/detection_output.h` — ArduinoJson v6 JSON line + `calc_threat_score()`
- `firmware/seen_cache.h` — 64-slot ring buffer, 30-second MAC cooldown

**Hardware validation needed:**
- [ ] Scan fires and produces output
- [ ] Known SSID/MAC triggers detection line

---

## Milestone 6: WiFi promiscuous mode ✅ (code written)
- `firmware/wifi_promisc.h` — `IRAM_ATTR` callback, IE parsing, 2.4 GHz channel hopping
- Interleaves 5 GHz channels on `BOARD_HAS_5GHZ` boards
- `wifi_promisc_pause()` / `wifi_promisc_resume()` around active scan window

**Hardware validation needed:**
- [ ] Callback fires on real 802.11 management traffic
- [ ] Probe request frame offsets correct (byte 24 for IEs — no fixed params)
- [ ] Beacon/probe response offsets correct (byte 36 — 12 B fixed params)
- [ ] Pause/resume interleave with active scan is stable

---

## Milestone 7–8: BLE scan + signature matching ✅ (code written)
- `firmware/ble_signatures.h` — 4 BLE name patterns
- `firmware/ble_scan.h` — NimBLE `AdvertisedDeviceCallbacks`, MAC + name matching

**Hardware validation needed:**
- [ ] NimBLE init works alongside WiFi (coexistence)
- [ ] BLE advertisements seen and matched

---

## Milestone 9: Confidence scoring ✅ (basic)
Current scoring in `detection_output.h`:
- `ssid_match` / `ble_name` → 100
- `mac_prefix` / `ble_mac` → 85
- RSSI > -60 → +5

**Remaining:**
- [ ] Multi-hit bonus: same MAC seen via WiFi + BLE in same session
- [ ] Repeat sighting count factor

---

## Milestone 10: Logging and output ✅ (serial JSON + TUI done)
- Serial JSON: done (`detection_output.h`)
- Python TUI consuming serial JSON: done (`tools/serial_reader.py`)
- GPS tagging in TUI: done (`tools/gps_reader.py`)
- CSV / KML export: done (`tools/export.py`)
- deflock.me export: stub — writes local JSON, no HTTP submission yet

**Remaining:**
- [ ] deflock.me actual HTTP API (research endpoint + auth)
- [ ] SD card logging (firmware side, optional)
- [ ] OLED / e-ink status display (firmware side, optional)

---

## Milestone 11: README refresh after working MVP 🔲
**Exit condition:** README has real serial output examples, tested build instructions.

- [ ] Update status table after first successful flash
- [ ] Add real serial output sample (copy from monitor)
- [ ] Remove "not hardware tested" caveats from validated sections
- [ ] Tag v0.1.0 release

---

## Known risks for first flash

1. **Promiscuous + active scan interleave** — `wifi_promisc_pause/resume` is untested; may need delay or state cleanup around the transition
2. **WiFi + BLE coexistence** — NimBLE and WiFi promiscuous share the radio; ESP-IDF coexistence should handle it but may need tuning
3. **5 GHz in promiscuous mode** — depends on ESP-IDF version in the Arduino core; may not work on all Arduino ESP32 releases
4. **IE frame offsets** — probe request IEs at byte 24, beacon/probe-response at byte 36; live traffic may reveal alignment issues
5. **`strcasestr` availability** — used in `sig_match.h`; available in ESP-IDF libc, same pattern as reference, but worth confirming on first build
