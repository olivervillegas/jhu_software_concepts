"""ETL: load applicant rows from a local JSON/JSONL file into PostgreSQL."""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Callable, Dict, List, Optional

from psycopg import sql

from .db import APPLICANTS_TABLE, DB, connect


_FLOAT_RE = re.compile(r"\d+(\.\d+)?")
_DATE_RE = re.compile(r"^\s*(\d{4})-(\d{2})-(\d{2})\s*$")


def clean_text(value: object) -> Optional[str]:
    """Normalize text values for storage."""
    if value is None:
        return None
    return str(value).replace("\x00", "").strip() or None


def safe_float(value: object) -> Optional[float]:
    """Extract a float from messy input like '3.5/4' or 'GRE: 330'."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    match = _FLOAT_RE.search(str(value))
    return float(match.group()) if match else None


def safe_date(value: object) -> Optional[date]:
    """Parse YYYY-MM-DD into datetime.date or return None."""
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


def file_scraper(path: str = "data/llm_extend_applicant_data.json") -> List[Dict]:
    """
    Default scraper used in production mode (NO INTERNET).
    Reads from a local JSON array file or JSONL file.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Missing data file: {p.resolve()}")

    text = p.read_text(encoding="utf-8").strip()
    if not text:
        return []

    if text.startswith("["):
        return json.loads(text)

    return [json.loads(line) for line in text.splitlines() if line.strip()]


def insert_applicants(db: DB, rows: List[Dict]) -> int:
    """
    Insert applicant rows using parameter binding and ON CONFLICT for idempotency.

    Security:
    - SQL is composed safely (Identifier for table).
    - Values are NEVER interpolated into SQL text; they are bound as parameters.
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
    with connect(db) as conn:
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
                    clean_text(row.get("llm-generated-program") or
                        row.get("llm_generated_program")),
                    clean_text(row.get("llm-generated-university") or
                        row.get("llm_generated_university")),
                )
                cur.execute(stmt, params)
                inserted += cur.rowcount
        conn.commit()

    return inserted


def pull_and_load(db: DB, scraper_fn: Callable[[], List[Dict]]) -> Dict[str, object]:
    """Execute scraper + insert rows and return a simple status dict."""
    rows = scraper_fn()
    new_rows = insert_applicants(db, rows)
    return {"ok": True, "total_rows": new_rows}
