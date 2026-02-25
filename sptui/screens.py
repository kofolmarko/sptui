from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Label, ListItem, ListView, Static
from textual import work

from .client import SpotifyClient


HELP_TEXT = """\
 Keyboard Shortcuts
 ──────────────────────────────────────
 Space      Play / Pause
 n          Next track
 p          Previous track
 s          Toggle shuffle
 r          Cycle repeat (off/context/track)
 +          Volume up 10%
 -          Volume down 10%
 /          Focus search bar
 Enter      Play selected item
 d          Select playback device
 ↑ / ↓     Navigate lists and tables
 ?          Toggle this help screen
 q          Quit
 ──────────────────────────────────────
 Press any key to close
"""

_DEVICE_ICONS = {
    "Computer": "💻",
    "Smartphone": "📱",
    "Speaker": "🔊",
    "TV": "📺",
    "GameConsole": "🎮",
    "CastAudio": "🔊",
    "CastVideo": "📺",
    "AVR": "🔊",
    "STB": "📺",
    "AudioDongle": "🔊",
    "Unknown": "❓",
}


class HelpScreen(ModalScreen):
    BINDINGS = [Binding("escape", "dismiss", "Close")]

    DEFAULT_CSS = """
    HelpScreen { align: center middle; }
    #help-dialog {
        background: $surface;
        border: thick $primary;
        padding: 1 2;
        width: 52;
        height: auto;
    }
    #help-title {
        text-align: center;
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Static(id="help-dialog"):
            yield Label("sptui — Help", id="help-title")
            yield Static(HELP_TEXT)

    def on_key(self, event) -> None:
        self.dismiss()


class DeviceScreen(ModalScreen):
    BINDINGS = [Binding("escape", "dismiss", "Close")]

    DEFAULT_CSS = """
    DeviceScreen { align: center middle; }
    #device-dialog {
        background: $surface;
        border: thick $primary;
        padding: 1 2;
        width: 58;
        height: auto;
        max-height: 24;
    }
    #device-title {
        text-align: center;
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }
    #device-list { height: auto; max-height: 12; border: none; }
    #device-hint { color: $text-muted; margin-top: 1; }
    """

    def __init__(self, client: SpotifyClient, **kwargs) -> None:
        super().__init__(**kwargs)
        self._client = client
        self._devices: list[dict] = []

    def compose(self) -> ComposeResult:
        with Vertical(id="device-dialog"):
            yield Label("Select Playback Device", id="device-title")
            yield ListView(id="device-list")
            yield Static("Loading devices…", id="device-hint")

    def on_mount(self) -> None:
        self._load_devices()

    @work(thread=True)
    def _load_devices(self) -> None:
        try:
            devices = self._client.get_devices()
            self.app.call_from_thread(self._populate, devices)
        except Exception as e:
            self.app.call_from_thread(
                self.query_one("#device-hint", Static).update, f"Error: {e}"
            )

    def _populate(self, devices: list[dict]) -> None:
        self._devices = devices
        lv = self.query_one("#device-list", ListView)
        lv.clear()

        for device in devices:
            icon = _DEVICE_ICONS.get(device.get("type", "Unknown"), "❓")
            name = device.get("name", "Unknown")
            suffix = (" ✓" if device.get("is_active") else "") + (
                " [restricted]" if device.get("is_restricted") else ""
            )
            lv.append(ListItem(Label(f"{icon}  {name}{suffix}")))

        if devices:
            self.query_one("#device-hint", Static).update(
                "↑/↓ navigate · Enter select · Esc cancel"
            )
            lv.focus()
        else:
            self.query_one("#device-hint", Static).update(
                "No devices found.\n"
                "Open the Spotify app (you can minimize it to the system tray),\n"
                "then press 'd' again."
            )

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        idx = event.list_view.index
        if idx is None or idx >= len(self._devices):
            return
        device = self._devices[idx]
        if not device.get("is_restricted"):
            self._transfer(device["id"], device.get("name", "device"))

    @work(thread=True)
    def _transfer(self, device_id: str, name: str) -> None:
        try:
            self._client.transfer_playback(device_id, force_play=False)
            self.app.call_from_thread(self.app.notify, f"Switched to: {name}")
            self.app.call_from_thread(self.dismiss)
        except Exception as e:
            self.app.call_from_thread(self.app.notify, str(e), severity="error")
            self.app.call_from_thread(self.dismiss)
