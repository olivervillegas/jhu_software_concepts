from __future__ import annotations
import re
from typing import Any, Dict

from .db import DB, connect

EXPECTED_KEYS = [
    "Fall 2026 Applicants",
    "International Percentage",
    "Average GPA / GRE / GRE-V / GRE-AW (non-null)",
    "Avg GPA (American, Fall 2026)",
    "Acceptance Rate (Fall 2026)",
    "Avg GPA (Accepted, Fall 2026)",
    "JHU Masters CS Applicants",
    "Fall 2026 Accepted PhD CS at Georgetown/MIT/Stanford/CMU (program text)",
    "Fall 2026 Accepted PhD CS at Georgetown/MIT/Stanford/CMU (LLM fields)",
    "Top 5 Universities by # of Entries (LLM)",
    "Acceptance Rate Overall (all terms)",
]

def run_scalar(db: DB, sql: str):
    with connect(db) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            row = cur.fetchone()
            return row[0] if row else None

def run_row(db: DB, sql: str):
    with connect(db) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            return cur.fetchone()

def get_results(db: DB) -> Dict[str, Any]:
    return {
        "Fall 2026 Applicants": run_scalar(db, """SELECT COUNT(*) FROM applicants WHERE TRIM(term)='Fall 2026';"""),
        "International Percentage": run_scalar(db, """            SELECT ROUND((100.0 * COUNT(*) / NULLIF((SELECT COUNT(*) FROM applicants), 0))::numeric, 2)
            FROM applicants WHERE us_or_international='International';
        """),
        "Average GPA / GRE / GRE-V / GRE-AW (non-null)": run_row(db, """            SELECT
              ROUND(AVG(gpa)::numeric, 2),
              ROUND(AVG(gre)::numeric, 2),
              ROUND(AVG(gre_v)::numeric, 2),
              ROUND(AVG(gre_aw)::numeric, 2)
            FROM applicants
            WHERE gpa IS NOT NULL OR gre IS NOT NULL OR gre_v IS NOT NULL OR gre_aw IS NOT NULL;
        """),
        "Avg GPA (American, Fall 2026)": run_scalar(db, """            SELECT ROUND(AVG(gpa)::numeric, 2)
            FROM applicants
            WHERE TRIM(term)='Fall 2026' AND us_or_international='American' AND gpa IS NOT NULL;
        """),
        "Acceptance Rate (Fall 2026)": run_scalar(db, """            SELECT
              CASE
                WHEN (SELECT COUNT(*) FROM applicants WHERE TRIM(term)='Fall 2026') = 0 THEN 0
                ELSE ROUND((100.0 * COUNT(*) / (SELECT COUNT(*) FROM applicants WHERE TRIM(term)='Fall 2026'))::numeric, 2)
              END
            FROM applicants
            WHERE TRIM(term)='Fall 2026' AND status='Accepted';
        """),
        "Avg GPA (Accepted, Fall 2026)": run_scalar(db, """            SELECT ROUND(AVG(gpa)::numeric, 2)
            FROM applicants
            WHERE TRIM(term)='Fall 2026' AND status='Accepted' AND gpa IS NOT NULL;
        """),
        "JHU Masters CS Applicants": run_scalar(db, """            SELECT COUNT(*)
            FROM applicants
            WHERE program ILIKE '%Johns Hopkins%'
              AND program ILIKE '%Computer Science%'
              AND degree='Masters';
        """),
        "Fall 2026 Accepted PhD CS at Georgetown/MIT/Stanford/CMU (program text)": run_scalar(db, """            SELECT COUNT(*)
            FROM applicants
            WHERE TRIM(term)='Fall 2026'
              AND status='Accepted'
              AND degree='PhD'
              AND program ILIKE '%Computer Science%'
              AND (
                program ILIKE '%Georgetown%' OR
                program ILIKE '%MIT%' OR
                program ILIKE '%Stanford%' OR
                program ILIKE '%Carnegie Mellon%'
              );
        """),
        "Fall 2026 Accepted PhD CS at Georgetown/MIT/Stanford/CMU (LLM fields)": run_scalar(db, """            SELECT COUNT(*)
            FROM applicants
            WHERE TRIM(term)='Fall 2026'
              AND status='Accepted'
              AND degree='PhD'
              AND llm_generated_program ILIKE '%Computer Science%'
              AND (
                llm_generated_university ILIKE '%Georgetown%' OR
                llm_generated_university ILIKE '%MIT%' OR
                llm_generated_university ILIKE '%Stanford%' OR
                llm_generated_university ILIKE '%Carnegie Mellon%'
              );
        """),
        "Top 5 Universities by # of Entries (LLM)": run_scalar(db, """            SELECT STRING_AGG(x, '; ')
            FROM (
              SELECT llm_generated_university || ': ' || COUNT(*) AS x
              FROM applicants
              WHERE llm_generated_university IS NOT NULL
              GROUP BY llm_generated_university
              ORDER BY COUNT(*) DESC
              LIMIT 5
            ) t;
        """),
        "Acceptance Rate Overall (all terms)": run_scalar(db, """            SELECT ROUND(
              (100.0 * (SELECT COUNT(*) FROM applicants WHERE status='Accepted') /
               NULLIF((SELECT COUNT(*) FROM applicants), 0)
              )::numeric, 2
            );
        """),
    }

_PERCENTISH = re.compile(r"(percentage|rate)", re.IGNORECASE)

def format_for_display(key: str, value: Any) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, tuple):
        return ", ".join("N/A" if v is None else str(v) for v in value)
    if _PERCENTISH.search(key):
        try:
            return f"{float(value):.2f}%"
        except Exception:
            return str(value)
    return str(value)
