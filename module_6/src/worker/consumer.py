from __future__ import annotations

import json
import os
from typing import Any, Callable, Dict, Tuple

import pika
import psycopg

from src.worker.etl.db_ops import (
    insert_applicants,
    read_watermark,
    upsert_analytics_cache,
    write_watermark,
)
from src.worker.etl.incremental_scraper import incremental_from_watermark, load_all
from src.worker.etl.query_data import recompute_metrics

from src.common.amqp import EXCHANGE, QUEUE, ROUTING_KEY


def _open_rmq_channel() -> Tuple[pika.BlockingConnection,
                                 pika.adapters.blocking_connection.BlockingChannel]:
    """Connect to RabbitMQ, declare durable entities, and set prefetch=1."""
    url = os.environ["RABBITMQ_URL"]
    params = pika.URLParameters(url)
    conn = pika.BlockingConnection(params)
    ch = conn.channel()

    ch.exchange_declare(exchange=EXCHANGE, exchange_type="direct", durable=True)
    ch.queue_declare(queue=QUEUE, durable=True)
    ch.queue_bind(exchange=EXCHANGE, queue=QUEUE, routing_key=ROUTING_KEY)
    ch.basic_qos(prefetch_count=1)

    return conn, ch


def _open_db() -> psycopg.Connection:
    """Open a database connection using DATABASE_URL."""
    dsn = os.environ["DATABASE_URL"]
    return psycopg.connect(dsn)


def handle_scrape_new_data(conn: psycopg.Connection, payload: Dict[str, Any]) -> None:
    """Incrementally ingest new rows from a local JSON file using a watermark."""
    seed_json = os.environ.get("SEED_JSON", "/data/applicant_data.json")
    source = os.environ.get("WATERMARK_SOURCE", "applicant_data")

    since = payload.get("since")
    if since is None:
        since = read_watermark(conn, source)

    rows = load_all(seed_json)
    new_rows, new_last_seen = incremental_from_watermark(rows, since)

    if not new_rows:
        return

    _ = insert_applicants(conn, new_rows)

    if new_last_seen is not None: # pragma: no cover
        write_watermark(conn, source, new_last_seen)

    metrics = recompute_metrics(conn)
    upsert_analytics_cache(conn, metrics)


def handle_recompute_analytics(conn: psycopg.Connection, payload: Dict[str, Any]) -> None:
    """Recompute cached analytics."""
    _ = payload
    metrics = recompute_metrics(conn)
    upsert_analytics_cache(conn, metrics)


TASKS: Dict[str, Callable[[psycopg.Connection, Dict[str, Any]], None]] = {
    "scrape_new_data": handle_scrape_new_data,
    "recompute_analytics": handle_recompute_analytics,
}


def _on_message(ch, method, properties, body: bytes) -> None:
    """
    Consume one task message. ACK only after successful DB commit.
    On failure: rollback and NACK(requeue=False).
    """
    _ = properties
    kind = "<unknown>"
    try:
        msg = json.loads(body.decode("utf-8"))
        kind = msg.get("kind") or "<missing-kind>"
        payload = msg.get("payload") or {}

        if kind not in TASKS:
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return

        with _open_db() as dbconn:
            try:
                TASKS[kind](dbconn, payload)
                dbconn.commit()
            except Exception:  # pylint: disable=broad-exception-caught
                dbconn.rollback()
                raise

        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception:  # pylint: disable=broad-exception-caught
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def main() -> int:
    """Worker process main loop: connect and consume."""
    conn, ch = _open_rmq_channel()
    try:
        ch.basic_consume(queue=QUEUE, on_message_callback=_on_message, auto_ack=False)
        ch.start_consuming()
    finally:
        try:
            conn.close()
        except Exception:  # pragma: no cover
            pass
    return 0 # pragma: no cover


if __name__ == "__main__":
    raise SystemExit(main())
