from __future__ import annotations

import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "sptui"
CONFIG_FILE = CONFIG_DIR / "config.json"
TOKEN_CACHE = str(CONFIG_DIR / ".spotify_token_cache")

REQUIRED_SCOPES = " ".join([
    "user-read-playback-state",
    "user-modify-playback-state",
    "user-read-currently-playing",
    "user-library-read",
    "user-read-recently-played",
    "playlist-read-private",
    "playlist-read-collaborative",
])


def ensure_config() -> dict:
    """Load config, or run first-run prompts to create it."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    if CONFIG_FILE.exists():
        with CONFIG_FILE.open() as f:
            return json.load(f)

    print("sptui — First-time setup")
    print("=========================")
    print()
    print("You need a free Spotify Developer app. Steps:")
    print()
    print("  1. Go to https://developer.spotify.com/dashboard")
    print("     (log in with your regular Spotify account)")
    print()
    print("  2. Click 'Create app'")
    print("     - Name: anything (e.g. 'sptui')")
    print("     - Redirect URI: http://127.0.0.1:8080")
    print("       (use 127.0.0.1 — Spotify rejects 'localhost')")
    print("       (add it under 'Redirect URIs' and click Save)")
    print("     - Check 'Web API', then Save")
    print()
    print("  3. Open your app → Settings to find Client ID and Secret")
    print()

    client_id = input("Client ID: ").strip()
    client_secret = input("Client Secret: ").strip()
    redirect_uri = input("Redirect URI [http://127.0.0.1:8080]: ").strip()
    if not redirect_uri:
        redirect_uri = "http://127.0.0.1:8080"

    config = {
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
    }

    with CONFIG_FILE.open("w") as f:
        json.dump(config, f, indent=2)

    print(f"\nConfig saved to {CONFIG_FILE}")
    print("Launching sptui...\n")
    return config
