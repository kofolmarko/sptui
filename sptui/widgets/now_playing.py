from __future__ import annotations

import time
import spotipy
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.reactive import reactive
from textual.widgets import Static
from textual import work

from ..client import SpotifyClient, format_duration

_COMMAND_COOLDOWN = 0.5  # seconds between repeated commands


def _is_no_device(exc: Exception) -> bool:
    if isinstance(exc, spotipy.SpotifyException):
        return "NO_ACTIVE_DEVICE" in str(exc) or exc.http_status == 404
    return False


def _is_restriction(exc: Exception) -> bool:
    """Spotify rejects rapid/repeated commands with 403 Restriction violated — expected."""
    if isinstance(exc, spotipy.SpotifyException):
        return exc.http_status == 403 and "Restriction violated" in str(exc)
    return False


class NowPlayingBar(Vertical):
    """Bottom bar showing current track info and playback controls."""

    DEFAULT_CSS = """
    NowPlayingBar {
        height: 4;
        border-top: solid $surface-darken-1;
        padding: 0 1;
    }

    #track-info {
        height: 1;
        color: $text;
    }

    #controls-row {
        height: 1;
    }

    #progress-row {
        height: 1;
    }
    """

    is_playing: reactive[bool] = reactive(False)
    shuffle: reactive[bool] = reactive(False)
    repeat: reactive[str] = reactive("off")
    volume: reactive[int] = reactive(50)
    position_ms: reactive[int] = reactive(0)
    duration_ms: reactive[int] = reactive(0)

    def __init__(self, client: SpotifyClient, **kwargs) -> None:
        super().__init__(**kwargs)
        self._client = client
        self._progress_pct: float = 0.0
        self._last_command_at: float = 0.0

    def _check_cooldown(self) -> bool:
        """Return True and reset timer if enough time has passed; else False."""
        now = time.monotonic()
        if now - self._last_command_at < _COMMAND_COOLDOWN:
            return False
        self._last_command_at = now
        return True

    def compose(self) -> ComposeResult:
        yield Static("No track playing", id="track-info")
        yield Static("[◄◄] [▶] [▶▶]", id="controls-row")
        yield Static("░" * 20 + "  0:00 / 0:00", id="progress-row")

    def on_mount(self) -> None:
        self.set_interval(1.0, self._poll_playback)

    def _poll_playback(self) -> None:
        self.run_worker(self._fetch_playback, thread=True, exclusive=True)

    def _fetch_playback(self) -> None:
        try:
            state = self._client.get_current_playback()
            self.app.call_from_thread(self._update_display, state)
        except Exception:
            pass

    def _update_display(self, state: dict | None) -> None:
        """Update the three Static widgets with current playback state. Must run on main thread."""
        if not state or not state.get("item"):
            self.query_one("#track-info", Static).update("No track playing")
            self.query_one("#controls-row", Static).update("[◄◄] [▶] [▶▶]")
            self.query_one("#progress-row", Static).update("░" * 20 + "  0:00 / 0:00")
            self.is_playing = False
            return

        item = state["item"]
        self.is_playing = state.get("is_playing", False)
        self.shuffle = state.get("shuffle_state", False)
        self.repeat = state.get("repeat_state", "off")
        self.volume = state.get("device", {}).get("volume_percent", 50) or 50
        self.position_ms = state.get("progress_ms", 0) or 0
        self.duration_ms = item.get("duration_ms", 1) or 1
        self._progress_pct = self.position_ms / self.duration_ms

        track_name = item.get("name", "Unknown")
        artist_name = ", ".join(a["name"] for a in item.get("artists", []))
        album_name = item.get("album", {}).get("name", "")

        info = f"♫  {track_name}  ·  {artist_name}"
        if album_name:
            info += f"  ·  {album_name}"
        self.query_one("#track-info", Static).update(info)

        play_icon = "⏸" if self.is_playing else "▶"
        shuffle_icon = "🔀" if self.shuffle else "↔"
        repeat_icon = {"off": "↩", "context": "🔁", "track": "🔂"}.get(self.repeat, "↩")
        self.query_one("#controls-row", Static).update(
            f"[◄◄] [{play_icon}] [▶▶]   {shuffle_icon} {repeat_icon}   Vol: {self.volume}%"
        )

        pos = format_duration(self.position_ms)
        dur = format_duration(self.duration_ms)
        filled = int(self._progress_pct * 20)
        bar = "█" * filled + "░" * (20 - filled)
        self.query_one("#progress-row", Static).update(f"{bar}  {pos} / {dur}")

    # ── Error handling ────────────────────────────────────────────────────────

    def _handle_error(self, e: Exception) -> None:
        """Must run on main thread."""
        if _is_restriction(e):
            return  # Spotify's spam guard — expected, don't bother the user
        if _is_no_device(e):
            self.app.notify(
                "No active Spotify device. Press [b]d[/b] to pick one.",
                severity="warning",
                timeout=6,
            )
        else:
            self.app.notify(str(e), severity="error")

    # ── Playback actions (called from app keybindings) ───────────────────────

    @work(thread=True)
    def action_play_pause(self) -> None:
        if not self._check_cooldown():
            return
        try:
            self._client.play_pause(self.is_playing)
        except Exception as e:
            self.app.call_from_thread(self._handle_error, e)

    @work(thread=True)
    def action_next(self) -> None:
        if not self._check_cooldown():
            return
        try:
            self._client.next_track()
        except Exception as e:
            self.app.call_from_thread(self._handle_error, e)

    @work(thread=True)
    def action_prev(self) -> None:
        if not self._check_cooldown():
            return
        try:
            self._client.prev_track()
        except Exception as e:
            self.app.call_from_thread(self._handle_error, e)

    @work(thread=True)
    def action_volume_up(self) -> None:
        if not self._check_cooldown():
            return
        try:
            self._client.set_volume(self.volume + 10)
        except Exception as e:
            self.app.call_from_thread(self._handle_error, e)

    @work(thread=True)
    def action_volume_down(self) -> None:
        if not self._check_cooldown():
            return
        try:
            self._client.set_volume(self.volume - 10)
        except Exception as e:
            self.app.call_from_thread(self._handle_error, e)

    @work(thread=True)
    def action_shuffle(self) -> None:
        if not self._check_cooldown():
            return
        try:
            self._client.set_shuffle(not self.shuffle)
        except Exception as e:
            self.app.call_from_thread(self._handle_error, e)

    @work(thread=True)
    def action_repeat(self) -> None:
        if not self._check_cooldown():
            return
        try:
            self._client.cycle_repeat(self.repeat)
        except Exception as e:
            self.app.call_from_thread(self._handle_error, e)

    def play_track(self, track_uri: str, context_uri: str | None = None) -> None:
        self._play_track_worker(track_uri, context_uri)

    @work(thread=True)
    def _play_track_worker(self, track_uri: str, context_uri: str | None) -> None:
        try:
            self._client.play_track(track_uri, context_uri)
        except Exception as e:
            self.app.call_from_thread(self._handle_error, e)
