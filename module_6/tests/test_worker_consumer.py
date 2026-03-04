from __future__ import annotations

import json
import types

import pytest

from fakes import FakeChannel, FakeConn, FakeCursor, FakeRMQConn


class Method:
    def __init__(self, tag=1):
        self.delivery_tag = tag


def test_open_rmq_channel_declares_and_qos(env, monkeypatch):
    import src.worker.consumer as c

    ch = FakeChannel()
    rmq_conn = FakeRMQConn(ch)

    monkeypatch.setattr(c.pika, "BlockingConnection", lambda params: rmq_conn)

    conn, out_ch = c._open_rmq_channel()
    assert conn is rmq_conn
    assert out_ch is ch

    kinds = [x[0] for x in ch.calls]
    assert "exchange_declare" in kinds
    assert "queue_declare" in kinds
    assert "queue_bind" in kinds
    assert ("basic_qos", {"prefetch_count": 1}) in ch.calls


def test_open_db_calls_psycopg(env, monkeypatch):
    import src.worker.consumer as c

    called = {}

    def fake_connect(dsn):
        called["dsn"] = dsn
        return "DBCONN"

    monkeypatch.setattr(c.psycopg, "connect", fake_connect)
    monkeypatch.setenv("DATABASE_URL", "postgresql://db")

    out = c._open_db()
    assert out == "DBCONN"
    assert called["dsn"] == "postgresql://db"


def test_handle_scrape_new_data_uses_payload_since(env, monkeypatch):
    import src.worker.consumer as c

    # No real file reading; stub the pipeline
    monkeypatch.setenv("SEED_JSON", "/data/applicant_data.json")
    monkeypatch.setenv("WATERMARK_SOURCE", "applicant_data")

    monkeypatch.setattr(c, "read_watermark", lambda conn, source: "SHOULD_NOT_USE")
    monkeypatch.setattr(c, "load_all", lambda path: [{"date_added": "2026-01-02", "url": "u"}])
    monkeypatch.setattr(c, "incremental_from_watermark", lambda rows, since: (rows, "2026-01-02"))

    calls = {"insert": 0, "wm": 0, "cache": 0}
    monkeypatch.setattr(c, "insert_applicants", lambda conn, rows: calls.__setitem__("insert", calls["insert"] + 1) or 1)
    monkeypatch.setattr(c, "write_watermark", lambda conn, source, ls: calls.__setitem__("wm", calls["wm"] + 1))
    monkeypatch.setattr(c, "recompute_metrics", lambda conn: {"K": "V"})
    monkeypatch.setattr(c, "upsert_analytics_cache", lambda conn, m: calls.__setitem__("cache", calls["cache"] + 1))

    conn = FakeConn(lambda: FakeCursor())
    c.handle_scrape_new_data(conn, payload={"since": "2026-01-01"})

    assert calls["insert"] == 1
    assert calls["wm"] == 1
    assert calls["cache"] == 1


def test_handle_scrape_new_data_no_new_rows_returns(env, monkeypatch):
    import src.worker.consumer as c

    monkeypatch.setattr(c, "read_watermark", lambda conn, source: None)
    monkeypatch.setattr(c, "load_all", lambda path: [])
    monkeypatch.setattr(c, "incremental_from_watermark", lambda rows, since: ([], None))

    called = {"insert": 0}
    monkeypatch.setattr(c, "insert_applicants", lambda conn, rows: called.__setitem__("insert", 1))

    conn = FakeConn(lambda: FakeCursor())
    c.handle_scrape_new_data(conn, payload={})

    assert called["insert"] == 0


def test_handle_recompute_analytics_calls_cache(env, monkeypatch):
    import src.worker.consumer as c

    monkeypatch.setattr(c, "recompute_metrics", lambda conn: {"A": "1"})
    called = {"upsert": 0}
    monkeypatch.setattr(c, "upsert_analytics_cache", lambda conn, m: called.__setitem__("upsert", called["upsert"] + 1))

    conn = FakeConn(lambda: FakeCursor())
    c.handle_recompute_analytics(conn, payload={"x": "ignored"})
    assert called["upsert"] == 1


def test_on_message_unknown_kind_nacks_no_requeue(monkeypatch):
    import src.worker.consumer as c

    ch = FakeChannel()
    method = Method(7)

    body = json.dumps({"kind": "nope", "payload": {}}).encode("utf-8")
    c._on_message(ch, method, None, body)

    nacks = [x for x in ch.calls if x[0] == "basic_nack"]
    assert len(nacks) == 1
    assert nacks[0][1]["delivery_tag"] == 7
    assert nacks[0][1]["requeue"] is False


def test_on_message_missing_kind_nacks(monkeypatch):
    import src.worker.consumer as c

    ch = FakeChannel()
    method = Method(8)

    body = json.dumps({"payload": {}}).encode("utf-8")
    c._on_message(ch, method, None, body)

    nacks = [x for x in ch.calls if x[0] == "basic_nack"]
    assert len(nacks) == 1
    assert nacks[0][1]["delivery_tag"] == 8
    assert nacks[0][1]["requeue"] is False


def test_on_message_bad_json_nacks(monkeypatch):
    import src.worker.consumer as c

    ch = FakeChannel()
    method = Method(9)

    c._on_message(ch, method, None, b"not-json")

    nacks = [x for x in ch.calls if x[0] == "basic_nack"]
    assert len(nacks) == 1
    assert nacks[0][1]["delivery_tag"] == 9


def test_on_message_success_commits_then_acks(monkeypatch):
    import src.worker.consumer as c

    ch = FakeChannel()
    method = Method(1)

    cur = FakeCursor()
    dbconn = FakeConn(lambda: cur)

    monkeypatch.setattr(c, "_open_db", lambda: dbconn)
    monkeypatch.setattr(c, "TASKS", {"scrape_new_data": lambda conn, payload: None})

    body = json.dumps({"kind": "scrape_new_data", "payload": {}}).encode("utf-8")
    c._on_message(ch, method, None, body)

    assert dbconn.committed == 1
    assert dbconn.rolled_back == 0

    acks = [x for x in ch.calls if x[0] == "basic_ack"]
    assert len(acks) == 1
    assert acks[0][1]["delivery_tag"] == 1


def test_on_message_handler_error_rolls_back_and_nacks(monkeypatch):
    import src.worker.consumer as c

    ch = FakeChannel()
    method = Method(3)

    cur = FakeCursor()
    dbconn = FakeConn(lambda: cur)

    monkeypatch.setattr(c, "_open_db", lambda: dbconn)

    def boom(conn, payload):
        raise RuntimeError("fail")

    monkeypatch.setattr(c, "TASKS", {"recompute_analytics": boom})

    body = json.dumps({"kind": "recompute_analytics", "payload": {}}).encode("utf-8")
    c._on_message(ch, method, None, body)

    assert dbconn.committed == 0
    assert dbconn.rolled_back == 1

    nacks = [x for x in ch.calls if x[0] == "basic_nack"]
    assert len(nacks) == 1
    assert nacks[0][1]["delivery_tag"] == 3
    assert nacks[0][1]["requeue"] is False


def test_main_closes_connection(monkeypatch):
    import src.worker.consumer as c

    ch = FakeChannel()

    class Conn:
        def __init__(self):
            self.closed = 0

        def close(self):
            self.closed += 1

    conn = Conn()

    def stop():
        raise KeyboardInterrupt()

    ch.start_consuming = stop
    monkeypatch.setattr(c, "_open_rmq_channel", lambda: (conn, ch))

    with pytest.raises(KeyboardInterrupt):
        c.main()

    assert conn.closed == 1