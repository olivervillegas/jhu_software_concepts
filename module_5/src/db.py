"""Database access layer (connections + schema management)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

import psycopg
from psycopg import sql


APPLICANTS_TABLE: Final[str] = "applicants"


@dataclass(frozen=True)
class DB:
    """Database handle containing the connection string."""
    url: str

    @property
    def dsn(self) -> str:
        """Alias for compatibility with newer naming."""
        return self.url


def connect(db: DB) -> psycopg.Connection:
    """Open a new database connection."""
    return psycopg.connect(db.url)


def ensure_schema(db: DB) -> None:
    """Create applicants table and a unique index for url idempotency."""
    ddl = sql.SQL(
        """
        CREATE TABLE IF NOT EXISTS {table} (
            p_id SERIAL PRIMARY KEY,
            program TEXT,
            comments TEXT,
            date_added DATE,
            url TEXT,
            status TEXT,
            term TEXT,
            us_or_international TEXT,
            gpa DOUBLE PRECISION,
            gre DOUBLE PRECISION,
            gre_v DOUBLE PRECISION,
            gre_aw DOUBLE PRECISION,
            degree TEXT,
            llm_generated_program TEXT,
            llm_generated_university TEXT
        );
        """
    ).format(table=sql.Identifier(APPLICANTS_TABLE))

    uniq = sql.SQL(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS {idx}
        ON {table}(url);
        """
    ).format(
        idx=sql.Identifier("uq_applicants_url"),
        table=sql.Identifier(APPLICANTS_TABLE),
    )

    with connect(db) as conn:
        with conn.cursor() as cur:
            cur.execute(ddl)
            cur.execute(uniq)
        conn.commit()


def truncate_all(db: DB) -> None:
    """Truncate all app tables (used in tests)."""
    stmt = sql.SQL("TRUNCATE TABLE {table} RESTART IDENTITY;").format(
        table=sql.Identifier(APPLICANTS_TABLE)
    )
    with connect(db) as conn:
        with conn.cursor() as cur:
            cur.execute(stmt)
        conn.commit()
