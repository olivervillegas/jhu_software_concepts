from __future__ import annotations

from fakes import FakeConn, FakeCursor


def test_run_scalar_and_run_row_execute(monkeypatch):
    from src.web.app import query_data as q

    # scalar: fetchone returns (42,)
    cur_scalar = FakeCursor(fetchone_queue=[(42,)])
    conn_scalar = FakeConn(lambda: cur_scalar)

    monkeypatch.setattr(q, "connect", lambda db: conn_scalar)

    out = q.run_scalar(q.DB(url="x"), q.sql.SQL("SELECT 1 LIMIT 1;"))
    assert out == 42
    assert "SELECT 1" in cur_scalar.executed[0][0]

    # row: fetchone returns (1,2)
    cur_row = FakeCursor(fetchone_queue=[(1, 2)])
    conn_row = FakeConn(lambda: cur_row)

    monkeypatch.setattr(q, "connect", lambda db: conn_row)

    out2 = q.run_row(q.DB(url="x"), q.sql.SQL("SELECT 1,2 LIMIT 1;"))
    assert out2 == (1, 2)


def test_format_for_display_percent_fallback():
    from src.web.app import query_data as q

    # If value can't be converted to float, fallback to str(value)
    out = q.format_for_display("Acceptance Rate", "not-a-number")
    assert out == "not-a-number"