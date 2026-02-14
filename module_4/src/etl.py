from __future__ import annotations
from typing import Any, Dict, List

from .db import DB, connect

APPLICANT_COLS = [
    "program","comments","date_added","url","status","term","us_or_international",
    "gpa","gre","gre_v","gre_aw","degree","llm_generated_program","llm_generated_university"
]

def insert_applicants(db: DB, rows: List[Dict[str, Any]]) -> int:
    """Insert applicant rows with idempotency (ON CONFLICT DO NOTHING on url)."""
    if not rows:
        return 0

    inserted = 0
    with connect(db) as conn:
        with conn.cursor() as cur:
            for r in rows:
                values = [r.get(c) for c in APPLICANT_COLS]
                cur.execute(
                    """
                    INSERT INTO applicants (
                        program, comments, date_added, url, status, term, us_or_international,
                        gpa, gre, gre_v, gre_aw, degree, llm_generated_program, llm_generated_university
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT DO NOTHING
                    """,
                    values,
                )
                inserted += int(cur.rowcount == 1)
        conn.commit()
    return inserted

def count_applicants(db: DB) -> int:
    with connect(db) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM applicants;")
            return int(cur.fetchone()[0])

def pull_and_load(db: DB, scraper_fn) -> Dict[str, Any]:
    """Scrape (injected) -> insert -> return counts."""
    rows = scraper_fn()
    new_rows = insert_applicants(db, rows)
    total = count_applicants(db)
    return {"new_rows": new_rows, "total_rows": total}
