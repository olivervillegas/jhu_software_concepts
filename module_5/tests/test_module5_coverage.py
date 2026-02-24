import os
import pytest

from src.config import _required_env, get_database_dsn
from src.db import DB
from src.etl import file_scraper
from src.flask_app import create_app


def test_required_env_raises(monkeypatch):
    monkeypatch.delenv("SOME_MISSING_VAR", raising=False)
    with pytest.raises(RuntimeError):
        _required_env("SOME_MISSING_VAR")


def test_get_database_dsn_from_db_env_vars(monkeypatch):
    # Ensure DATABASE_URL override is not used so we cover the DB_* path
    monkeypatch.delenv("DATABASE_URL", raising=False)

    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_PORT", "5432")
    monkeypatch.setenv("DB_NAME", "gradcafe")
    monkeypatch.setenv("DB_USER", "user")
    # include a character that must be URL-encoded to cover quote_plus
    monkeypatch.setenv("DB_PASSWORD", "p@ss word")

    dsn = get_database_dsn()
    assert dsn.startswith("postgresql://user:")
    assert "@localhost:5432/gradcafe" in dsn
    # quote_plus turns space into + and @ into %40
    assert "p%40ss+word" in dsn


def test_db_dsn_property_covered():
    db = DB(url="postgresql://x:y@h:1/db")
    assert db.dsn == db.url


def test_file_scraper_missing_file(tmp_path):
    missing = tmp_path / "does_not_exist.json"
    with pytest.raises(FileNotFoundError):
        file_scraper(str(missing))


def test_file_scraper_empty_file(tmp_path):
    empty = tmp_path / "empty.json"
    empty.write_text("", encoding="utf-8")
    assert file_scraper(str(empty)) == []


def test_create_app_raises_when_database_url_required(monkeypatch):
    # This covers the explicit database_url path + raising branch
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(RuntimeError):
        create_app(database_url=None)
