from collections.abc import Callable
from datetime import datetime
from typing import Any

import httpx

from schedule_the_alamo.models import Showing
from schedule_the_alamo.normalize import normalize_title

THEATER_IDS = ["2103", "2101"]
API_URL = "https://feeds.drafthouse.com/adcService/showtimes.svc/calendar/{id}/"

type FetchFn = Callable[[str], dict[str, Any]]

_ssl_injected = False


def fetch_calendar_http(theater_id: str) -> dict[str, Any]:
    global _ssl_injected
    if not _ssl_injected:
        import truststore

        truststore.inject_into_ssl()
        _ssl_injected = True
    url = API_URL.format(id=theater_id)
    resp = httpx.get(url, timeout=30)
    resp.raise_for_status()
    return resp.json()


def _parse_film(film: dict[str, Any], location: str) -> list[Showing]:
    original_title = film.get("FilmName", "")
    runtime = int(film.get("FilmRuntime") or 0)
    normalized = normalize_title(original_title)
    showings: list[Showing] = []
    for series in film.get("Series") or []:
        series_name = series.get("SeriesName") or None
        for fmt in series.get("Formats") or []:
            format_name = fmt.get("FormatName", "")
            for session in fmt.get("Sessions") or []:
                dt_str = session.get("SessionDateTime")
                if not dt_str:
                    continue
                showings.append(
                    Showing(
                        normalized_title=normalized,
                        original_title=original_title,
                        showtime=datetime.fromisoformat(dt_str),
                        runtime_minutes=runtime,
                        location=location,
                        format_name=format_name,
                        series_name=series_name,
                    )
                )
    return showings


def parse_calendar(data: dict[str, Any] | None) -> list[Showing]:
    if not data:
        return []
    showings: list[Showing] = []
    seen: set[tuple[str, str, str]] = set()
    calendar = data.get("Calendar", {})
    for cinema in calendar.get("Cinemas") or []:
        location = cinema.get("CinemaName", "")
        for month in cinema.get("Months") or []:
            for week in month.get("Weeks") or []:
                for day in week.get("Days") or []:
                    for film in day.get("Films") or []:
                        for s in _parse_film(film, location):
                            # ponytail: dedup — API returns same session
                            # in overlapping week boundaries
                            key = (
                                s.showtime.isoformat(),
                                s.location,
                                s.normalized_title,
                            )
                            if key not in seen:
                                seen.add(key)
                                showings.append(s)
    return showings


def fetch_all_showings(
    theater_ids: list[str] | None = None,
    fetch: FetchFn = fetch_calendar_http,
) -> list[Showing]:
    ids = theater_ids or THEATER_IDS
    showings: list[Showing] = []
    for tid in ids:
        data = fetch(tid)
        showings.extend(parse_calendar(data))
    return showings
