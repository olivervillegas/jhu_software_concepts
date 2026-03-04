from __future__ import annotations

import os

from src.web.app.flask_app import create_app


def main() -> int:
    """Entrypoint for the web service."""
    app = create_app()
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=8080, debug=debug)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
