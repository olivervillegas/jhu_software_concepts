from __future__ import annotations

def test_connect_calls_psycopg(monkeypatch):
    from src.web.app import db as mod

    called = {}

    def fake_connect(url):
        called["url"] = url
        return "CONN"

    monkeypatch.setattr(mod.psycopg, "connect", fake_connect)

    out = mod.connect(mod.DB(url="postgresql://x"))
    assert out == "CONN"
    assert called["url"] == "postgresql://x"