# sptui

A Spotify TUI client for the terminal.

## Requirements

- Python 3.10+
- Spotify Premium account
- Spotify app open on at least one device (desktop, phone, or web player)

## Install

**Linux / macOS**
```bash
curl -fsSL https://raw.githubusercontent.com/kofolmarko/sptui/main/install.sh | bash
```

**Windows (PowerShell)**
```powershell
irm https://raw.githubusercontent.com/kofolmarko/sptui/main/install.ps1 | iex
```

Both scripts install [pipx](https://pipx.pypa.io) if needed, then install sptui into an isolated environment so it doesn't interfere with anything else on your system.

> **Manual install:** `pipx install git+https://github.com/kofolmarko/sptui.git`

## First-time setup

On first launch sptui will walk you through setup — you only do this once:

1. Go to [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard) and log in
2. Click **Create app**, set any name, add `http://127.0.0.1:8080` as a Redirect URI, check **Web API**, and save
3. Copy the **Client ID** and **Client Secret** from app Settings into the prompts
4. A browser window opens for OAuth — log in and authorise
5. Optionally configure an AI provider for natural language commands (see below)

Credentials are saved to `~/.config/sptui/config.json`. Subsequent launches start immediately.

## Usage

Open the Spotify app on any device (you can minimise it to the system tray), then:

```bash
sptui
```

Press `d` to pick which device to play on.

## Keybindings

| Key | Action |
|-----|--------|
| `Space` | Play / Pause |
| `n` | Next track |
| `p` | Previous track |
| `s` | Toggle shuffle |
| `r` | Cycle repeat (off / context / track) |
| `+` / `-` | Volume ±10% |
| `/` | Focus search |
| `Enter` | Play selected item |
| `d` | Select playback device |
| `a` | AI command (natural language) |
| `?` | Help overlay |
| `q` | Quit |

## AI Commands

Press `a` to open the AI command bar and type in plain English:

- *play something chill*
- *skip this track*
- *set volume to 40*
- *turn off shuffle*
- *repeat the current song*
- *play Bohemian Rhapsody*

### Providers

Pick a provider during first-time setup, or edit `~/.config/sptui/config.json` directly:

**Anthropic (Claude)**
```json
"ai": { "provider": "anthropic", "api_key": "sk-ant-...", "model": "claude-opus-4-6" }
```
Get a key at [console.anthropic.com](https://console.anthropic.com). You can also set the `ANTHROPIC_API_KEY` environment variable instead of storing the key in config.

**Ollama (local, no API key)**
```json
"ai": { "provider": "ollama", "base_url": "http://localhost:11434", "model": "llama3.2" }
```
Install Ollama at [ollama.com](https://ollama.com), then `ollama pull llama3.2`. Models with tool-calling support: `llama3.2`, `llama3.1`, `mistral`, `qwen2.5`, `phi4`.

**OpenAI-compatible (OpenAI, Groq, LM Studio, …)**
```json
"ai": { "provider": "openai_compatible", "base_url": "https://api.openai.com", "api_key": "sk-...", "model": "gpt-4o" }
```
