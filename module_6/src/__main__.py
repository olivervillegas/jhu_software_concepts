"""Entrypoint: `python -m src`."""

from __future__ import annotations

import os

from .flask_app import create_app

app = create_app()

if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    app.run(debug=debug)
