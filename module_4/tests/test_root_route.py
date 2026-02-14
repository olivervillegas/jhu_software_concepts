import pytest

@pytest.mark.web
def test_root_route_returns_analysis(client):
    r = client.get("/")
    assert r.status_code == 200
    html = r.data.decode("utf-8")
    assert "Analysis" in html
