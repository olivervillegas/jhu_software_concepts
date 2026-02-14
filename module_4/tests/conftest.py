import os
import re
import pytest

from src.flask_app import create_app, BusyFlag
from src.db import DB, truncate_all, ensure_schema
from src.query_data import EXPECTED_KEYS

MARKERS = {"web", "buttons", "analysis", "db", "integration"}

def pytest_collection_modifyitems(config, items):
    for item in items:
        marks = {m.name for m in item.iter_markers()}
        if not (marks & MARKERS):
            raise pytest.UsageError(
                f"Unmarked test found: {item.nodeid}. "
                f"All tests must be marked with one of: {sorted(MARKERS)}"
            )

@pytest.fixture(scope="session")
def database_url():
    return os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres")

@pytest.fixture
def db(database_url):
    db = DB(url=database_url)
    ensure_schema(db)
    truncate_all(db)
    yield db
    truncate_all(db)

@pytest.fixture
def fake_scraper():
    def _scrape():
        return [
            {
                "program": "MIT Computer Science",
                "comments": "Great fit",
                "date_added": "2026-01-31",
                "url": "https://thegradcafe.com/result/123",
                "status": "Accepted",
                "term": "Fall 2026",
                "us_or_international": "International",
                "gpa": 3.9,
                "gre": 330,
                "gre_v": 165,
                "gre_aw": 4.5,
                "degree": "PhD",
                "llm_generated_program": "Computer Science",
                "llm_generated_university": "MIT",
            },
            {
                "program": "Stanford Computer Science",
                "comments": None,
                "date_added": "2026-01-30",
                "url": "https://thegradcafe.com/result/124",
                "status": "Rejected",
                "term": "Fall 2026",
                "us_or_international": "American",
                "gpa": 3.7,
                "gre": 325,
                "gre_v": 162,
                "gre_aw": 4.0,
                "degree": "PhD",
                "llm_generated_program": "Computer Science",
                "llm_generated_university": "Stanford",
            },
            {
                "program": "MIT Computer Science",
                "comments": "duplicate",
                "date_added": "2026-01-31",
                "url": "https://thegradcafe.com/result/123",
                "status": "Accepted",
                "term": "Fall 2026",
                "us_or_international": "International",
                "gpa": 3.9,
                "gre": 330,
                "gre_v": 165,
                "gre_aw": 4.5,
                "degree": "PhD",
                "llm_generated_program": "Computer Science",
                "llm_generated_university": "MIT",
            },
        ]
    return _scrape

@pytest.fixture
def app(db, fake_scraper):
    busy = BusyFlag(False)
    app = create_app(db=db, scraper_fn=fake_scraper, busy_flag=busy)
    app.testing = True
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def pct_regex():
    return re.compile(r"\d+\.\d{2}%")
