from __future__ import annotations

from fakes import FakeConn, FakeCursor


def test_read_write_watermark():
    from src.worker.etl import db_ops as d

    # read_watermark returns existing value
    cur1 = FakeCursor(fetchone_queue=[("2026-01-01",)])
    conn1 = FakeConn(lambda: cur1)
    assert d.read_watermark(conn1, "src") == "2026-01-01"
    assert "SELECT last_seen" in cur1.executed[0][0]
    assert cur1.executed[0][1] == ("src",)

    # write watermark issues upsert
    cur2 = FakeCursor()
    conn2 = FakeConn(lambda: cur2)
    d.write_watermark(conn2, "src", "2026-01-02")
    sql_text, params = cur2.executed[0]
    assert "INSERT INTO ingestion_watermarks" in sql_text
    assert params == ("src", "2026-01-02")


def test_insert_applicants_uses_parameters_and_conflict():
    from src.worker.etl import db_ops as d

    cur = FakeCursor()
    # emulate rowcount increments (two inserts)
    def cursor_factory():
        return cur

    conn = FakeConn(cursor_factory)

    rows = [
        {"program": "P", "date_added": "2026-01-01", "url": "u1"},
        {"program": "P", "date_added": "2026-01-02", "url": "u2"},
    ]

    # monkey rowcount behavior
    orig_execute = cur.execute
    def execute(stmt, params=()):
        orig_execute(stmt, params)
        cur.rowcount = 1
    cur.execute = execute

    inserted = d.insert_applicants(conn, rows)
    assert inserted == 2

    stmt_text, params0 = cur.executed[0]
    assert "ON CONFLICT (url) DO NOTHING" in stmt_text
    # params should be a tuple, not string interpolation
    assert isinstance(params0, tuple)
    assert "u1" in params0


def test_upsert_analytics_cache():
    from src.worker.etl import db_ops as d

    cur = FakeCursor()
    conn = FakeConn(lambda: cur)

    d.upsert_analytics_cache(conn, {"A": "1", "B": "2"})
    assert len(cur.executed) == 2
    assert "INSERT INTO analytics_cache" in cur.executed[0][0]