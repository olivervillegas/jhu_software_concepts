"""Database connection helper for the web service."""

from __future__ import annotations

from dataclasses import dataclass

import psycopg


@dataclass(frozen=True)
class DB:
    """Database handle containing the connection string."""
    url: str


def connect(db: DB) -> psycopg.Connection:
    """Open a new Postgres connection."""
    return psycopg.connect(db.url)
