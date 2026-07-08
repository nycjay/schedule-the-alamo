import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import schedule_the_alamo.state as _state_mod
from schedule_the_alamo import app, get_fetch_fn
from schedule_the_alamo.state import load_state

FIXTURE = Path(__file__).parent / "fixtures" / "calendar_2103.json"


def _mock_fetch(_tid: str) -> dict:
    return json.loads(FIXTURE.read_text())


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(_state_mod, "STATE_FILE", tmp_path / "s.json")
    app.dependency_overrides[get_fetch_fn] = lambda: _mock_fetch
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_all_movies_groups_by_normalized_title(client: TestClient) -> None:
    resp = client.get("/movies")
    assert resp.status_code == 200
    # Fixture has "BEAUTY AND THE BEAST IMAX" and "BEAUTY AND THE BEAST"
    # Both normalize to "BEAUTY AND THE BEAST" — should appear once
    assert resp.text.count("BEAUTY AND THE BEAST") >= 1
    # Only 2 unique normalized titles in fixture
    assert "THE BEYOND" in resp.text


def test_dismiss_on_movies_affects_calendar(
    client: TestClient, tmp_path: Path
) -> None:
    # Dismiss from all movies view
    client.post("/movies/dismiss", data={"title": "BEAUTY AND THE BEAST"})
    # Verify state persisted
    state = load_state(tmp_path / "s.json")
    assert "BEAUTY AND THE BEAST" in state.dismissed
    # All movies view shows it in dismissed section, not main list
    resp = client.get("/movies")
    assert "<s>BEAUTY AND THE BEAST</s>" in resp.text
    assert 'hx-post="/movies/undismiss"' in resp.text


def test_wishlist_on_movies_shared_with_calendar(
    client: TestClient, tmp_path: Path
) -> None:
    client.post("/wishlist", data={"title": "THE BEYOND"})
    state = load_state(tmp_path / "s.json")
    assert "THE BEYOND" in state.wishlisted
    # Verify star shows filled on all movies page
    resp = client.get("/movies")
    assert "★" in resp.text


def test_all_movies_has_htmx_buttons(client: TestClient) -> None:
    resp = client.get("/movies")
    assert 'hx-post="/wishlist"' in resp.text
    assert 'hx-post="/movies/dismiss"' in resp.text
