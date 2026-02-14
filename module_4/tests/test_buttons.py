import pytest

@pytest.mark.buttons
def test_post_pull_data_returns_200_and_triggers_loader(client):
    resp = client.post("/pull-data")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["ok"] is True
    assert data["total_rows"] >= 1

@pytest.mark.buttons
def test_post_update_analysis_returns_200_when_not_busy(client):
    resp = client.post("/update-analysis")
    assert resp.status_code == 200
    assert resp.get_json()["ok"] is True

@pytest.mark.buttons
def test_busy_gating_update_analysis(app, client):
    app.busy_flag.value = True
    resp = client.post("/update-analysis")
    assert resp.status_code == 409
    assert resp.get_json() == {"busy": True}

@pytest.mark.buttons
def test_busy_gating_pull_data(app, client):
    app.busy_flag.value = True
    resp = client.post("/pull-data")
    assert resp.status_code == 409
    assert resp.get_json() == {"busy": True}
