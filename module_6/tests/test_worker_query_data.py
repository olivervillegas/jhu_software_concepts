from __future__ import annotations

from fakes import FakeConn, FakeCursor


def test_recompute_metrics_stringifies():
    from src.worker.etl import query_data as q

    # Provide fetchone values in the order called by recompute_metrics():
    # fall_2026 count -> 10
    # intl_pct -> 12.34
    # avgs row -> (3.8, 320, 160, 4)
    # accept_overall -> 50.0
    cur = FakeCursor(fetchone_queue=[(10,), (12.34,), (3.8, 320, 160, 4), (50.0,)])
    conn = FakeConn(lambda: cur)

    out = q.recompute_metrics(conn)

    assert out["Fall 2026 Applicants"] == "10"
    assert out["International Percentage"].endswith("%")
    assert out["International Percentage"] == "12.34%"

    avg_key = "Average GPA / GRE / GRE-V / GRE-AW (non-null)"
    assert avg_key in out
    assert out[avg_key] == "3.8, 320, 160, 4"

    assert out["Acceptance Rate Overall (all terms)"] == "50.00%"