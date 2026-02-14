import os
import pytest

from src.config import get_database_url
from src.etl import insert_applicants
from src.flask_app import create_app
from src.query_data import format_for_display
from src.db import DB

@pytest.mark.db
def test_insert_empty_rows_returns_0(db):
    assert insert_applicants(db, []) == 0

@pytest.mark.web
def test_pull_data_without_scraper_returns_500(db):
    app = create_app(db=db, scraper_fn=None)
    app.testing = True
    client = app.test_client()
    r = client.post("/pull-data")
    assert r.status_code == 500

@pytest.mark.analysis
def test_format_for_display_bad_percent_value_falls_back():
    # triggers the exception path in format_for_display
    out = format_for_display("Acceptance Rate (Fall 2026)", "not-a-number")
    assert out == "not-a-number"

@pytest.mark.db
def test_get_database_url_default_when_env_missing(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    url = get_database_url()
    assert url.startswith("postgresql://")
