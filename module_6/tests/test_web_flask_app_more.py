from __future__ import annotations


def test_pull_data_accept_star_treated_as_html(env, monkeypatch):
    from src.web.app import flask_app as fa

    monkeypatch.setattr(fa, "publish_task", lambda kind, payload=None: None)

    app = fa.create_app()
    client = app.test_client()

    resp = client.post("/pull-data", headers={"Accept": "*/*"})
    assert resp.status_code == 303
    assert "queued=scrape_new_data" in resp.headers["Location"]


def test_update_analysis_publish_failure_html_text(env, monkeypatch):
    from src.web.app import flask_app as fa

    def boom(*args, **kwargs):
        raise RuntimeError("rmq down")

    monkeypatch.setattr(fa, "publish_task", boom)

    app = fa.create_app()
    client = app.test_client()

    resp = client.post("/update-analysis", headers={"Accept": "text/html"})
    assert resp.status_code == 503
    assert b"Publish failed" in resp.data