from __future__ import annotations

import os
from io import StringIO

import pytest


def test_load_data_main_prints(env, monkeypatch, capsys):
    import src.db.load_data as ld

    monkeypatch.setenv("DATABASE_URL", "postgresql://x")
    monkeypatch.setenv("SEED_JSON", "/tmp/seed.json")

    rc = ld.main()
    assert rc == 0

    out = capsys.readouterr().out
    assert "scrape_new_data" in out
    assert "DATABASE_URL=postgresql://x" in out
    assert "SEED_JSON=/tmp/seed.json" in out