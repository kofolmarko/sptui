from __future__ import annotations

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import DataTable
from textual import work

from .client import SpotifyClient
from .screens import DeviceScreen, HelpScreen
from .widgets.main_panel import MainPanel
from .widgets.now_playing import NowPlayingBar
from .widgets.sidebar import (
    PlaylistRequested,
    SearchRequested,
    Sidebar,
    ViewRequested,
)


class SptApp(App):
    """Spotify TUI client."""

    TITLE = "sptui"

    CSS = """
    Screen {
        layout: vertical;
    }

    #body {
        layout: horizontal;
        height: 1fr;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("question_mark", "help", "Help", key_display="?"),
        Binding("space", "play_pause", "Play/Pause", show=False),
        Binding("n", "next_track", "Next", show=False),
        Binding("p", "prev_track", "Prev", show=False),
        Binding("s", "shuffle", "Shuffle", show=False),
        Binding("r", "repeat", "Repeat", show=False),
        Binding("plus", "volume_up", "Vol+", show=False),
        Binding("minus", "volume_down", "Vol-", show=False),
        Binding("slash", "focus_search", "Search", show=False),
        Binding("d", "devices", "Devices", show=False),
    ]

    def __init__(self, client: SpotifyClient, config: dict, **kwargs) -> None:
        super().__init__(**kwargs)
        self._client = client
        self._config = config

    def compose(self) -> ComposeResult:
        from textual.widgets import Footer, Header
        from textual.containers import Horizontal

        yield Header()
        with Horizontal(id="body"):
            yield Sidebar(id="sidebar")
            yield MainPanel(self._client, id="main-panel")
        yield NowPlayingBar(self._client, id="now-playing")
        yield Footer()

    def on_mount(self) -> None:
        self._load_playlists()

    @work(thread=True)
    def _load_playlists(self) -> None:
        try:
            playlists = self._client.get_playlists()
            self.call_from_thread(self._set_playlists, playlists)
        except Exception as e:
            self.call_from_thread(self.notify, f"Failed to load playlists: {e}", severity="warning")

    def _set_playlists(self, playlists: list[dict]) -> None:
        self.query_one("#sidebar", Sidebar).set_playlists(playlists)

    # ── Message handlers ─────────────────────────────────────────────────────

    def on_search_requested(self, event: SearchRequested) -> None:
        self.query_one("#main-panel", MainPanel).load_search(event.query)

    def on_view_requested(self, event: ViewRequested) -> None:
        panel = self.query_one("#main-panel", MainPanel)
        if event.view == "recently_played":
            panel.load_recently_played()
        elif event.view == "liked_songs":
            panel.load_liked_songs()

    def on_playlist_requested(self, event: PlaylistRequested) -> None:
        self.query_one("#main-panel", MainPanel).load_playlist(
            event.playlist_id, event.playlist_name
        )

    # ── Actions ───────────────────────────────────────────────────────────────

    def action_help(self) -> None:
        self.push_screen(HelpScreen())

    def action_devices(self) -> None:
        self.push_screen(DeviceScreen(self._client))

    def action_play_pause(self) -> None:
        self.query_one("#now-playing", NowPlayingBar).action_play_pause()

    def action_next_track(self) -> None:
        self.query_one("#now-playing", NowPlayingBar).action_next()

    def action_prev_track(self) -> None:
        self.query_one("#now-playing", NowPlayingBar).action_prev()

    def action_volume_up(self) -> None:
        self.query_one("#now-playing", NowPlayingBar).action_volume_up()

    def action_volume_down(self) -> None:
        self.query_one("#now-playing", NowPlayingBar).action_volume_down()

    def action_shuffle(self) -> None:
        self.query_one("#now-playing", NowPlayingBar).action_shuffle()

    def action_repeat(self) -> None:
        self.query_one("#now-playing", NowPlayingBar).action_repeat()

    def action_focus_search(self) -> None:
        self.query_one("#sidebar", Sidebar).focus_search()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        panel = self.query_one("#main-panel", MainPanel)
        track = panel.get_selected_track()
        if track:
            uri = track.get("uri")
            if uri:
                np = self.query_one("#now-playing", NowPlayingBar)
                np.play_track(uri, panel._context_uri)
