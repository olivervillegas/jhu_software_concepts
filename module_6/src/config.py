"""Application configuration and environment handling."""

from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import quote_plus


def _required_env(name: str) -> str:
    """Get a required environment variable or raise a clear error."""
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def get_database_dsn() -> str:
    """
    Build a Postgres DSN from environment variables.

    Supports DATABASE_URL as an override for CI/local convenience, but the
    primary configuration path is DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASSWORD.
    """
    override = os.getenv("DATABASE_URL")
    if override:
        return override

    host = _required_env("DB_HOST")
    port = _required_env("DB_PORT")
    name = _required_env("DB_NAME")
    user = _required_env("DB_USER")
    password = quote_plus(_required_env("DB_PASSWORD"))

    # psycopg accepts standard Postgres URIs
    return f"postgresql://{user}:{password}@{host}:{port}/{name}"

# Backward-compatible name used by older tests / module_4
def get_database_url() -> str:
    """Backward-compatible alias for tests expecting get_database_url()."""
    return get_database_dsn()


@dataclass(frozen=True)
class Config:
    """Flask configuration container."""

    testing: bool = False
    database_dsn: str = ""
