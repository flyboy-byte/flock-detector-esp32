# README Plan

## What to carry over from each reference

### From flock-you
- Multi-method detection breakdown (WiFi promiscuous, BLE, MAC prefix, SSID pattern, device name) — these are the actual techniques this project will use
- Audio alert system concept and GPIO wiring (useful, hardware-specific but reproducible)
- JSON detection output format — real structure documented in code, worth showing
- Web dashboard concept: Flask + SocketIO, GPS integration, CSV/KML export — keep the concept, not the prose
- Reference to deflock.me datasets for signature provenance
- Credit to the project and its authors

### From Flock-Safety-Trap-Shooter-Sniffer-Alarm
- Dual-band scanning (2.4 GHz channels 1–13 + 5 GHz channels 36/40/44/48/149/153/157/161/165) — the sniffer does this; flock-you does not
- Minimal single-file ESP-IDF approach as a design contrast
- Credit to Jon Gaines / GainSec and dj1ch

---

## What NOT to copy

- Commercial product language: "Oui-Spy device available at colonelpanic.tech", "Purchase Information", "available exclusively at"
- "Professional surveillance camera detection" — marketing copy
- "AutoPwn coming 09/27/25" / exploit tool integration — GainSec's separate project, not ours
- Troubleshooting sections specific to the old hardware setups
- Support and community sections that belong to those projects
- Any claim to be the same project or a continuation of either

---

## What this repo can honestly claim right now

- Two reference implementations have been vendored, read, and understood
- Detection patterns (MAC prefixes, SSID strings, BLE names) are extracted from real device data (deflock.me datasets, GainSec research)
- Target hardware is decided: Xiao ESP32 S3
- Architecture is planned: WiFi promiscuous + BLE, serial JSON output, Flask dashboard
- The reference code is working on its original hardware — this project is a port/rework, not a from-scratch invention

## What must wait until firmware actually exists

- Any claim of detecting Flock Safety cameras
- Detection range or performance numbers
- "Works with" anything
- Dashboard live demo / screenshot
- Comparison vs. reference implementations

---

## New project identity

A personal, practical toolkit for passively detecting Flock Safety ALPR cameras and similar roadside surveillance infrastructure. Passive/receive-only. Focused on detection, logging, GPS tagging, and signature analysis. ESP32-S3 is the first hardware target; Linux laptop, Raspberry Pi, and mobile field logging are on the roadmap. Not a commercial product. Not affiliated with either reference project. Builds on their work with credit.

---

## Safety/legal framing

Keep it short and factual:
- Passive/receive-only — no packet injection or transmission
- WiFi promiscuous mode is legal for receive-only in most jurisdictions, but verify locally
- Don't use detection data to track individuals
- A one-paragraph section, not a legal disclaimer wall

---

## README sections

1. **What this is** — 2–3 sentences, honest project description
2. **What this is not** — short list (not a commercial product, not an exploit tool, not tested yet)
3. **Background** — why Flock Safety / ALPR, deflock.me context, what these cameras do
4. **Current status** — honest table or list: what exists, what's in progress, what's planned
5. **Repository layout** — quick tree with descriptions
6. **How it works** — detection techniques (WiFi promiscuous, BLE, MAC/SSID/name patterns, dual-band scanning)
7. **Planned modules** — ESP32-S3 firmware, Python dashboard, future targets
8. **Roadmap** — milestone list
9. **Hardware** — ESP32-S3 target, wiring, buzzer pin
10. **Building (reference code)** — commands for both reference projects while port is in progress
11. **Credits** — flock-you authors, GainSec/Jon Gaines, deflock.me, dj1ch
12. **Legal/safety** — one paragraph
