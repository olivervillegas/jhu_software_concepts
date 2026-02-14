from __future__ import annotations

from dataclasses import dataclass
import psycopg

@dataclass(frozen=True)
class DB:
    url: str

def connect(db: DB):
    return psycopg.connect(db.url)

def ensure_schema(db: DB) -> None:
    """Create applicants table if it doesn't exist + enforce idempotency on url."""
    ddl = """
    CREATE TABLE IF NOT EXISTS applicants (
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

    # This is enough for ON CONFLICT and idempotency.
    # Works whether url is nullable or not.
    uniq = """
    CREATE UNIQUE INDEX IF NOT EXISTS uq_applicants_url
    ON applicants(url)
    """

    with connect(db) as conn:
        with conn.cursor() as cur:
            cur.execute(ddl)
            cur.execute(uniq)
        conn.commit()

def truncate_all(db: DB) -> None:
    with connect(db) as conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE applicants RESTART IDENTITY;")
        conn.commit()
