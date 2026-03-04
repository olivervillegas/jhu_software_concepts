from __future__ import annotations

import json

import pytest

from fakes import FakeChannel, FakeRMQConn


def test_open_channel_declares_durable_entities(env, monkeypatch):
    import src.web.publisher as publisher

    ch = FakeChannel()
    rmq_conn = FakeRMQConn(ch)

    monkeypatch.setattr(publisher.pika, "BlockingConnection", lambda params: rmq_conn)

    conn, out_ch = publisher._open_channel()
    assert conn is rmq_conn
    assert out_ch is ch

    kinds = [c[0] for c in ch.calls]
    assert "exchange_declare" in kinds
    assert "queue_declare" in kinds
    assert "queue_bind" in kinds


def test_open_channel_confirm_delivery_optional(env, monkeypatch):
    import src.web.publisher as publisher

    ch = FakeChannel()
    ch.raise_on_confirm = True
    rmq_conn = FakeRMQConn(ch)

    monkeypatch.setattr(publisher.pika, "BlockingConnection", lambda params: rmq_conn)

    # should not raise if confirms aren't supported
    publisher._open_channel()


def test_publish_task_success_sets_persistent_and_closes(env, monkeypatch):
    import src.web.publisher as publisher

    ch = FakeChannel()
    rmq_conn = FakeRMQConn(ch)
    monkeypatch.setattr(publisher, "_open_channel", lambda: (rmq_conn, ch))

    publisher.publish_task("scrape_new_data", payload={"x": 1}, headers={"h": "v"})

    assert rmq_conn.closed == 1

    publish_calls = [c for c in ch.calls if c[0] == "basic_publish"]
    assert len(publish_calls) == 1

    kwargs = publish_calls[0][1]
    msg = json.loads(kwargs["body"].decode("utf-8"))
    assert msg["kind"] == "scrape_new_data"
    assert msg["payload"] == {"x": 1}

    props = kwargs["properties"]
    assert props.delivery_mode == 2
    assert props.headers == {"h": "v"}


def test_publish_task_publish_error_raises_and_closes(env, monkeypatch):
    import src.web.publisher as publisher

    ch = FakeChannel()

    def boom(**kwargs):
        raise RuntimeError("broker down")

    ch.basic_publish = boom  # override method
    rmq_conn = FakeRMQConn(ch)
    monkeypatch.setattr(publisher, "_open_channel", lambda: (rmq_conn, ch))

    with pytest.raises(RuntimeError, match="broker down"):
        publisher.publish_task("recompute_analytics")

    assert rmq_conn.closed == 1