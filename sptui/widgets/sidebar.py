from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.message import Message
from textual.reactive import reactive
from textual.widgets import Input, Label, ListItem, ListView, Static


class SearchRequested(Message):
    """Posted when the user submits a search query."""

    def __init__(self, query: str) -> None:
        super().__init__()
        self.query = query


class ViewRequested(Message):
    """Posted when the user selects a built-in view (recently played, liked songs)."""

    def __init__(self, view: str) -> None:
        super().__init__()
        self.view = view  # "recently_played" | "liked_songs"


class PlaylistRequested(Message):
    """Posted when the user selects a playlist."""

    def __init__(self, playlist_id: str, playlist_name: str) -> None:
        super().__init__()
        self.playlist_id = playlist_id
        self.playlist_name = playlist_name


class Sidebar(Vertical):
    """Navigation sidebar with search, built-in views, and playlist list."""

    DEFAULT_CSS = """
    Sidebar {
        width: 22;
        border-right: solid $surface-darken-1;
        padding: 0;
    }

    #sidebar-header {
        background: $surface-darken-1;
        color: $primary;
        text-style: bold;
        padding: 0 1;
        height: 1;
    }

    #search-input {
        margin: 0;
        border: none;
        border-bottom: solid $surface-darken-1;
    }

    #nav-section-label {
        color: $text-muted;
        text-style: bold;
        padding: 0 1;
        height: 1;
        margin-top: 1;
    }

    #playlist-section-label {
        color: $text-muted;
        text-style: bold;
        padding: 0 1;
        height: 1;
        margin-top: 1;
    }

    #nav-list {
        height: auto;
        border: none;
        padding: 0;
    }

    #playlist-list {
        border: none;
        padding: 0;
    }

    ListView > ListItem {
        padding: 0 1;
    }

    ListView > ListItem.--highlight {
        background: $accent 20%;
    }
    """

    playlists: reactive[list[dict]] = reactive([], recompose=True)

    def compose(self) -> ComposeResult:
        yield Static("sptui", id="sidebar-header")
        yield Input(placeholder="/ Search...", id="search-input")
        yield Static("NAVIGATION", id="nav-section-label")
        yield ListView(
            ListItem(Label("Recently Played"), id="item-recently-played"),
            ListItem(Label("Liked Songs"), id="item-liked-songs"),
            id="nav-list",
        )
        yield Static("PLAYLISTS", id="playlist-section-label")
        playlist_items = [
            ListItem(Label(p.get("name", "Untitled")), id=f"playlist-{p['id']}")
            for p in self.playlists
        ]
        yield ListView(*playlist_items, id="playlist-list")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        query = event.value.strip()
        if query:
            self.post_message(SearchRequested(query))
            event.input.clear()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        item_id = event.item.id or ""
        if item_id == "item-recently-played":
            self.post_message(ViewRequested("recently_played"))
        elif item_id == "item-liked-songs":
            self.post_message(ViewRequested("liked_songs"))
        elif item_id.startswith("playlist-"):
            playlist_id = item_id[len("playlist-"):]
            # Find playlist name
            name = next(
                (p.get("name", "Untitled") for p in self.playlists if p["id"] == playlist_id),
                "Playlist",
            )
            self.post_message(PlaylistRequested(playlist_id, name))

    def focus_search(self) -> None:
        self.query_one("#search-input", Input).focus()

    def set_playlists(self, playlists: list[dict]) -> None:
        self.playlists = playlists
