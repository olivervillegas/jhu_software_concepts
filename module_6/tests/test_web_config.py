from __future__ import annotations

import pytest


def test_get_database_dsn_uses_database_url(monkeypatch):
    from src.web.app.config import get_database_dsn

    monkeypatch.setenv("DATABASE_URL", "postgresql://override")
    assert get_database_dsn() == "postgresql://override"


def test_get_database_dsn_builds_from_parts(monkeypatch):
    from src.web.app.config import get_database_dsn

    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("DB_HOST", "db")
    monkeypatch.setenv("DB_PORT", "5432")
    monkeypatch.setenv("DB_NAME", "n")
    monkeypatch.setenv("DB_USER", "u")
    monkeypatch.setenv("DB_PASSWORD", "p@ss word")

    dsn = get_database_dsn()
    assert dsn.startswith("postgresql://u:")
    # password should be quoted
    assert "p%40ss+word" in dsn
    assert "@db:5432/n" in dsn


def test_required_env_missing_raises(monkeypatch):
    from src.web.app.config import get_database_dsn

    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("DB_HOST", raising=False)
    monkeypatch.setenv("DB_PORT", "5432")
    monkeypatch.setenv("DB_NAME", "n")
    monkeypatch.setenv("DB_USER", "u")
    monkeypatch.setenv("DB_PASSWORD", "p")

    with pytest.raises(RuntimeError, match="DB_HOST"):
        get_database_dsn()