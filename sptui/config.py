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


def _prompt_ai_provider() -> dict | None:
    """Interactive AI provider setup. Returns a config dict or None to skip."""
    print()
    print("AI Commands (optional)")
    print("  Control Spotify with natural language (e.g. 'play something chill')")
    print()
    print("  1. Anthropic (Claude)    — API key from console.anthropic.com")
    print("  2. Ollama (local)        — run models locally, no API key needed")
    print("  3. OpenAI-compatible     — OpenAI, Groq, LM Studio, or any compatible endpoint")
    print("  4. Skip")
    print()

    choice = input("Provider [1/2/3/4]: ").strip()

    if choice == "1":
        api_key = input("Anthropic API key: ").strip()
        if not api_key:
            print("Skipping AI setup.")
            return None
        model = input("Model [claude-opus-4-6]: ").strip() or "claude-opus-4-6"
        return {"provider": "anthropic", "api_key": api_key, "model": model}

    elif choice == "2":
        print("  Ollama must be running locally. Install at https://ollama.com")
        print("  Tool-calling models: llama3.2, llama3.1, mistral, qwen2.5, phi4")
        base_url = input("Ollama base URL [http://localhost:11434]: ").strip() or "http://localhost:11434"
        model = input("Model [llama3.2]: ").strip() or "llama3.2"
        return {"provider": "ollama", "base_url": base_url, "model": model}

    elif choice == "3":
        base_url = input("Base URL (e.g. https://api.openai.com): ").strip()
        if not base_url:
            print("Skipping AI setup.")
            return None
        api_key = input("API key (press Enter if not required): ").strip() or "none"
        model = input("Model (e.g. gpt-4o, llama-3.3-70b-versatile): ").strip()
        if not model:
            print("Skipping AI setup.")
            return None
        return {"provider": "openai_compatible", "base_url": base_url, "api_key": api_key, "model": model}

    return None


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

    ai_config = _prompt_ai_provider()
    if ai_config:
        config["ai"] = ai_config

    with CONFIG_FILE.open("w") as f:
        json.dump(config, f, indent=2)

    print(f"\nConfig saved to {CONFIG_FILE}")
    print("Launching sptui...\n")
    return config
