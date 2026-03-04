from __future__ import annotations


def test_run_main_calls_app_run(monkeypatch):
    import src.web.run as run_mod

    class FakeApp:
        def __init__(self):
            self.called = False
            self.kwargs = None

        def run(self, **kwargs):
            self.called = True
            self.kwargs = kwargs

    fake_app = FakeApp()

    monkeypatch.setattr(run_mod, "create_app", lambda: fake_app)
    monkeypatch.setenv("FLASK_DEBUG", "1")

    rc = run_mod.main()
    assert rc == 0
    assert fake_app.called is True
    assert fake_app.kwargs == {"host": "0.0.0.0", "port": 8080, "debug": True}