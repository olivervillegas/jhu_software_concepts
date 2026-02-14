import os
import json
import pytest

from src.flask_app import create_app, BusyFlag
from src.db import ensure_schema, truncate_all, DB
from src.etl import (
    clean_text,
    safe_float,
    insert_applicants,
    pull_and_load,
    file_scraper,
)
from src.query_data import get_results, format_for_display
from src.config import get_database_url


# -----------------------------
# Fixtures
# -----------------------------

@pytest.fixture
def test_db():
    url = os.environ.get("DATABASE_URL")
    db = DB(url=url)
    ensure_schema(db)
    truncate_all(db)
    return db


@pytest.fixture
def app(test_db):
    def fake_scraper():
        return [{
            "program": "MIT Computer Science",
            "comments": "Test",
            "date_added": "2026-01-01",
            "url": "http://test1",
            "status": "Accepted",
            "semester_year_start": "Fall 2026",
            "citizenship": "International",
            "gpa": "3.9",
            "gre": "330",
            "gre_v": "165",
            "gre_aw": "4.5",
            "masters_or_phd": "PhD",
            "llm-generated-program": "Computer Science",
            "llm-generated-university": "MIT"
        }]

    return create_app(
        database_url=os.environ.get("DATABASE_URL"),
        scraper_fn=fake_scraper,
        busy_flag=BusyFlag()
    )


@pytest.fixture
def client(app):
    return app.test_client()


# -----------------------------
# DB Tests
# -----------------------------

@pytest.mark.db
def test_clean_text_and_safe_float():
    assert clean_text("abc\x00") == "abc"
    assert clean_text(None) is None
    assert safe_float("GPA 3.8") == 3.8
    assert safe_float(None) is None


@pytest.mark.db
def test_insert_and_idempotency(test_db):
    rows = [{"url": "unique-url", "gpa": "3.5"}]

    assert insert_applicants(test_db, rows) == 1
    assert insert_applicants(test_db, rows) == 0


@pytest.mark.integration
def test_pull_and_load(test_db):
    def scraper():
        return [{"url": "url2"}]

    result = pull_and_load(test_db, scraper)
    assert result["ok"] is True


@pytest.mark.db
def test_file_scraper(tmp_path):
    file = tmp_path / "data.json"
    file.write_text(json.dumps([{"a": 1}]))
    assert isinstance(file_scraper(str(file)), list)

    empty = tmp_path / "empty.json"
    empty.write_text("")
    assert file_scraper(str(empty)) == []


# -----------------------------
# Analysis Tests
# -----------------------------

@pytest.mark.analysis
def test_get_results_and_format(test_db):
    results = get_results(test_db)
    assert isinstance(results, dict)

    for k, v in results.items():
        formatted = format_for_display(k, v)
        assert isinstance(formatted, str)


# -----------------------------
# Web + Button Tests
# -----------------------------

@pytest.mark.web
def test_analysis_page(client):
    r = client.get("/analysis")
    assert r.status_code == 200


@pytest.mark.buttons
def test_pull_route(client):
    r = client.post("/pull-data")
    assert r.status_code == 302


@pytest.mark.buttons
def test_update_route(client):
    r = client.post("/update-analysis")
    assert r.status_code == 302


@pytest.mark.integration
def test_busy_branch(app):
    app.busy_flag.busy = True
    client = app.test_client()
    r = client.post("/pull-data")
    assert r.status_code == 302

@pytest.mark.db
def test_config_env_override(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://test")
    from src.config import get_database_url

    assert get_database_url() == "postgresql://test"

@pytest.mark.db
def test_file_scraper_empty_file(tmp_path):
    f = tmp_path / "empty.json"
    f.write_text("")
    assert file_scraper(str(f)) == []

@pytest.mark.db
def test_file_scraper_missing_file():
    with pytest.raises(FileNotFoundError):
        file_scraper("non_existent_file.json")


@pytest.mark.db
def test_file_scraper_jsonl(tmp_path):
    file = tmp_path / "data.jsonl"
    file.write_text('{"a":1}\n{"b":2}')
    data = file_scraper(str(file))
    assert len(data) == 2

@pytest.mark.db
def test_safe_float_int_and_float():
    assert safe_float(5) == 5.0
    assert safe_float(3.25) == 3.25

@pytest.mark.db
def test_safe_float_no_number():
    assert safe_float("no numbers here") is None

@pytest.mark.web
def test_create_app_missing_database_url(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    from src.flask_app import create_app
    with pytest.raises(RuntimeError):
        create_app(database_url=None)


@pytest.mark.web
def test_create_app_defaults(test_db):
    # use defaults for scraper + busy flag
    app = create_app(database_url=os.environ.get("DATABASE_URL"))
    assert app.scraper_fn is not None
    assert app.busy_flag is not None


@pytest.mark.analysis
def test_percentage_formatting_branch(app):
    client = app.test_client()

    # Insert at least one row via fake scraper
    def fake_scraper():
        return [{
            "program": "Test",
            "url": "unique1",
            "status": "Accepted",
            "term": "Fall 2026",
            "us_or_international": "International"
        }]

    app.scraper_fn = fake_scraper
    client.post("/pull-data")

    r = client.get("/analysis")
    html = r.data.decode()

    assert "%" in html

@pytest.mark.db
def test_file_scraper_file_not_found():
    with pytest.raises(FileNotFoundError):
        file_scraper("definitely_missing.json")

@pytest.mark.buttons
def test_update_busy_branch(app):
    app.busy_flag.busy = True
    client = app.test_client()
    r = client.post("/update-analysis")
    assert r.status_code == 302

@pytest.mark.analysis
def test_format_for_display_exception_branch():
    # Force percentish key but invalid numeric conversion
    result = format_for_display("Acceptance Rate", "invalid")
    assert isinstance(result, str)

# -----------------------------
# Config Coverage
# -----------------------------

@pytest.mark.db
def test_config():
    os.environ["DATABASE_URL"] = "test-url"
    assert get_database_url() == "test-url"
