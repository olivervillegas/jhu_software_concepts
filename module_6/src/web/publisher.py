from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

import pika

from src.common.amqp import EXCHANGE, QUEUE, ROUTING_KEY


def _open_channel() -> Tuple[pika.BlockingConnection,
                             pika.adapters.blocking_connection.BlockingChannel]:
    """
    Open a connection + channel and declare durable entities.
    Returns (conn, ch). Caller must close conn.
    """
    url = os.environ["RABBITMQ_URL"]
    params = pika.URLParameters(url)
    conn = pika.BlockingConnection(params)
    ch = conn.channel()

    # Optional publisher confirms (recommended)
    try:
        ch.confirm_delivery()
    except Exception:
        # If broker/channel doesn't support confirms, it's okay to proceed.
        pass

    ch.exchange_declare(exchange=EXCHANGE, exchange_type="direct", durable=True)
    ch.queue_declare(queue=QUEUE, durable=True)
    ch.queue_bind(exchange=EXCHANGE, queue=QUEUE, routing_key=ROUTING_KEY)
    return conn, ch


def publish_task(kind: str,
                 payload: Optional[Dict[str, Any]] = None,
                 headers: Optional[Dict[str, Any]] = None) -> None:
    """
    Publish a durable (persistent) task message. Raises on failure.
    """
    body = json.dumps(
        {
            "kind": kind,
            "ts": datetime.now(timezone.utc).isoformat(),
            "payload": payload or {},
        },
        separators=(",", ":"),
    ).encode("utf-8")

    conn, ch = _open_channel()
    try:
        ch.basic_publish(
            exchange=EXCHANGE,
            routing_key=ROUTING_KEY,
            body=body,
            properties=pika.BasicProperties(
                delivery_mode=2,  # persistent
                headers=headers or {},
                content_type="application/json",
            ),
            mandatory=False,
        )
        # If you enabled confirms via ch.confirm_delivery(), you can optionally enforce:
        if getattr(ch, "wait_for_confirms", None):
            if not ch.wait_for_confirms(): # pragma: no cover
                raise RuntimeError("Publish not confirmed")
    finally:
        conn.close()
