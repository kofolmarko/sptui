from __future__ import annotations

from typing import Any

import spotipy
from spotipy.oauth2 import SpotifyOAuth

from .config import REQUIRED_SCOPES, TOKEN_CACHE


class SpotifyClient:
    """Thin sync wrapper around Spotipy. No Textual imports."""

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str) -> None:
        auth = SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope=REQUIRED_SCOPES,
            cache_path=TOKEN_CACHE,
            open_browser=True,
        )
        self.sp = spotipy.Spotify(auth_manager=auth)

    # ── Playback state ────────────────────────────────────────────────────────

    def get_current_playback(self) -> dict | None:
        """Return current playback state or None if nothing is active."""
        return self.sp.current_playback()

    # ── Controls ──────────────────────────────────────────────────────────────

    def play_pause(self, is_playing: bool) -> None:
        if is_playing:
            self.sp.pause_playback()
        else:
            self.sp.start_playback()

    def next_track(self) -> None:
        self.sp.next_track()

    def prev_track(self) -> None:
        self.sp.previous_track()

    def set_volume(self, volume_pct: int) -> None:
        volume_pct = max(0, min(100, volume_pct))
        self.sp.volume(volume_pct)

    def set_shuffle(self, state: bool) -> None:
        self.sp.shuffle(state)

    def cycle_repeat(self, current: str) -> None:
        """Cycle: off → context → track → off."""
        order = ["off", "context", "track"]
        next_state = order[(order.index(current) + 1) % len(order)]
        self.sp.repeat(next_state)

    def play_track(self, track_uri: str, context_uri: str | None = None) -> None:
        if context_uri:
            self.sp.start_playback(context_uri=context_uri, offset={"uri": track_uri})
        else:
            self.sp.start_playback(uris=[track_uri])

    # ── Devices ───────────────────────────────────────────────────────────────

    def get_devices(self) -> list[dict]:
        result = self.sp.devices()
        return result.get("devices", [])

    def transfer_playback(self, device_id: str, force_play: bool = False) -> None:
        self.sp.transfer_playback(device_id, force_play=force_play)

    # ── Library ───────────────────────────────────────────────────────────────

    def get_liked_songs(self, limit: int = 50) -> list[dict]:
        results = self.sp.current_user_saved_tracks(limit=limit)
        return [item["track"] for item in results.get("items", [])]

    def get_recently_played(self, limit: int = 50) -> list[dict]:
        results = self.sp.current_user_recently_played(limit=limit)
        return [item["track"] for item in results.get("items", [])]

    # ── Playlists ─────────────────────────────────────────────────────────────

    def get_playlists(self, limit: int = 50) -> list[dict]:
        results = self.sp.current_user_playlists(limit=limit)
        return results.get("items", [])

    def get_playlist_tracks(self, playlist_id: str, limit: int = 100) -> list[dict]:
        results = self.sp.playlist_tracks(playlist_id, limit=limit)
        tracks = []
        for item in results.get("items", []):
            if item and item.get("track"):
                tracks.append(item["track"])
        return tracks

    # ── Search ────────────────────────────────────────────────────────────────

    def search(self, query: str, limit: int = 30) -> list[dict]:
        results = self.sp.search(q=query, type="track", limit=limit)
        return results.get("tracks", {}).get("items", [])


def format_duration(ms: int) -> str:
    """Format milliseconds as m:ss."""
    s = ms // 1000
    return f"{s // 60}:{s % 60:02d}"


def format_track(track: dict) -> tuple[str, str, str, str]:
    """Return (name, artist, album, duration) strings."""
    name = track.get("name", "Unknown")
    artists = ", ".join(a["name"] for a in track.get("artists", []))
    album = track.get("album", {}).get("name", "Unknown")
    duration = format_duration(track.get("duration_ms", 0))
    return name, artists, album, duration
