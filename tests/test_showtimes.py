import json
from datetime import datetime
from pathlib import Path
from typing import Any

from schedule_the_alamo.fetch import parse_calendar
from schedule_the_alamo.normalize import normalize_title

FIXTURE = Path(__file__).parent / "fixtures" / "calendar_2103.json"


def _load_fixture() -> dict[str, Any]:
    return json.loads(FIXTURE.read_text())


def test_parse_calendar_count() -> None:
    showings = parse_calendar(_load_fixture())
    assert len(showings) == 3


def test_parse_calendar_fields() -> None:
    s = parse_calendar(_load_fixture())[0]
    assert s.original_title == "BEAUTY AND THE BEAST IMAX"
    assert s.showtime == datetime(2026, 7, 1, 18, 0)
    assert s.runtime_minutes == 144
    assert s.location == "Lower Manhattan"
    assert s.format_name == "IMAX"


def test_title_normalization() -> None:
    assert normalize_title("BEAUTY AND THE BEAST IMAX") == "BEAUTY AND THE BEAST"
    assert normalize_title("THE MATRIX OC") == "THE MATRIX"
    assert normalize_title("DUNE Open Caption") == "DUNE"
    assert normalize_title("ALIEN 3D (2026)") == "ALIEN"
    assert normalize_title("NOPE Subtitled") == "NOPE"
    assert normalize_title("MOVIE CC") == "MOVIE"
    assert normalize_title("PARTY OF FIVE") == "PARTY OF FIVE"
    assert normalize_title("COOL FILM - IMAX 3D") == "COOL FILM"
    # Prefix formats
    assert normalize_title("Open Caption: TOY STORY 5") == "TOY STORY 5"
    assert normalize_title("70mm: DISCLOSURE DAY") == "DISCLOSURE DAY"
    assert normalize_title("35mm: BLADE RUNNER") == "BLADE RUNNER"
    assert normalize_title("IMAX: DUNE") == "DUNE"
    assert normalize_title("HDR by Barco: TOY STORY 5") == "TOY STORY 5"


def test_normalization_groups_variants() -> None:
    titles = {s.normalized_title for s in parse_calendar(_load_fixture())}
    assert "BEAUTY AND THE BEAST" in titles
    assert len(titles) == 2


def test_series_parsed() -> None:
    showings = parse_calendar(_load_fixture())
    terror = [s for s in showings if s.series_name]
    assert len(terror) == 1
    assert terror[0].series_name == "Terror Tuesday"
    assert terror[0].normalized_title == "THE BEYOND"


def test_missing_session_datetime_skipped() -> None:
    data = {
        "Calendar": {
            "Cinemas": [{
                "CinemaName": "Test",
                "Months": [{"Weeks": [{"Days": [{"Films": [{
                    "FilmName": "X",
                    "FilmRuntime": "90",
                    "Series": [{"SeriesName": None, "Formats": [
                        {"FormatName": "Digital", "Sessions": [
                            {"SessionDateTime": "2026-01-01T10:00:00"},
                            {},
                        ]}
                    ]}],
                }]}]}]}],
            }],
        }
    }
    showings = parse_calendar(data)
    assert len(showings) == 1


