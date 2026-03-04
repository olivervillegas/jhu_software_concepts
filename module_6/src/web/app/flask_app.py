from __future__ import annotations

import os
from typing import Any, Dict

from flask import Flask, jsonify, redirect, render_template, request, url_for

from src.web.publisher import publish_task
from .config import get_database_dsn
from .db import DB
from .query_data import compute_live_metrics, format_for_display, read_cached_metrics


def _wants_json() -> bool:
    """
    Decide whether to return JSON.

    Browser form posts often send Accept: */* or text/html, so we treat those as HTML.
    If the client explicitly requests JSON, return JSON.
    """
    accept = (request.headers.get("Accept") or "").lower()
    return "application/json" in accept


def create_app() -> Flask:
    """Flask app factory for the web service."""
    app = Flask(__name__)
    app.secret_key = os.getenv("FLASK_SECRET", "dev")

    db = DB(url=get_database_dsn())
    # Store on app for potential debugging / extension
    app.db = db  # type: ignore[attr-defined]

    @app.get("/")
    @app.get("/analysis")
    def analysis() -> str:
        """
        Render analysis page:
        - Always compute live metrics so all expected keys appear.
        - Overlay any cached metrics produced by the worker.
        """
        live: Dict[str, Any] = compute_live_metrics(db)
        formatted = {k: format_for_display(k, v) for k, v in live.items()}

        cached = read_cached_metrics(db)
        if cached: # pragma: no cover
            formatted.update(cached)

        return render_template("analysis.html", results=formatted)

    @app.post("/pull-data")
    def enqueue_scrape():
        """Enqueue scrape_new_data via RabbitMQ."""
        try:
            publish_task("scrape_new_data", payload={})
            if _wants_json():
                return jsonify({"status": "queued", "task": "scrape_new_data"}), 202
            return redirect(url_for("analysis", queued="scrape_new_data"), code=303)
        except Exception:  # pylint: disable=broad-exception-caught
            app.logger.exception("Failed to publish scrape_new_data")
            if _wants_json():
                return jsonify({"error": "publish_failed"}), 503
            return "Publish failed", 503 # pragma: no cover

    @app.post("/update-analysis")
    def enqueue_recompute():
        """Enqueue recompute_analytics via RabbitMQ."""
        try:
            publish_task("recompute_analytics", payload={})
            if _wants_json(): # pragma: no cover
                return jsonify({"status": "queued", "task": "recompute_analytics"}), 202
            return redirect(url_for("analysis", queued="recompute_analytics"), code=303)
        except Exception:  # pylint: disable=broad-exception-caught
            app.logger.exception("Failed to publish recompute_analytics")
            if _wants_json(): # pragma: no cover
                return jsonify({"error": "publish_failed"}), 503
            return "Publish failed", 503

    return app
