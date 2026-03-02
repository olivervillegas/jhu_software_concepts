"""Flask application factory and routes."""

from __future__ import annotations
import os
from dataclasses import dataclass
from typing import Callable, Optional, Any, Final

from flask import Flask, redirect, render_template, url_for

from .config import get_database_dsn
from .db import DB, ensure_schema
from .etl import file_scraper, pull_and_load
from .query_data import format_for_display, get_results

_MISSING: Final[Any] = object()

@dataclass
class BusyFlag:
    """Simple flag to prevent concurrent ETL runs in a single-process app."""

    busy: bool = False


def create_app(
    database_url: str | None | Any = _MISSING,
    database_dsn: Optional[str] = None,
    scraper_fn: Optional[Callable[[], list]] = None,
    busy_flag: Optional[BusyFlag] = None,
) -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)

    if database_url is not _MISSING:
        chosen = database_url or os.environ.get("DATABASE_URL")
        if not chosen:
            raise RuntimeError("DATABASE_URL must be provided")
    elif database_dsn is not None: # pragma: no cover
        chosen = database_dsn
    else: # pragma: no cover
        chosen = get_database_dsn()

    if not chosen: # pragma: no cover
        raise RuntimeError("DATABASE_URL or DB_* variables must be provided")

    db = DB(url=chosen)

    ensure_schema(db)

    if scraper_fn is None:
        scraper_fn = file_scraper

    if busy_flag is None:
        busy_flag = BusyFlag()

    app.db = db
    app.scraper_fn = scraper_fn
    app.busy_flag = busy_flag

    @app.get("/")
    @app.get("/analysis")
    def analysis() -> str:
        results = get_results(db)
        formatted = {k: format_for_display(k, v) for k, v in results.items()}
        return render_template("analysis.html", results=formatted)

    @app.post("/pull-data")
    def pull_data():
        if app.busy_flag.busy:
            return redirect(url_for("analysis"))

        app.busy_flag.busy = True
        try:
            pull_and_load(app.db, app.scraper_fn)
        finally:
            app.busy_flag.busy = False

        return redirect(url_for("analysis"))

    @app.post("/update-analysis")
    def update_analysis():
        return redirect(url_for("analysis"))

    return app
