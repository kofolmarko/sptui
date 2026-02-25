from __future__ import annotations

from .config import ensure_config
from .client import SpotifyClient
from .app import SptApp


def main() -> None:
    config = ensure_config()
    client = SpotifyClient(
        client_id=config["client_id"],
        client_secret=config["client_secret"],
        redirect_uri=config["redirect_uri"],
    )
    app = SptApp(client, config)
    app.run()


if __name__ == "__main__":
    main()
