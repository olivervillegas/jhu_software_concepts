import pytest
from bs4 import BeautifulSoup

@pytest.mark.web
def test_app_factory_has_required_routes(app):
    rules = {r.rule for r in app.url_map.iter_rules()}
    assert "/analysis" in rules
    assert "/pull-data" in rules
    assert "/update-analysis" in rules

@pytest.mark.web
def test_get_analysis_page_loads_and_has_components(client):
    resp = client.get("/analysis")
    assert resp.status_code == 200
    soup = BeautifulSoup(resp.data, "html.parser")

    assert soup.find(attrs={"data-testid": "pull-data-btn"}) is not None
    assert soup.find(attrs={"data-testid": "update-analysis-btn"}) is not None

    text = soup.get_text(" ", strip=True)
    assert "Analysis" in text
    assert "Answer:" in text
