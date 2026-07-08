"""Filter showings by time windows and sort results."""

from datetime import datetime, timedelta

from schedule_the_alamo.models import Showing

BUFFER = timedelta(minutes=30)


def fits_window(
    showing: Showing, window_start: datetime, window_end: datetime
) -> bool:
    """Check if showing fits within window with 30-min buffer.

    Buffer extends outward: movie can start 30min before your free time
    (you arrive during previews) and end 30min after (you don't mind
    staying a bit late).
    """
    effective_start = window_start - BUFFER
    effective_end = window_end + BUFFER
    show_end = showing.showtime + timedelta(minutes=showing.runtime_minutes)
    return showing.showtime >= effective_start and show_end <= effective_end


def filter_showings(
    showings: list[Showing],
    window_start: datetime,
    window_end: datetime,
    wishlisted: set[str] | None = None,
    dismissed: set[str] | None = None,
    sort: str = "time",
) -> list[Showing]:
    """Filter and sort showings for a given time window."""
    dismissed = dismissed or set()
    matched = [
        s
        for s in showings
        if fits_window(s, window_start, window_end)
        and s.normalized_title not in dismissed
    ]
    if sort == "title":
        matched.sort(
            key=lambda s: (
                s.normalized_title,
                s.showtime,
            )
        )
    else:
        matched.sort(key=lambda s: s.showtime)
    return matched
