from __future__ import annotations

import pytest


def test_analysis_computes_live_and_overlays_cached(env, monkeypatch):
    from src.web.app import flask_app as fa

    monkeypatch.setattr(fa, "compute_live_metrics", lambda db: {"A": 1, "B": 2})
    monkeypatch.setattr(fa, "format_for_display", lambda k, v: f"{k}={v}")
    monkeypatch.setattr(fa, "read_cached_metrics", lambda db: {"B": "CACHED", "C": "ONLYCACHED"})

    app = fa.create_app()
    client = app.test_client()

    resp = client.get("/analysis")
    assert resp.status_code == 200
    # Live metric A is present
    assert b"A=1" in resp.data
    # Cached overrides live for B
    assert b"B:" in resp.data
    assert b"CACHED" in resp.data
    # Cached-only key shows too
    assert b"ONLYCACHED" in resp.data


def test_pull_data_html_redirects_303(env, monkeypatch):
    from src.web.app import flask_app as fa

    calls = []
    monkeypatch.setattr(fa, "publish_task", lambda kind, payload=None: calls.append((kind, payload)))

    app = fa.create_app()
    client = app.test_client()

    # Browser-ish accept header
    resp = client.post("/pull-data", headers={"Accept": "text/html"})
    assert resp.status_code == 303
    assert resp.headers["Location"].endswith("/analysis?queued=scrape_new_data")
    assert calls == [("scrape_new_data", {})]


def test_pull_data_json_returns_202(env, monkeypatch):
    from src.web.app import flask_app as fa

    calls = []
    monkeypatch.setattr(fa, "publish_task", lambda kind, payload=None: calls.append((kind, payload)))

    app = fa.create_app()
    client = app.test_client()

    resp = client.post("/pull-data", headers={"Accept": "application/json"})
    assert resp.status_code == 202
    assert resp.json == {"status": "queued", "task": "scrape_new_data"}
    assert calls == [("scrape_new_data", {})]


def test_update_analysis_html_redirects_303(env, monkeypatch):
    from src.web.app import flask_app as fa

    calls = []
    monkeypatch.setattr(fa, "publish_task", lambda kind, payload=None: calls.append((kind, payload)))

    app = fa.create_app()
    client = app.test_client()

    resp = client.post("/update-analysis", headers={"Accept": "text/html"})
    assert resp.status_code == 303
    assert resp.headers["Location"].endswith("/analysis?queued=recompute_analytics")
    assert calls == [("recompute_analytics", {})]


def test_publish_failure_json_503(env, monkeypatch):
    from src.web.app import flask_app as fa

    def boom(*args, **kwargs):
        raise RuntimeError("rmq down")

    monkeypatch.setattr(fa, "publish_task", boom)

    app = fa.create_app()
    client = app.test_client()

    resp = client.post("/pull-data", headers={"Accept": "application/json"})
    assert resp.status_code == 503
    assert resp.json == {"error": "publish_failed"}


def test_publish_failure_html_503(env, monkeypatch):
    from src.web.app import flask_app as fa

    def boom(*args, **kwargs):
        raise RuntimeError("rmq down")

    monkeypatch.setattr(fa, "publish_task", boom)

    app = fa.create_app()
    client = app.test_client()

    resp = client.post("/update-analysis", headers={"Accept": "text/html"})
    assert resp.status_code == 503
    assert b"Publish failed" in resp.data