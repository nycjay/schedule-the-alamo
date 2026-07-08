from datetime import datetime
from pathlib import Path

import pytest

import schedule_the_alamo.state as _state_mod
from schedule_the_alamo.filter import filter_showings
from schedule_the_alamo.models import Showing
from schedule_the_alamo.state import UserState, load_state, save_state


def _showing(
    title: str = "MOVIE",
    hour: int = 14,
    location: str = "Lower Manhattan",
) -> Showing:
    return Showing(
        normalized_title=title,
        original_title=title,
        showtime=datetime(2026, 7, 1, hour, 0),
        runtime_minutes=90,
        location=location,
        format_name="Digital",
        series_name=None,
    )


W_START = datetime(2026, 7, 1, 9, 0)
W_END = datetime(2026, 7, 1, 20, 0)


def test_dismiss_removes_from_results() -> None:
    showings = [_showing("A"), _showing("B", hour=15)]
    result = filter_showings(
        showings, W_START, W_END, dismissed={"A"}
    )
    titles = [s.normalized_title for s in result]
    assert "A" not in titles
    assert "B" in titles


def test_wishlist_sorts_to_top() -> None:
    showings = [_showing("A", hour=14), _showing("B", hour=12)]
    result = filter_showings(
        showings, W_START, W_END, wishlisted={"A"}
    )
    # Sort by time is purely chronological; wishlisted no longer floats
    assert result[0].normalized_title == "B"


def test_undo_dismiss_restores() -> None:
    state = UserState()
    state.dismiss("A")
    assert "A" in state.dismissed
    state.undismiss("A")
    assert "A" not in state.dismissed


def test_undo_wishlist_restores() -> None:
    state = UserState()
    state.wishlist("A")
    assert "A" in state.wishlisted
    state.unwishlist("A")
    assert "A" not in state.wishlisted


def test_state_json_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "state.json"
    state = UserState(
        dismissed={"BAD MOVIE"},
        wishlisted={"GOOD MOVIE"},
    )
    save_state(state, path)
    loaded = load_state(path)
    assert loaded.dismissed == {"BAD MOVIE"}
    assert loaded.wishlisted == {"GOOD MOVIE"}


def test_load_state_missing_file(tmp_path: Path) -> None:
    path = tmp_path / "nonexistent.json"
    state = load_state(path)
    assert state.dismissed == set()
    assert state.wishlisted == set()


# --- Integration tests: actual HTTP endpoints ---


@pytest.fixture(autouse=False)
def _tmp_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "state.json"
    monkeypatch.setattr(_state_mod, "STATE_FILE", path)
    return path


def test_endpoint_wishlist(_tmp_state: Path) -> None:
    from fastapi.testclient import TestClient

    from schedule_the_alamo import app

    c = TestClient(app)
    resp = c.post("/wishlist", data={"title": "MOVIE"})
    assert resp.status_code == 200
    loaded = load_state(_tmp_state)
    assert "MOVIE" in loaded.wishlisted


def test_endpoint_dismiss(_tmp_state: Path) -> None:
    from fastapi.testclient import TestClient

    from schedule_the_alamo import app

    c = TestClient(app)
    resp = c.post("/dismiss", data={"title": "BAD"})
    assert resp.status_code == 200
    assert "Dismissed" in resp.text
    assert "Undo" in resp.text
    loaded = load_state(_tmp_state)
    assert "BAD" in loaded.dismissed
