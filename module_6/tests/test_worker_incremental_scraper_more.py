from __future__ import annotations

from src.worker.etl.incremental_scraper import _parse_date


def test_parse_date_formats():
    assert _parse_date("2026-01-31").isoformat() == "2026-01-31"
    assert _parse_date("January 31, 2026").isoformat() == "2026-01-31"
    assert _parse_date("not a date") is None
    assert _parse_date(None) is None