from __future__ import annotations

import json
from typing import Any

from .client import SpotifyClient

_TOOLS: list[dict] = [
    {
        "name": "play_pause",
        "description": "Play or pause playback, or toggle the current state.",
        "input_schema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["play", "pause", "toggle"],
                    "description": "play = start playing, pause = stop playing, toggle = flip current state",
                },
            },
            "required": ["action"],
        },
    },
    {
        "name": "next_track",
        "description": "Skip to the next track.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "prev_track",
        "description": "Go back to the previous track.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "set_volume",
        "description": "Set the playback volume to a specific level.",
        "input_schema": {
            "type": "object",
            "properties": {
                "volume": {
                    "type": "integer",
                    "description": "Volume percentage from 0 to 100.",
                },
            },
            "required": ["volume"],
        },
    },
    {
        "name": "set_shuffle",
        "description": "Enable or disable shuffle mode.",
        "input_schema": {
            "type": "object",
            "properties": {
                "enabled": {
                    "type": "boolean",
                    "description": "True to enable shuffle, False to disable.",
                },
            },
            "required": ["enabled"],
        },
    },
    {
        "name": "set_repeat",
        "description": "Set the repeat mode.",
        "input_schema": {
            "type": "object",
            "properties": {
                "mode": {
                    "type": "string",
                    "enum": ["off", "context", "track"],
                    "description": "off = no repeat, context = repeat playlist/album, track = repeat current song",
                },
            },
            "required": ["mode"],
        },
    },
    {
        "name": "search_and_play",
        "description": "Search Spotify for a track, artist, or genre and start playing the best result.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query, e.g. 'Bohemian Rhapsody Queen' or 'lofi hip hop chill'",
                },
            },
            "required": ["query"],
        },
    },
]


def _build_system(state: dict | None) -> str:
    lines = [
        "You are a Spotify assistant. The user gives you natural language commands and you call the appropriate tools to control Spotify playback.",
        "Call tools directly — do not ask clarifying questions. If the user's intent is clear, act immediately.",
        "After executing, respond with a short confirmation (one sentence).",
        "",
        "Current playback state:",
    ]
    if state and state.get("item"):
        item = state["item"]
        track = item.get("name", "Unknown")
        artists = ", ".join(a["name"] for a in item.get("artists", []))
        is_playing = state.get("is_playing", False)
        shuffle = state.get("shuffle_state", False)
        repeat = state.get("repeat_state", "off")
        volume = state.get("device", {}).get("volume_percent", 50) or 50
        lines += [
            f"  Track: {track} by {artists}",
            f"  Playing: {is_playing}",
            f"  Volume: {volume}%",
            f"  Shuffle: {shuffle}",
            f"  Repeat: {repeat}",
        ]
    else:
        lines.append("  Nothing currently playing.")
    return "\n".join(lines)


def _execute_tool(tool_name: str, tool_input: dict[str, Any], client: SpotifyClient, state: dict | None) -> str:
    try:
        if tool_name == "play_pause":
            action = tool_input.get("action", "toggle")
            is_playing = state.get("is_playing", False) if state else False
            if action == "toggle":
                client.play_pause(is_playing)
            elif action == "play":
                if not is_playing:
                    client.play_pause(False)
            elif action == "pause":
                if is_playing:
                    client.play_pause(True)
            return "Done"

        elif tool_name == "next_track":
            client.next_track()
            return "Skipped to next track"

        elif tool_name == "prev_track":
            client.prev_track()
            return "Went to previous track"

        elif tool_name == "set_volume":
            vol = int(tool_input["volume"])
            client.set_volume(vol)
            return f"Volume set to {vol}%"

        elif tool_name == "set_shuffle":
            enabled = bool(tool_input["enabled"])
            client.set_shuffle(enabled)
            return f"Shuffle {'enabled' if enabled else 'disabled'}"

        elif tool_name == "set_repeat":
            mode = tool_input["mode"]
            client.sp.repeat(mode)
            return f"Repeat set to {mode}"

        elif tool_name == "search_and_play":
            query = tool_input["query"]
            tracks = client.search(query, limit=1)
            if not tracks:
                return f"No results found for '{query}'"
            track = tracks[0]
            client.play_track(track["uri"])
            track_name = track.get("name", "Unknown")
            artist = ", ".join(a["name"] for a in track.get("artists", []))
            return f"Now playing: {track_name} by {artist}"

        else:
            return f"Unknown tool: {tool_name}"

    except Exception as exc:
        return f"Error: {exc}"


# ── Anthropic ─────────────────────────────────────────────────────────────────

def _run_anthropic(query: str, client: SpotifyClient, ai_config: dict, state: dict | None) -> str:
    import anthropic

    ai = anthropic.Anthropic(api_key=ai_config["api_key"])
    model = ai_config.get("model", "claude-opus-4-6")
    system = _build_system(state)
    messages: list[dict] = [{"role": "user", "content": query}]

    while True:
        response = ai.messages.create(
            model=model,
            max_tokens=512,
            system=system,
            tools=_TOOLS,
            messages=messages,
        )

        if response.stop_reason == "end_turn":
            return next((b.text for b in response.content if b.type == "text"), "Done.")

        if response.stop_reason != "tool_use":
            break

        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                result = _execute_tool(block.name, block.input, client, state)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })
        messages.append({"role": "user", "content": tool_results})

    return "Done."


# ── OpenAI-compatible (Ollama, OpenAI, Groq, LM Studio, …) ────────────────────

def _openai_tools() -> list[dict]:
    """Convert Anthropic tool schema to OpenAI function-calling format."""
    return [
        {
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t["description"],
                "parameters": t["input_schema"],
            },
        }
        for t in _TOOLS
    ]


def _run_openai_compatible(query: str, client: SpotifyClient, ai_config: dict, state: dict | None) -> str:
    import requests  # already a transitive dep via spotipy

    provider = ai_config.get("provider", "openai_compatible")
    base_url = ai_config.get("base_url", "http://localhost:11434").rstrip("/")
    model = ai_config.get("model", "llama3.2")
    api_key = ai_config.get("api_key", "ollama")

    if provider == "ollama" and not base_url.endswith("/v1"):
        base_url += "/v1"

    chat_url = base_url + "/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    system = _build_system(state)
    messages: list[dict] = [
        {"role": "system", "content": system},
        {"role": "user", "content": query},
    ]
    tools = _openai_tools()

    while True:
        payload = {"model": model, "messages": messages, "tools": tools, "stream": False}
        resp = requests.post(chat_url, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()

        choice = data["choices"][0]
        message = choice["message"]
        tool_calls = message.get("tool_calls") or []

        if not tool_calls:
            return message.get("content") or "Done."

        messages.append(message)

        for tc in tool_calls:
            fn = tc["function"]
            args = json.loads(fn["arguments"])
            result = _execute_tool(fn["name"], args, client, state)
            messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": result,
            })

    return "Done."


# ── Public entry point ────────────────────────────────────────────────────────

def run_ai_command(query: str, client: SpotifyClient, ai_config: dict) -> str:
    """Execute a natural language Spotify command. Returns a confirmation string."""
    try:
        state = client.get_current_playback()
    except Exception:
        state = None

    provider = ai_config.get("provider", "anthropic")

    if provider == "anthropic":
        return _run_anthropic(query, client, ai_config, state)
    else:
        return _run_openai_compatible(query, client, ai_config, state)
