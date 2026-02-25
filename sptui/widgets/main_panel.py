from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import ContentSwitcher, DataTable, Label, Static
from textual import work

from ..client import SpotifyClient, format_track


COLUMNS = ("Title", "Artist", "Album", "Duration")


class MainPanel(Vertical):
    """Main content area with a DataTable for tracks."""

    DEFAULT_CSS = """
    MainPanel {
        width: 1fr;
        height: 1fr;
    }

    #panel-header {
        height: 1;
        background: $surface-darken-1;
        color: $primary;
        text-style: bold;
        padding: 0 1;
    }

    #track-table {
        height: 1fr;
    }

    #empty-label {
        content-align: center middle;
        height: 1fr;
        color: $text-muted;
    }
    """

    def __init__(self, client: SpotifyClient, **kwargs) -> None:
        super().__init__(**kwargs)
        self._client = client
        self._tracks: list[dict] = []
        self._context_uri: str | None = None
        self._current_view = "empty"

    def compose(self) -> ComposeResult:
        yield Static("sptui", id="panel-header")
        with ContentSwitcher(initial="empty-label"):
            yield Label("Select a view from the sidebar", id="empty-label")
            yield DataTable(id="track-table", zebra_stripes=True, cursor_type="row")

    def on_mount(self) -> None:
        table = self.query_one("#track-table", DataTable)
        table.add_columns(*COLUMNS)

    def _set_header(self, title: str) -> None:
        self.query_one("#panel-header", Static).update(title)

    def _show_table(self) -> None:
        self.query_one(ContentSwitcher).current = "track-table"

    def _show_empty(self, message: str = "No results") -> None:
        self.query_one("#empty-label", Label).update(message)
        self.query_one(ContentSwitcher).current = "empty-label"

    def _populate_table(self, tracks: list[dict]) -> None:
        self._tracks = [t for t in tracks if t]
        table = self.query_one("#track-table", DataTable)
        table.clear()
        if not self._tracks:
            self._show_empty("No tracks found")
            return
        for track in self._tracks:
            name, artist, album, duration = format_track(track)
            table.add_row(name, artist, album, duration)
        self._show_table()

    # ── Public load methods (called from app) ────────────────────────────────

    def load_recently_played(self) -> None:
        self._set_header("Recently Played")
        self._context_uri = None
        self._fetch_recently_played()

    @work(thread=True)
    def _fetch_recently_played(self) -> None:
        try:
            tracks = self._client.get_recently_played()
            self.app.call_from_thread(self._populate_table, tracks)
        except Exception as e:
            self.app.call_from_thread(self._show_empty, f"Error: {e}")

    def load_liked_songs(self) -> None:
        self._set_header("Liked Songs")
        self._context_uri = None
        self._fetch_liked_songs()

    @work(thread=True)
    def _fetch_liked_songs(self) -> None:
        try:
            tracks = self._client.get_liked_songs()
            self.app.call_from_thread(self._populate_table, tracks)
        except Exception as e:
            self.app.call_from_thread(self._show_empty, f"Error: {e}")

    def load_playlist(self, playlist_id: str, playlist_name: str) -> None:
        self._set_header(f"Playlist: {playlist_name}")
        self._context_uri = f"spotify:playlist:{playlist_id}"
        self._fetch_playlist(playlist_id)

    @work(thread=True)
    def _fetch_playlist(self, playlist_id: str) -> None:
        try:
            tracks = self._client.get_playlist_tracks(playlist_id)
            self.app.call_from_thread(self._populate_table, tracks)
        except Exception as e:
            self.app.call_from_thread(self._show_empty, f"Error: {e}")

    def load_search(self, query: str) -> None:
        self._set_header(f"Search: {query}")
        self._context_uri = None
        self._fetch_search(query)

    @work(thread=True)
    def _fetch_search(self, query: str) -> None:
        try:
            tracks = self._client.search(query)
            self.app.call_from_thread(self._populate_table, tracks)
        except Exception as e:
            self.app.call_from_thread(self._show_empty, f"Error: {e}")

    def get_selected_track(self) -> dict | None:
        """Return the track dict at the current cursor row, or None."""
        table = self.query_one("#track-table", DataTable)
        if not self._tracks or table.cursor_row < 0:
            return None
        try:
            return self._tracks[table.cursor_row]
        except IndexError:
            return None
