from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Callable, List, Dict

from .db import connect, DB


# -------------------------------------------------
# Default File-Based Scraper (NO INTERNET)
# -------------------------------------------------
def clean_text(v):
    if v is None:
        return None
    return str(v).replace("\x00", "").strip()

def safe_float(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    match = re.search(r"\d+(\.\d+)?", str(v))
    return float(match.group()) if match else None

def file_scraper(path: str = "data/llm_extend_applicant_data.json") -> List[Dict]:
    """
    Default scraper used in production mode.
    Reads from a local JSON or JSONL file.
    """
    p = Path(path)

    if not p.exists():
        raise FileNotFoundError(f"Missing data file: {p.resolve()}")

    text = p.read_text(encoding="utf-8").strip()

    if not text:
        return []

    # JSON array
    if text.startswith("["):
        return json.loads(text)

    # JSONL
    return [json.loads(line) for line in text.splitlines() if line.strip()]


# -------------------------------------------------
# Insert Logic
# -------------------------------------------------

def insert_applicants(db: DB, rows: List[Dict]) -> int:
    """
    Insert applicant rows.
    Uses ON CONFLICT (url) to enforce idempotency.
    """
    inserted = 0

    with connect(db) as conn:
        with conn.cursor() as cur:
            for r in rows:
                cur.execute(
                    """
                    INSERT INTO applicants (
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
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (url) DO NOTHING
                    """,
                    (
                        clean_text(r.get("program")),
                        clean_text(r.get("comments")),
                        clean_text(r.get("date_added")),
                        clean_text(r.get("url")),
                        clean_text(r.get("applicant_status") or r.get("status")),
                        clean_text(r.get("semester_year_start") or r.get("term")),
                        clean_text(r.get("citizenship") or r.get("us_or_international")),
                        safe_float(r.get("gpa")),
                        safe_float(r.get("gre")),
                        safe_float(r.get("gre_v")),
                        safe_float(r.get("gre_aw")),
                        clean_text(r.get("masters_or_phd") or r.get("degree")),
                        clean_text(r.get("llm-generated-program") or r.get("llm_generated_program")),
                        clean_text(r.get("llm-generated-university") or r.get("llm_generated_university"))
                    ),
                )
                inserted += cur.rowcount

        conn.commit()

    return inserted


# -------------------------------------------------
# Pull & Load Orchestrator
# -------------------------------------------------

def pull_and_load(db: DB, scraper_fn: Callable[[], List[Dict]]) -> Dict:
    """
    Executes scraper + inserts rows.
    """
    rows = scraper_fn()
    new_rows = insert_applicants(db, rows)

    return {
        "ok": True,
        "total_rows": new_rows
    }
