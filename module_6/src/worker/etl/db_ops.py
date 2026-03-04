from __future__ import annotations

import re
from datetime import date
from typing import Dict, List, Optional

import psycopg
from psycopg import sql

APPLICANTS_TABLE = "applicants"

_FLOAT_RE = re.compile(r"\d+(\.\d+)?")
_DATE_RE = re.compile(r"^\s*(\d{4})-(\d{2})-(\d{2})\s*$")


def clean_text(value: object) -> Optional[str]:
    """Normalize text for DB storage."""
    if value is None:
        return None
    return str(value).replace("\x00", "").strip() or None


def safe_float(value: object) -> Optional[float]:
    """Extract a float from int/float or from a messy string."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)

    match = _FLOAT_RE.search(str(value))
    return float(match.group()) if match else None


def safe_date(value: object) -> Optional[date]:
    """Parse YYYY-MM-DD into date; return None if invalid."""
    if value is None:
        return None

    match = _DATE_RE.match(str(value))
    if not match:
        return None

    year, month, day = (int(match.group(1)), int(match.group(2)), int(match.group(3)))
    try:
        return date(year, month, day)
    except ValueError:
        return None


def read_watermark(conn: psycopg.Connection, source: str) -> Optional[str]:
    """Read watermark for a given source."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT last_seen FROM ingestion_watermarks WHERE source = %s;",
            (source,),
        )
        row = cur.fetchone()
        return row[0] if row else None


def write_watermark(conn: psycopg.Connection, source: str, last_seen: str) -> None:
    """Upsert watermark for a given source."""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO ingestion_watermarks (source, last_seen)
            VALUES (%s, %s)
            ON CONFLICT (source)
            DO UPDATE SET last_seen = EXCLUDED.last_seen, updated_at = now();
            """,
            (source, last_seen),
        )


def insert_applicants(conn: psycopg.Connection, rows: List[Dict]) -> int:
    """
    Insert applicants using parameter binding and ON CONFLICT DO NOTHING (idempotent).
    Returns count of inserted rows (sum of cursor.rowcount).
    """
    stmt = sql.SQL(
        """
        INSERT INTO {table} (
            program,
            comments,
            date_added,
            url,
            status,
            term,
            us_or_international,
            gpa,
            gre,
            gre_v,
            gre_aw,
            degree,
            llm_generated_program,
            llm_generated_university
        )
        VALUES (
            {program},{comments},{date_added},{url},{status},{term},{us_int},
            {gpa},{gre},{gre_v},{gre_aw},{degree},{llm_prog},{llm_uni}
        )
        ON CONFLICT (url) DO NOTHING;
        """
    ).format(
        table=sql.Identifier(APPLICANTS_TABLE),
        program=sql.Placeholder(),
        comments=sql.Placeholder(),
        date_added=sql.Placeholder(),
        url=sql.Placeholder(),
        status=sql.Placeholder(),
        term=sql.Placeholder(),
        us_int=sql.Placeholder(),
        gpa=sql.Placeholder(),
        gre=sql.Placeholder(),
        gre_v=sql.Placeholder(),
        gre_aw=sql.Placeholder(),
        degree=sql.Placeholder(),
        llm_prog=sql.Placeholder(),
        llm_uni=sql.Placeholder(),
    )

    inserted = 0
    with conn.cursor() as cur:
        for row in rows:
            params = (
                clean_text(row.get("program")),
                clean_text(row.get("comments")),
                safe_date(row.get("date_added")),
                clean_text(row.get("url")),
                clean_text(row.get("applicant_status") or row.get("status")),
                clean_text(row.get("semester_year_start") or row.get("term")),
                clean_text(row.get("citizenship") or row.get("us_or_international")),
                safe_float(row.get("gpa")),
                safe_float(row.get("gre")),
                safe_float(row.get("gre_v")),
                safe_float(row.get("gre_aw")),
                clean_text(row.get("masters_or_phd") or row.get("degree")),
                clean_text(row.get("llm-generated-program") or row.get("llm_generated_program")),
                clean_text(row.get("llm-generated-university") or
                           row.get("llm_generated_university")),
            )
            cur.execute(stmt, params)
            inserted += cur.rowcount

    return inserted


def upsert_analytics_cache(conn: psycopg.Connection, metrics: Dict[str, str]) -> None:
    """Upsert computed metrics into analytics_cache."""
    with conn.cursor() as cur:
        for key, value in metrics.items():
            cur.execute(
                """
                INSERT INTO analytics_cache (key, value)
                VALUES (%s, %s)
                ON CONFLICT (key)
                DO UPDATE SET value = EXCLUDED.value, updated_at = now();
                """,
                (key, value),
            )
