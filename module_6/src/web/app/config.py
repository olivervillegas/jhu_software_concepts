"""Configuration helpers for the web service."""

from __future__ import annotations

import os
from urllib.parse import quote_plus


def _required_env(name: str) -> str:
    """Return environment variable value or raise a clear error."""
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def get_database_dsn() -> str:
    """
    Return Postgres DSN.

    Preference order:
    1) DATABASE_URL if present
    2) Build from DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASSWORD
    """
    override = os.getenv("DATABASE_URL")
    if override:
        return override

    host = _required_env("DB_HOST")
    port = _required_env("DB_PORT")
    name = _required_env("DB_NAME")
    user = _required_env("DB_USER")
    password = quote_plus(_required_env("DB_PASSWORD"))

    return f"postgresql://{user}:{password}@{host}:{port}/{name}"
