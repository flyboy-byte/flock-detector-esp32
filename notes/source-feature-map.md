# Source Feature Map

Comparison of both reference implementations. Used to decide what to port, what to skip, and what to redesign.

---

## Feature comparison

| Feature | flock-you | sniffer-alarm | This project |
|---|---|---|---|
| WiFi scan (active) | No | No | Milestone 4 |
| WiFi promiscuous mode | Yes — 2.4 GHz only, ch 1–13 | Yes — 2.4 + 5 GHz, specific ch list | Milestone 6 (conditional) |
| Channel hopping | Yes — every 2500 ms | Yes — every 2500 ms | Same timing |
| 5 GHz channels | No | 36/40/44/48/149/153/157/161/165 | Add in M6 |
| SSID pattern matching | Yes — flock/Flock/FLOCK/FS Ext Battery/Penguin/Pigvision | Yes — "flock" only, case-insensitive | Milestone 5 |
| MAC prefix matching | Yes — 19 prefixes (FS/Penguin/Pigvision) | No | Milestone 5 |
| BLE scanning | Yes — NimBLE active scan, 100ms interval | No | Milestone 7 |
| BLE device name matching | Yes — FS Ext Battery/Penguin/Flock/Pigvision | No | Milestone 8 |
| BLE MAC prefix matching | Yes — same list as WiFi | No | Milestone 8 |
| JSON serial output | Yes — verbose, per-detection | No — ESP-IDF log only | Milestone 9–10 |
| Confidence/threat score | Yes — basic (100/85/70 by match type) | No | Milestone 9 (redesign) |
| Audio alert (buzzer) | Yes — boot/detect/heartbeat sequences | No | Optional, behind config flag |
| Range/heartbeat tracking | Yes — 30s timeout, 10s heartbeat | No | Optional |
| Single-shot detection | No — continuous | Yes — halts after first hit | No — continuous preferred |
| Python dashboard | Yes — Flask + SocketIO + GPS | No | Milestone 10 (future tools/) |
| GPS integration | Yes — NMEA, 9600 baud, temporal matching | No | Milestone 10 |
| OUI manufacturer lookup | Yes — oui.txt loaded at startup | No | Milestone 10 (tools) |
| CSV export | Yes | No | tools/ (future) |
| KML export | Yes | No | tools/ (future) |
| Cumulative detection persistence | Yes — pickle | No | tools/ (future) |
| MAC deduplication + count | Yes | No | Milestone 9–10 |
| Serial terminal in dashboard | Yes | No | tools/ (future) |
| Reconnect logic | Yes — 5 retries, 3s delay | No | tools/ (future) |

---

## Signature inventory

### MAC OUI prefixes (from flock-you)

Derived from deflock.me dataset. These represent the first 3 octets of the device MAC.

**Flock Safety WiFi devices:**
`70:c9:4e`, `3c:91:80`, `d8:f3:bc`, `80:30:49`, `14:5a:fc`, `74:4c:a1`, `08:3a:88`, `9c:2f:9d`

**FS Ext Battery devices:**
`58:8e:81`, `cc:cc:cc`, `ec:1b:bd`, `90:35:ea`, `04:0d:84`, `f0:82:c0`, `1c:34:f1`, `38:5b:44`, `94:34:69`, `b4:e3:f9`

**Penguin devices:**
`cc:09:24`, `ed:c7:63`, `e8:ce:56`, `ea:0c:ea`, `d8:8f:14`, `f9:d9:c0`, `f1:32:f9`, `f6:a0:76`, `e4:1c:9e`, `e7:f2:43`, `e2:71:33`, `da:91:a9`, `e1:0e:15`, `c8:ae:87`, `f4:ed:b2`, `d8:bf:b5`, `ee:8f:3c`, `d7:2b:21`, `ea:5a:98`

### WiFi SSID patterns (from flock-you)
`flock`, `Flock`, `FLOCK`, `FS Ext Battery`, `Penguin`, `Pigvision`

Note: flock-you checks these with `strcasestr`, so "flock"/"Flock"/"FLOCK" are redundant — can collapse to one case-insensitive check. The sniffer-alarm already does this correctly with its local `strcasestr`.

### BLE device name patterns (from flock-you)
`FS Ext Battery`, `Penguin`, `Flock`, `Pigvision`

---

## Design decisions for this project

**What we keep as-is:**
- Signature lists (MAC prefixes, SSID patterns, BLE names) — extracted into `signatures/`
- WiFi promiscuous channel hopping timing (2500 ms)
- NimBLE active scan parameters (100ms interval, 99ms window)
- JSON serial output format (simplified but compatible)

**What we change:**
- SSID matching: use single case-insensitive match per logical pattern, not three variants of "flock"
- Start with active WiFi scan (Milestone 4) before adding promiscuous mode — simpler to debug
- Confidence scoring: redesign from the flat 100/85/70 to a proper additive score (see Milestone 9)
- Feature flags in config.h rather than hardcoded `#ifdef` removal

**What we skip for firmware (push to tools/):**
- Dashboard, GPS, OUI lookup, CSV/KML export, persistence, reconnect logic
- These belong in Python tooling, not on the ESP32

**What we skip entirely (for now):**
- Single-shot mode (sniffer-alarm behavior) — not useful for logging
- Exploit tool integration (GainSec's separate project)
- The `cc:cc:cc` prefix — almost certainly a placeholder/test entry, not a real OUI
