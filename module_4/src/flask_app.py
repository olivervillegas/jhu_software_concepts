from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Any, Dict, Optional

from flask import Flask, render_template, jsonify

from .config import Config
from .db import DB, ensure_schema
from .etl import pull_and_load
from .query_data import get_results, format_for_display

@dataclass
class BusyFlag:
    value: bool = False

def create_app(
    config: Optional[type[Config]] = None,
    *,
    db: Optional[DB] = None,
    scraper_fn: Optional[Callable[[], list[dict[str, Any]]]] = None,
    results_fn: Optional[Callable[[DB], Dict[str, Any]]] = None,
    busy_flag: Optional[BusyFlag] = None,
) -> Flask:
    app = Flask(__name__, template_folder="templates")
    app.config.from_object(config or Config)

    app.db = db or DB(url=app.config["DATABASE_URL"])
    ensure_schema(app.db)

    app.scraper_fn = scraper_fn
    app.results_fn = results_fn or get_results
    app.busy_flag = busy_flag or BusyFlag(False)
    app.cached_results = None

    @app.get("/analysis")
    def analysis():
        results = app.cached_results or app.results_fn(app.db)
        formatted = {k: format_for_display(k, v) for k, v in results.items()}
        return render_template("analysis.html", results=formatted)

    @app.post("/pull-data")
    def pull_data():
        if app.busy_flag.value:
            return jsonify({"busy": True}), 409
        if app.scraper_fn is None:
            return jsonify({"ok": False, "error": "No scraper configured"}), 500
        app.busy_flag.value = True
        try:
            info = pull_and_load(app.db, app.scraper_fn)
            return jsonify({"ok": True, **info}), 200
        finally:
            app.busy_flag.value = False

    @app.post("/update-analysis")
    def update_analysis():
        if app.busy_flag.value:
            return jsonify({"busy": True}), 409
        app.cached_results = app.results_fn(app.db)
        return jsonify({"ok": True}), 200

    @app.get("/")
    def index():
        return analysis()

    return app
