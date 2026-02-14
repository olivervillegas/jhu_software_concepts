import pytest

@pytest.mark.analysis
def test_answer_labels_present(client):
    client.post("/pull-data")  # ensure data exists
    html = client.get("/analysis").data.decode("utf-8")
    assert "Answer:" in html

@pytest.mark.analysis
def test_percentages_two_decimals(client, pct_regex):
    client.post("/pull-data")  # ensure data exists
    html = client.get("/analysis").data.decode("utf-8")
    assert pct_regex.search(html), "Expected at least one percentage formatted with two decimals, like 39.28%."
