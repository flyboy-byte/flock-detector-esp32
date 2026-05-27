"""Flock Safety detection TUI.

Usage:
    python tools/tui.py                                 # no auto-connect
    python tools/tui.py --port /dev/ttyACM0             # auto-connect ESP32
    python tools/tui.py --port /dev/ttyACM0 --gps /dev/ttyUSB0
    python tools/tui.py --demo                          # fake detections
    python tools/tui.py --demo --replay captures/log.json
"""

from __future__ import annotations

import argparse
import json
import sys
import threading
from pathlib import Path

# Make tools/ importable regardless of working directory
sys.path.insert(0, str(Path(__file__).parent))

import serial.tools.list_ports
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, DataTable, Footer, Header, Label, Select, Static

import demo as demo_mod
from export import export_csv, export_deflock, export_kml
from gps_reader import GPSReader
from serial_reader import SerialReader, parse_detection
from store import DetectionStore


def _port_options() -> list[tuple[str, str]]:
    ports = serial.tools.list_ports.comports()
    return [(p.device, p.device) for p in ports] if ports else [("(no ports found)", "")]


class FlockTUI(App):
    CSS = """
    Screen { layout: vertical; }

    #conn-bar {
        height: 3;
        background: $surface;
        border-bottom: solid $primary-darken-2;
        padding: 0 1;
    }
    #esp32-col, #gps-col {
        width: 1fr;
        align: left middle;
    }
    #esp32-col Label, #gps-col Label {
        width: 6;
        color: $text-muted;
    }
    #esp32-select, #gps-select {
        width: 22;
    }
    #esp32-btn, #gps-btn {
        min-width: 11;
        margin-left: 1;
    }

    #detection-table { height: 1fr; }

    #gps-bar {
        height: 1;
        background: $surface;
        border-top: solid $primary-darken-2;
        padding: 0 1;
        color: $text-muted;
    }

    #action-bar {
        height: 3;
        background: $surface;
        border-top: solid $primary-darken-2;
        align: center middle;
        padding: 0 1;
    }
    #action-bar Button { margin: 0 1; min-width: 14; }
    #btn-clear { }
    """

    BINDINGS = [
        Binding("c", "export_csv", "CSV"),
        Binding("k", "export_kml", "KML"),
        Binding("d", "export_deflock", "Deflock"),
        Binding("x", "clear", "Clear"),
        Binding("r", "refresh_ports", "Refresh ports"),
        Binding("q", "quit", "Quit"),
    ]

    TITLE = "flock-detector-esp32"
    SUB_TITLE = "0 detected"

    def __init__(self, args: argparse.Namespace) -> None:
        super().__init__()
        self.args = args
        self.store = DetectionStore()
        self.gps = GPSReader()
        self.reader = SerialReader(self.store, self.gps)

    # ── Layout ────────────────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="conn-bar"):
            with Horizontal(id="esp32-col"):
                yield Label("ESP32")
                yield Select(_port_options(), id="esp32-select", prompt="select port")
                yield Button("Connect", id="esp32-btn", variant="primary")
            with Horizontal(id="gps-col"):
                yield Label("GPS")
                yield Select(_port_options(), id="gps-select", prompt="select port")
                yield Button("Connect", id="gps-btn")
        yield DataTable(id="detection-table", zebra_stripes=True, cursor_type="row")
        yield Static("GPS: not connected", id="gps-bar")
        with Horizontal(id="action-bar"):
            yield Button("Export CSV  [c]", id="btn-csv")
            yield Button("Export KML  [k]", id="btn-kml")
            yield Button("Deflock  [d]", id="btn-deflock")
            yield Button("Clear  [x]", id="btn-clear", variant="warning")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_column("MAC", key="mac", width=19)
        table.add_column("Type", key="proto", width=13)
        table.add_column("RSSI", key="rssi", width=8)
        table.add_column("GPS", key="gps", width=4)
        table.add_column("Seen", key="seen", width=6)
        table.add_column("First seen", key="first_seen", width=10)

        self.reader.on_detection = lambda d, is_new: self.call_from_thread(
            self._on_detection, d, is_new
        )
        self.gps.on_fix = lambda fix: self.call_from_thread(self._on_gps_fix, fix)

        if self.args.demo:
            self._start_demo()
        elif self.args.port:
            self._connect_esp32(self.args.port)

        if self.args.gps:
            self._connect_gps(self.args.gps)

    # ── Connection helpers ────────────────────────────────────────────────────

    def _connect_esp32(self, port: str) -> None:
        try:
            self.reader.connect(port)
            self.notify(f"ESP32 connected on {port}")
            btn = self.query_one("#esp32-btn", Button)
            btn.label = "Disconnect"
            btn.variant = "error"
        except Exception as e:
            self.notify(f"ESP32 connect failed: {e}", severity="error")

    def _disconnect_esp32(self) -> None:
        self.reader.disconnect()
        btn = self.query_one("#esp32-btn", Button)
        btn.label = "Connect"
        btn.variant = "primary"

    def _connect_gps(self, port: str) -> None:
        try:
            self.gps.connect(port)
            self.notify(f"GPS connected on {port}")
            self.query_one("#gps-btn", Button).label = "Disconnect"
        except Exception as e:
            self.notify(f"GPS connect failed: {e}", severity="error")

    def _disconnect_gps(self) -> None:
        self.gps.disconnect()
        self.query_one("#gps-btn", Button).label = "Connect"
        self.query_one("#gps-bar", Static).update("GPS: disconnected")

    def _start_demo(self) -> None:
        if self.args.replay:
            t = threading.Thread(
                target=demo_mod.replay,
                args=(self.args.replay, self._ingest_line),
                daemon=True,
            )
        else:
            t = threading.Thread(
                target=demo_mod.generate,
                args=(self._ingest_line,),
                daemon=True,
            )
        t.start()
        self.notify("Demo mode — no hardware needed", severity="information")
        self.sub_title = "DEMO — 0 detected"

    def _ingest_line(self, line: str) -> None:
        """Feed a raw JSON line into the store (used by demo mode)."""
        try:
            data = json.loads(line)
            det = parse_detection(data, self.gps)
            if det:
                d, is_new = self.store.add_or_update(det)
                self.call_from_thread(self._on_detection, d, is_new)
        except Exception:
            pass

    # ── Callbacks from background threads ─────────────────────────────────────

    def _on_detection(self, det, is_new: bool) -> None:
        table = self.query_one(DataTable)
        count = self.store.count()
        prefix = "DEMO — " if self.args.demo else ""
        self.sub_title = f"{prefix}{count} detected"

        gps_icon = "✓" if det.lat is not None else "✗"

        if is_new:
            table.add_row(
                det.mac,
                det.protocol,
                f"{det.rssi} dBm",
                gps_icon,
                str(det.seen_count),
                det.first_seen.strftime("%H:%M:%S"),
                key=det.mac,
            )
        else:
            table.update_cell(det.mac, "rssi", f"{det.rssi} dBm")
            table.update_cell(det.mac, "gps", gps_icon)
            table.update_cell(det.mac, "seen", str(det.seen_count))

    def _on_gps_fix(self, fix) -> None:
        lat_dir = "N" if fix.lat >= 0 else "S"
        lon_dir = "E" if fix.lon >= 0 else "W"
        quality = "good" if fix.fix_quality >= 1 else "no fix"
        self.query_one("#gps-bar", Static).update(
            f"GPS  {abs(fix.lat):.5f}°{lat_dir}  {abs(fix.lon):.5f}°{lon_dir}"
            f"  alt {fix.alt:.0f}m  sats {fix.satellites}  fix: {quality}"
        )

    # ── Button / action handlers ──────────────────────────────────────────────

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "esp32-btn":
            if self.reader.connected:
                self._disconnect_esp32()
            else:
                port = self.query_one("#esp32-select", Select).value
                if port and port is not Select.BLANK:
                    self._connect_esp32(str(port))
        elif bid == "gps-btn":
            if self.gps.connected:
                self._disconnect_gps()
            else:
                port = self.query_one("#gps-select", Select).value
                if port and port is not Select.BLANK:
                    self._connect_gps(str(port))
        elif bid == "btn-csv":
            self.action_export_csv()
        elif bid == "btn-kml":
            self.action_export_kml()
        elif bid == "btn-deflock":
            self.action_export_deflock()
        elif bid == "btn-clear":
            self.action_clear()

    def action_export_csv(self) -> None:
        detections = self.store.all()
        if not detections:
            self.notify("No detections to export", severity="warning")
            return
        path = export_csv(detections)
        self.notify(f"CSV → {path}")

    def action_export_kml(self) -> None:
        detections = self.store.all()
        if not detections:
            self.notify("No detections to export", severity="warning")
            return
        path = export_kml(detections)
        self.notify(f"KML → {path}")

    def action_export_deflock(self) -> None:
        detections = self.store.all()
        gps_count = sum(1 for d in detections if d.lat is not None)
        if not gps_count:
            self.notify("No GPS-tagged detections for deflock export", severity="warning")
            return
        path = export_deflock(detections)
        self.notify(f"Deflock → {path}  ({gps_count} records)")

    def action_clear(self) -> None:
        self.store.clear()
        self.query_one(DataTable).clear()
        prefix = "DEMO — " if self.args.demo else ""
        self.sub_title = f"{prefix}0 detected"

    def action_refresh_ports(self) -> None:
        options = _port_options()
        self.query_one("#esp32-select", Select).set_options(options)
        self.query_one("#gps-select", Select).set_options(options)
        self.notify("Port list refreshed")


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Flock Safety detection TUI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--port", help="ESP32 serial port (e.g. /dev/ttyACM0)")
    parser.add_argument("--gps", help="GPS dongle serial port (e.g. /dev/ttyUSB0)")
    parser.add_argument("--demo", action="store_true", help="Demo mode (no hardware needed)")
    parser.add_argument("--replay", metavar="FILE", help="Replay JSON file in demo mode")
    args = parser.parse_args()

    FlockTUI(args).run()


if __name__ == "__main__":
    main()
