from __future__ import annotations

import types

from fakes import FakeConn, FakeCursor


def test_clamp_limit():
    from src.web.app import query_data as q

    assert q.clamp_limit(None) == 100
    assert q.clamp_limit(0) == 1
    assert q.clamp_limit(999) == 100
    assert q.clamp_limit(5) == 5


def test_format_for_display():
    from src.web.app import query_data as q

    assert q.format_for_display("anything", None) == "N/A"
    assert q.format_for_display("tuple", (None, 2)) == "N/A, 2"
    assert q.format_for_display("Acceptance Rate", 12.3456) == "12.35%"
    assert q.format_for_display("Count", 7) == "7"


def test_read_cached_metrics():
    from src.web.app import query_data as q

    cur = FakeCursor(fetchall_value=[("A", "1"), ("B", "2")])
    conn = FakeConn(lambda: cur)

    # patch connect() to return our fake connection
    q.connect = lambda db: conn  # type: ignore[assignment]

    out = q.read_cached_metrics(q.DB(url="x"))
    assert out == {"A": "1", "B": "2"}
    assert "SELECT key, value FROM analytics_cache" in cur.executed[0][0]


def test_compute_live_metrics_smoke(monkeypatch):
    """
    Avoid running real DB: monkeypatch run_scalar/run_row to deterministic values.
    Ensures compute_live_metrics executes and returns expected keys.
    """
    from src.web.app import query_data as q

    monkeypatch.setattr(q, "run_scalar", lambda db, stmt, params=(): 1)
    monkeypatch.setattr(q, "run_row", lambda db, stmt, params=(): (3.5, 320.0, 160.0, 4.0))

    out = q.compute_live_metrics(q.DB(url="x"))
    # verify a couple representative keys exist
    assert "Fall 2026 Applicants" in out
    assert "Average GPA / GRE / GRE-V / GRE-AW (non-null)" in out