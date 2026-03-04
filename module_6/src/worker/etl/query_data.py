from __future__ import annotations

from typing import Any, Dict

from psycopg import sql
import psycopg

APPLICANTS_TABLE = "applicants"


def _scalar(conn: psycopg.Connection, stmt: sql.SQL, params=()) -> Any:
    with conn.cursor() as cur:
        cur.execute(stmt, params)
        row = cur.fetchone()
        return row[0] if row else None


def _row(conn: psycopg.Connection, stmt: sql.SQL, params=()):
    with conn.cursor() as cur:
        cur.execute(stmt, params)
        return cur.fetchone()


def recompute_metrics(conn: psycopg.Connection) -> Dict[str, str]:
    """
    This function recomputes metrics.
    """
    tbl = sql.Identifier(APPLICANTS_TABLE)

    fall_2026 = _scalar(
        conn,
        sql.SQL("SELECT COUNT(*) FROM {t} WHERE TRIM(term) = %s LIMIT 1;").format(t=tbl),
        ("Fall 2026",),
    )

    intl_pct = _scalar(
        conn,
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

    avgs = _row(
        conn,
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

    accept_overall = _scalar(
        conn,
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

    # stringify for cache
    def s(x: object) -> str:
        if x is None: # pragma: no cover
            return "N/A"
        if isinstance(x, tuple):
            return ", ".join("N/A" if v is None else str(v) for v in x)
        return str(x)

    return {
        "Fall 2026 Applicants": s(fall_2026),
        "International Percentage": f"{float(intl_pct):.2f}%" if intl_pct is not None else "N/A",
        "Average GPA / GRE / GRE-V / GRE-AW (non-null)": s(avgs),
        "Acceptance Rate Overall (all terms)": f"{float(accept_overall):.2f}%" 
          if accept_overall is not None else "N/A",
    }
