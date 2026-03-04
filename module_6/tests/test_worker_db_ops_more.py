from __future__ import annotations

from datetime import date

from fakes import FakeConn, FakeCursor


def test_clean_text_variants():
    from src.worker.etl import db_ops as d

    assert d.clean_text(None) is None
    assert d.clean_text("  hi  ") == "hi"
    assert d.clean_text("a\x00b") == "ab"
    assert d.clean_text("   ") is None


def test_safe_float_variants():
    from src.worker.etl import db_ops as d

    assert d.safe_float(None) is None
    assert d.safe_float(3) == 3.0
    assert d.safe_float(3.5) == 3.5
    assert d.safe_float("GRE: 330") == 330.0
    assert d.safe_float("nope") is None


def test_safe_date_variants():
    from src.worker.etl import db_ops as d

    assert d.safe_date(None) is None
    assert d.safe_date("2026-01-02") == date(2026, 1, 2)
    assert d.safe_date("bad") is None
    # invalid calendar date
    assert d.safe_date("2026-02-30") is None