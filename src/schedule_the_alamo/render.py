"""Render filtered showings as card-based HTMX HTML fragments."""

from html import escape
from urllib.parse import quote_plus

from schedule_the_alamo.models import Showing

_SPECIAL_SERIES: set[str] = {
    "Terror Tuesday",
    "Weird Wednesday",
    "Video Vortex",
    "Graveyard Shift",
    "Action Pack",
    "Breakfast Club",
}


def _tag(label: str, category: str) -> str:
    return (
        f'<span class="tag tag-{category}" '
        f"onclick=\"toggleFilter('{category}', '{escape(label, quote=True)}')\">"
        f"{label}</span>"
    )


def render_showing(
    showing: Showing,
    wishlisted: bool = False,
    rt_score: str | None = None,
) -> str:
    time_str = showing.showtime.strftime("%I:%M %p").lstrip("0")
    dt = showing.showtime.isoformat()
    safe_id = dt.replace(":", "-")
    title = showing.normalized_title
    t_esc = escape(title, quote=True)
    star = "★" if wishlisted else "☆"
    score_html = (
        f'<span class="rt-score">{rt_score}</span>' if rt_score else ""
    )


    trailer_url = (
        "https://www.youtube.com/results?search_query="
        + quote_plus(title + " trailer")
    )

    tags = (
        _tag(showing.location, "location")
        + _tag(showing.format_name, "format")
    )
    if showing.series_name and showing.series_name in _SPECIAL_SERIES:
        tags += _tag(showing.series_name, "series")

    loc_esc = escape(showing.location, quote=True)
    fmt_esc = escape(showing.format_name, quote=True)
    series_esc = escape(showing.series_name or "", quote=True)

    return (
        f'<div class="showing-card" id="showing-{safe_id}" '
        f'data-location="{loc_esc}" '
        f'data-format="{fmt_esc}" '
        f'data-series="{series_esc}">'
        f'<div class="info">'
        f'<div class="title">{title} '
        f'<a href="{trailer_url}" target="_blank" class="trailer-link" '
        f'title="Search trailer">🎬</a> {score_html}</div>'
        f'<div class="time">{time_str}</div>'
        f'<div class="tags">{tags}</div>'
        f"</div>"
        f'<div class="actions">'
        f'<form style="display:inline" hx-post="/wishlist" '
        f'hx-target="this" hx-swap="outerHTML">'
        f'<input type="hidden" name="title" value="{t_esc}">'
        f'<button type="submit" title="Wishlist">{star}</button></form>'
        f'<form style="display:inline" hx-post="/dismiss" '
        f'hx-target="#showing-{safe_id}" hx-swap="outerHTML">'
        f'<input type="hidden" name="title" value="{t_esc}">'
        f'<button type="submit" title="Dismiss">✗</button></form>'
        f"</div></div>"
    )


def render_window_results(
    showings: list[Showing],
    label: str,
    wishlisted: set[str] | None = None,
    scores: dict[str, str | None] | None = None,
) -> str:
    wishlisted = wishlisted or set()
    scores = scores or {}
    if not showings:
        return (
            f'<div class="window-results"><h4>{label}</h4>'
            f'<p class="no-results">No movies fit this window.</p></div>'
        )
    items = "\n".join(
        render_showing(
            s,
            s.normalized_title in wishlisted,
            scores.get(s.normalized_title),
        )
        for s in showings
    )
    return f'<div class="window-results"><h4>{label}</h4>{items}</div>'
