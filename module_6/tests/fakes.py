from __future__ import annotations

from typing import Any, Callable, List, Optional, Tuple


class FakeCursor:
    def __init__(self, fetchone_queue: Optional[List[Any]] = None, fetchall_value=None):
        self.fetchone_queue = list(fetchone_queue or [])
        self.fetchall_value = fetchall_value
        self.executed: List[Tuple[str, tuple]] = []
        self.rowcount = 0

    def execute(self, stmt, params=()):
        self.executed.append((str(stmt), tuple(params)))

    def fetchone(self):
        if self.fetchone_queue:
            return self.fetchone_queue.pop(0)
        return None

    def fetchall(self):
        return self.fetchall_value if self.fetchall_value is not None else []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeConn:
    def __init__(self, cursor_factory: Callable[[], FakeCursor]):
        self._cursor_factory = cursor_factory
        self.committed = 0
        self.rolled_back = 0

    def cursor(self):
        return self._cursor_factory()

    def commit(self):
        self.committed += 1

    def rollback(self):
        self.rolled_back += 1

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeChannel:
    def __init__(self):
        self.calls: List[tuple] = []
        self.publish_ok = True
        self.raise_on_confirm = False

    def confirm_delivery(self):
        if self.raise_on_confirm:
            raise RuntimeError("no confirms")

    def exchange_declare(self, **kwargs):
        self.calls.append(("exchange_declare", kwargs))

    def queue_declare(self, **kwargs):
        self.calls.append(("queue_declare", kwargs))

    def queue_bind(self, **kwargs):
        self.calls.append(("queue_bind", kwargs))

    def basic_publish(self, **kwargs):
        self.calls.append(("basic_publish", kwargs))
        return self.publish_ok

    def basic_qos(self, **kwargs):
        self.calls.append(("basic_qos", kwargs))

    def basic_consume(self, **kwargs):
        self.calls.append(("basic_consume", kwargs))

    def start_consuming(self):
        self.calls.append(("start_consuming", {}))

    def basic_ack(self, **kwargs):
        self.calls.append(("basic_ack", kwargs))

    def basic_nack(self, **kwargs):
        self.calls.append(("basic_nack", kwargs))


class FakeRMQConn:
    def __init__(self, ch: FakeChannel):
        self._ch = ch
        self.closed = 0

    def channel(self):
        return self._ch

    def close(self):
        self.closed += 1