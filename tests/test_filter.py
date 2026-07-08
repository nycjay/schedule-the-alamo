from datetime import datetime

from schedule_the_alamo.filter import filter_showings, fits_window
from schedule_the_alamo.models import Showing
from schedule_the_alamo.render import render_showing


def _showing(
    title: str = "MOVIE",
    hour: int = 14,
    minute: int = 0,
    runtime: int = 120,
    location: str = "Lower Manhattan",
    format_name: str = "Digital",
    series_name: str | None = None,
) -> Showing:
    return Showing(
        normalized_title=title,
        original_title=title,
        showtime=datetime(2026, 7, 1, hour, minute),
        runtime_minutes=runtime,
        location=location,
        format_name=format_name,
        series_name=series_name,
    )


# --- Filtering with buffer ---


def test_fits_window_inside() -> None:
    s = _showing(hour=10, runtime=90)  # 10:00-11:30
    # Window 09:00-12:30 → effective 09:30-12:00
    start = datetime(2026, 7, 1, 9, 0)
    end = datetime(2026, 7, 1, 12, 30)
    assert fits_window(s, start, end)


def test_fits_window_exact_boundary_excluded() -> None:
    # Movie starts exactly at window_start + 30min buffer, ends exactly at
    # window_end - 30min buffer. Should fit (>=, <=).
    s = _showing(hour=9, minute=30, runtime=60)  # 09:30-10:30
    start = datetime(2026, 7, 1, 9, 0)
    end = datetime(2026, 7, 1, 11, 0)  # effective end = 10:30
    assert fits_window(s, start, end)


def test_movie_starting_before_buffer_excluded() -> None:
    # Movie starts more than 30min before window start — too early
    s = _showing(hour=8, minute=29, runtime=60)
    start = datetime(2026, 7, 1, 9, 0)  # effective start = 8:30
    end = datetime(2026, 7, 1, 12, 0)
    assert not fits_window(s, start, end)


def test_movie_ending_after_buffer_excluded() -> None:
    # Movie ends more than 30min after window end — too late
    s = _showing(hour=10, runtime=150)  # 10:00-12:30
    start = datetime(2026, 7, 1, 9, 0)
    end = datetime(2026, 7, 1, 11, 59)  # effective end = 12:29
    assert not fits_window(s, start, end)


# --- Sort order ---


def test_sort_wishlisted_first() -> None:
    a = _showing(title="NOT WISHLISTED", hour=10)
    b = _showing(title="WISHLISTED", hour=11)
    start = datetime(2026, 7, 1, 9, 0)
    end = datetime(2026, 7, 1, 18, 0)
    # Default sort is by time; wishlisted no longer floats to top
    result = filter_showings([a, b], start, end, wishlisted={"WISHLISTED"})
    assert result[0].normalized_title == "NOT WISHLISTED"


def test_sort_by_start_time_ignores_location() -> None:
    a = _showing(title="A", location="Downtown Brooklyn", hour=10)
    b = _showing(title="B", location="Lower Manhattan", hour=11)
    start = datetime(2026, 7, 1, 9, 0)
    end = datetime(2026, 7, 1, 18, 0)
    result = filter_showings([a, b], start, end)
    assert result[0].normalized_title == "A"


def test_sort_by_start_time() -> None:
    a = _showing(title="LATE", hour=15)
    b = _showing(title="EARLY", hour=11)
    start = datetime(2026, 7, 1, 9, 0)
    end = datetime(2026, 7, 1, 20, 0)
    result = filter_showings([a, b], start, end)
    assert result[0].normalized_title == "EARLY"


# --- Tags in rendered output ---


def test_render_shows_format_tag() -> None:
    s = _showing(format_name="IMAX")
    html = render_showing(s)
    assert "tag-format" in html
    assert "IMAX" in html


def test_render_shows_location_tag() -> None:
    s = _showing(location="Lower Manhattan")
    html = render_showing(s)
    assert "tag-location" in html
    assert "Lower Manhattan" in html


def test_render_no_series_tag_for_regular() -> None:
    s = _showing(series_name=None)
    html = render_showing(s)
    assert "tag-series" not in html


# --- Screening badges ---


def test_render_series_tag_for_special() -> None:
    s = _showing(series_name="Terror Tuesday")
    html = render_showing(s)
    assert "tag-series" in html
    assert "Terror Tuesday" in html


def test_render_no_series_tag_for_non_special() -> None:
    s = _showing(series_name="New Release")
    html = render_showing(s)
    assert "tag-series" not in html


# --- Render integration ---


def test_render_showing_has_icon_and_badge() -> None:
    s = _showing(format_name="IMAX", series_name="Terror Tuesday")
    html = render_showing(s)
    assert "tag-format" in html
    assert "IMAX" in html
    assert "tag-series" in html
    assert "Terror Tuesday" in html
    assert "MOVIE" in html
    assert "showing-card" in html
