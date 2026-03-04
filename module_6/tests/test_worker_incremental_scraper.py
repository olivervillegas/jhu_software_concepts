from __future__ import annotations

import json
from pathlib import Path

import pytest


def test_load_all_json_array(tmp_path: Path):
    from src.worker.etl.incremental_scraper import load_all

    p = tmp_path / "data.json"
    p.write_text(json.dumps([{"a": 1}, {"b": 2}]), encoding="utf-8")
    rows = load_all(str(p))
    assert rows == [{"a": 1}, {"b": 2}]


def test_load_all_jsonl(tmp_path: Path):
    from src.worker.etl.incremental_scraper import load_all

    p = tmp_path / "data.jsonl"
    p.write_text('{"a":1}\n{"b":2}\n', encoding="utf-8")
    rows = load_all(str(p))
    assert rows == [{"a": 1}, {"b": 2}]


def test_load_all_missing_raises(tmp_path: Path):
    from src.worker.etl.incremental_scraper import load_all

    with pytest.raises(FileNotFoundError):
        load_all(str(tmp_path / "nope.json"))


def test_incremental_from_watermark():
    from src.worker.etl.incremental_scraper import incremental_from_watermark

    rows = [
        {"date_added": "2026-01-01", "x": 1},
        {"date_added": "2026-01-02", "x": 2},
        {"date_added": "bad-date", "x": 3},
    ]

    new_rows, new_last = incremental_from_watermark(rows, "2026-01-01")
    assert [r["x"] for r in new_rows] == [2]
    assert new_last == "2026-01-02"

    all_rows, last2 = incremental_from_watermark(rows, None)
    assert len(all_rows) == 2
    assert last2 == "2026-01-02"