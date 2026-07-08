from fastapi.testclient import TestClient

from schedule_the_alamo import app


def test_index_serves_html() -> None:
    client = TestClient(app)
    resp = client.get("/")
    assert resp.status_code == 200
    assert "flatpickr" in resp.text
    assert "htmx" in resp.text
    assert "dates-container" in resp.text


def test_add_date() -> None:
    client = TestClient(app)
    resp = client.post("/dates/add", data={"date": "2026-07-01"})
    assert resp.status_code == 200
    assert "2026-07-01" in resp.text
    assert 'id="date-2026-07-01"' in resp.text
    assert "<select" in resp.text


def test_add_window() -> None:
    client = TestClient(app)
    resp = client.post("/dates/2026-07-01/window")
    assert resp.status_code == 200
    assert "time-window" in resp.text
    assert "09:00" in resp.text


def test_remove_window() -> None:
    client = TestClient(app)
    resp = client.delete("/dates/2026-07-01/window/0")
    assert resp.status_code == 200
    assert resp.text == ""


def test_multiple_dates_independent() -> None:
    client = TestClient(app)
    r1 = client.post("/dates/add", data={"date": "2026-07-01"})
    r2 = client.post("/dates/add", data={"date": "2026-07-02"})
    assert 'id="date-2026-07-01"' in r1.text
    assert 'id="date-2026-07-02"' in r2.text
    assert "windows-2026-07-01" in r1.text
    assert "windows-2026-07-02" in r2.text


def test_time_dropdowns_30min_increments() -> None:
    client = TestClient(app)
    resp = client.post("/dates/add", data={"date": "2026-07-01"})
    # Check 30-min increments exist
    assert "00:00" in resp.text
    assert "00:30" in resp.text
    assert "12:00" in resp.text
    assert "23:30" in resp.text
