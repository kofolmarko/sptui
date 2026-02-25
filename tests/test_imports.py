"""Smoke test: every module must import without errors."""

from sptui.app import SptApp  # noqa: F401
from sptui.ai import _TOOLS, _openai_tools  # noqa: F401
from sptui.config import ensure_config  # noqa: F401
from sptui.client import SpotifyClient, format_duration, format_track  # noqa: F401
from sptui.screens import HelpScreen, DeviceScreen, AIScreen  # noqa: F401
from sptui.widgets.sidebar import Sidebar  # noqa: F401
from sptui.widgets.now_playing import NowPlayingBar  # noqa: F401
from sptui.widgets.main_panel import MainPanel  # noqa: F401

print("All imports OK")
