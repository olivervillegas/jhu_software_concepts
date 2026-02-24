import pytest

from src.etl import safe_date
from src.flask_app import create_app


def test_safe_date_no_match_returns_none():
    assert safe_date("not-a-date") is None


def test_safe_date_value_error_returns_none():
    # Matches regex but invalid calendar date -> triggers ValueError branch
    assert safe_date("2026-02-31") is None
