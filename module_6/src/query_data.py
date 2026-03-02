"""Analytics queries (safe SQL composition + enforced LIMIT)."""

from __future__ import annotations

import re
from typing import Any, Dict, Optional, Sequence, Tuple, Union

from psycopg import sql
from psycopg.sql import Composable

from .db import APPLICANTS_TABLE, DB, connect


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


def clamp_limit(value: Optional[int], *, minimum: int = 1, maximum: int = 100) -> int:
    """Clamp LIMIT to a safe range (required by assignment)."""
    if value is None: #pragma: no cover
        return maximum
    return max(minimum, min(maximum, int(value)))


Scalar = Union[int, float, str, None]
Row = Optional[Tuple[Any, ...]]


def run_scalar(db: DB, stmt: Composable, params: Sequence[object] = ()) -> Scalar:
    """Run a statement returning a single scalar value (LIMIT 1 required)."""
    with connect(db) as conn:
        with conn.cursor() as cur:
            cur.execute(stmt, params)
            row = cur.fetchone()
            return row[0] if row else None


def run_row(db: DB, stmt: Composable, params: Sequence[object] = ()) -> Row:
    """Run a statement returning a single row (LIMIT 1 required)."""
    with connect(db) as conn:
        with conn.cursor() as cur:
            cur.execute(stmt, params)
            return cur.fetchone()


def get_results(db: DB) -> Dict[str, Any]:
    """Compute analysis metrics from the applicants table."""
    tbl = sql.Identifier(APPLICANTS_TABLE)

    fall_2026_applicants = run_scalar(
        db,
        sql.SQL(
            "SELECT COUNT(*) FROM {t} WHERE TRIM(term) = %s LIMIT 1;"
        ).format(t=tbl),
        ("Fall 2026",),
    )

    international_pct = run_scalar(
        db,
        sql.SQL(
            """
            SELECT ROUND(
                (100.0 * COUNT(*) / NULLIF((SELECT COUNT(*) FROM {t}), 0))::numeric,
                2
            )
            FROM {t}
            WHERE us_or_international = %s
            LIMIT 1;
            """
        ).format(t=tbl),
        ("International",),
    )

    averages = run_row(
        db,
        sql.SQL(
            """
            SELECT
              ROUND(AVG(gpa)::numeric, 2),
              ROUND(AVG(gre)::numeric, 2),
              ROUND(AVG(gre_v)::numeric, 2),
              ROUND(AVG(gre_aw)::numeric, 2)
            FROM {t}
            WHERE gpa IS NOT NULL OR gre IS NOT NULL OR gre_v IS NOT NULL OR gre_aw IS NOT NULL
            LIMIT 1;
            """
        ).format(t=tbl),
    )

    avg_gpa_american_fall = run_scalar(
        db,
        sql.SQL(
            """
            SELECT ROUND(AVG(gpa)::numeric, 2)
            FROM {t}
            WHERE TRIM(term) = %s
              AND us_or_international = %s
              AND gpa IS NOT NULL
            LIMIT 1;
            """
        ).format(t=tbl),
        ("Fall 2026", "American"),
    )

    acceptance_rate_fall = run_scalar(
        db,
        sql.SQL(
            """
            SELECT
              CASE
                WHEN (SELECT COUNT(*) FROM {t} WHERE TRIM(term) = %s) = 0 THEN 0
                ELSE ROUND(
                  (100.0 * COUNT(*) / (SELECT COUNT(*) FROM {t} WHERE TRIM(term) = %s))::numeric,
                  2
                )
              END
            FROM {t}
            WHERE TRIM(term) = %s AND status = %s
            LIMIT 1;
            """
        ).format(t=tbl),
        ("Fall 2026", "Fall 2026", "Fall 2026", "Accepted"),
    )

    avg_gpa_accepted_fall = run_scalar(
        db,
        sql.SQL(
            """
            SELECT ROUND(AVG(gpa)::numeric, 2)
            FROM {t}
            WHERE TRIM(term) = %s AND status = %s AND gpa IS NOT NULL
            LIMIT 1;
            """
        ).format(t=tbl),
        ("Fall 2026", "Accepted"),
    )

    jhu_masters_cs = run_scalar(
        db,
        sql.SQL(
            """
            SELECT COUNT(*)
            FROM {t}
            WHERE program ILIKE %s
              AND program ILIKE %s
              AND degree = %s
            LIMIT 1;
            """
        ).format(t=tbl),
        ("%Johns Hopkins%", "%Computer Science%", "Masters"),
    )

    accepted_phd_program_text = run_scalar(
        db,
        sql.SQL(
            """
            SELECT COUNT(*)
            FROM {t}
            WHERE TRIM(term) = %s
              AND status = %s
              AND degree = %s
              AND program ILIKE %s
              AND (
                program ILIKE %s OR
                program ILIKE %s OR
                program ILIKE %s OR
                program ILIKE %s
              )
            LIMIT 1;
            """
        ).format(t=tbl),
        (
            "Fall 2026",
            "Accepted",
            "PhD",
            "%Computer Science%",
            "%Georgetown%",
            "%MIT%",
            "%Stanford%",
            "%Carnegie Mellon%",
        ),
    )

    accepted_phd_llm_fields = run_scalar(
        db,
        sql.SQL(
            """
            SELECT COUNT(*)
            FROM {t}
            WHERE TRIM(term) = %s
              AND status = %s
              AND degree = %s
              AND llm_generated_program ILIKE %s
              AND (
                llm_generated_university ILIKE %s OR
                llm_generated_university ILIKE %s OR
                llm_generated_university ILIKE %s OR
                llm_generated_university ILIKE %s
              )
            LIMIT 1;
            """
        ).format(t=tbl),
        (
            "Fall 2026",
            "Accepted",
            "PhD",
            "%Computer Science%",
            "%Georgetown%",
            "%MIT%",
            "%Stanford%",
            "%Carnegie Mellon%",
        ),
    )

    # Explicit LIMIT with clamp (assignment requirement).
    top_n = clamp_limit(5, minimum=1, maximum=100)
    top5_universities = run_scalar(
        db,
        sql.SQL(
            """
            SELECT STRING_AGG(x, '; ')
            FROM (
              SELECT llm_generated_university || ': ' || COUNT(*) AS x
              FROM {t}
              WHERE llm_generated_university IS NOT NULL
              GROUP BY llm_generated_university
              ORDER BY COUNT(*) DESC
              LIMIT {lim}
            ) sub
            LIMIT 1;
            """
        ).format(t=tbl, lim=sql.Literal(top_n)),
    )

    acceptance_rate_overall = run_scalar(
        db,
        sql.SQL(
            """
            SELECT ROUND(
              (100.0 * (SELECT COUNT(*) FROM {t} WHERE status = %s) /
               NULLIF((SELECT COUNT(*) FROM {t}), 0)
              )::numeric, 2
            )
            LIMIT 1;
            """
        ).format(t=tbl),
        ("Accepted",),
    )

    return {
        "Fall 2026 Applicants": fall_2026_applicants,
        "International Percentage": international_pct,
        "Average GPA / GRE / GRE-V / GRE-AW (non-null)": averages,
        "Avg GPA (American, Fall 2026)": avg_gpa_american_fall,
        "Acceptance Rate (Fall 2026)": acceptance_rate_fall,
        "Avg GPA (Accepted, Fall 2026)": avg_gpa_accepted_fall,
        "JHU Masters CS Applicants": jhu_masters_cs,
        "Fall 2026 Accepted PhD CS at Georgetown/MIT/Stanford/CMU (program text)": 
            accepted_phd_program_text,
        "Fall 2026 Accepted PhD CS at Georgetown/MIT/Stanford/CMU (LLM fields)": 
            accepted_phd_llm_fields,
        "Top 5 Universities by # of Entries (LLM)": top5_universities,
        "Acceptance Rate Overall (all terms)": acceptance_rate_overall,
    }


_PERCENTISH = re.compile(r"(percentage|rate)", re.IGNORECASE)


def format_for_display(key: str, value: Any) -> str:
    """Format values for UI display (counts vs % vs tuples)."""
    if value is None:
        return "N/A"
    if isinstance(value, tuple):
        return ", ".join("N/A" if v is None else str(v) for v in value)
    if _PERCENTISH.search(key):
        try:
            return f"{float(value):.2f}%"
        except (ValueError, TypeError):
            return str(value)
    return str(value)
