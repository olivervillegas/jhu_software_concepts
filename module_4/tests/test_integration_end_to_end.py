import pytest
from bs4 import BeautifulSoup

@pytest.mark.integration
def test_end_to_end_pull_update_render(client):
    r1 = client.post("/pull-data")
    assert r1.status_code == 200
    r2 = client.post("/update-analysis")
    assert r2.status_code == 200

    r3 = client.get("/analysis")
    assert r3.status_code == 200
    soup = BeautifulSoup(r3.data, "html.parser")
    text = soup.get_text(" ", strip=True)
    assert "Analysis" in text
    assert "Answer:" in text

@pytest.mark.integration
def test_multiple_pulls_overlap_consistent(client):
    a = client.post("/pull-data").get_json()["total_rows"]
    b = client.post("/pull-data").get_json()["total_rows"]
    assert a == b
