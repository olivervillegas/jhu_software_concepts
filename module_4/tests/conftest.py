import os
import pytest
from src.db import DB, ensure_schema, truncate_all

@pytest.fixture
def test_db():
    url = os.environ["DATABASE_URL"]  # workflow must set this
    db = DB(url=url)
    ensure_schema(db)
    truncate_all(db)
    return db
