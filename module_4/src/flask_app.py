from __future__ import annotations

import os
from flask import Flask, jsonify, render_template, redirect, url_for

from .db import DB, ensure_schema
from .etl import pull_and_load, file_scraper
from .query_data import get_results


class BusyFlag:
    def __init__(self):
        self.busy = False


def create_app(
    database_url: str | None = None,
    scraper_fn=None,
    busy_flag: BusyFlag | None = None,
):
    app = Flask(__name__)

    # ----------------------------------------
    # Database setup
    # ----------------------------------------
    if database_url is None:
        database_url = os.environ.get("DATABASE_URL")

    if not database_url:
        raise RuntimeError("DATABASE_URL must be provided")

    db = DB(url=database_url)
    ensure_schema(db)

    # ----------------------------------------
    # Default scraper wiring
    # ----------------------------------------
    if scraper_fn is None:
        scraper_fn = file_scraper

    if busy_flag is None:
        busy_flag = BusyFlag()

    app.db = db
    app.scraper_fn = scraper_fn
    app.busy_flag = busy_flag

    # ----------------------------------------
    # Routes
    # ----------------------------------------

    @app.get("/")
    @app.get("/analysis")
    def analysis():
        results = get_results(db)

        # Format percentages to two decimals if numeric
        formatted = {}
        for k, v in results.items():
            if isinstance(v, (int, float)):
                formatted[k] = f"{v:.2f}%"
            else:
                formatted[k] = v if v is not None else "N/A"

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
        if app.busy_flag.busy:
            return redirect(url_for("analysis"))

        return redirect(url_for("analysis"))

    return app
