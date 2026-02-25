# sptui

A Spotify TUI client for the terminal.

## Requirements

- Spotify Premium account
- Spotify app open on at least one device (desktop, phone, or web player)

## Install

### Binary (no Python required)

Download the latest binary for your platform from [Releases](https://github.com/kofolmarko/sptui/releases).

```bash
# Linux
chmod +x sptui-linux-x86_64 && ./sptui-linux-x86_64

# macOS (Apple Silicon — Intel users can run via Rosetta or install from source)
chmod +x sptui-macos-arm64 && ./sptui-macos-arm64
```

On Windows, download `sptui-windows-x86_64.exe` and run it directly.

### From source (requires Python 3.10+)

```bash
pip install git+https://github.com/kofolmarko/sptui.git
sptui
```

## First-time setup

On first launch sptui will ask for Spotify Developer credentials. You only do this once:

1. Go to [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard) and log in with your Spotify account
2. Click **Create app**, set any name, and add `http://127.0.0.1:8080` as a Redirect URI
3. Check **Web API** and save
4. Copy the **Client ID** and **Client Secret** from the app settings into the prompts
5. A browser window will open for OAuth — log in and authorise

Credentials are saved to `~/.config/sptui/config.json` and the OAuth token is cached, so subsequent launches start immediately.

## Usage

Before launching, open the Spotify app on any device (you can minimise it to the system tray). Then:

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
| `?` | Help overlay |
| `q` | Quit |
