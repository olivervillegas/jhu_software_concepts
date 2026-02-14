import pytest
from src.db import connect
from src.query_data import get_results, EXPECTED_KEYS

@pytest.mark.db
def test_insert_on_pull_before_empty_after_has_rows(db, client):
    with connect(db) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM applicants;")
            assert cur.fetchone()[0] == 0

    r = client.post("/pull-data")
    assert r.status_code == 200

    with connect(db) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM applicants;")
            assert cur.fetchone()[0] >= 1
            cur.execute("SELECT COUNT(*) FROM applicants WHERE url IS NULL;")
            assert cur.fetchone()[0] == 0

@pytest.mark.db
def test_idempotency_duplicate_rows_do_not_duplicate(db, client):
    a = client.post("/pull-data").get_json()["total_rows"]
    b = client.post("/pull-data").get_json()["total_rows"]
    assert a == b

@pytest.mark.db
def test_query_function_returns_expected_keys(db):
    results = get_results(db)
    for k in EXPECTED_KEYS:
        assert k in results
