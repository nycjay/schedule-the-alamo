import json
from datetime import datetime
from html import escape
from pathlib import Path
from urllib.parse import quote_plus

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from schedule_the_alamo.fetch import (
    FetchFn,
    fetch_all_showings,
    fetch_calendar_http,
)
from schedule_the_alamo.filter import filter_showings
from schedule_the_alamo.models import Showing
from schedule_the_alamo.ratings import get_scores_batch
from schedule_the_alamo.render import render_window_results
from schedule_the_alamo.state import TimeWindow, load_state, save_state
from schedule_the_alamo.views import date_row_html, time_window_html

app = FastAPI()
_STATIC = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=_STATIC), name="static")

_TEMPLATES = Path(__file__).parent / "templates"


def get_fetch_fn() -> FetchFn:
    return fetch_calendar_http


@app.get("/", response_class=HTMLResponse)
def index() -> str:

    state = load_state()
    # Pre-render saved date rows
    date_rows = ""
    for date in sorted(state.windows):
        wins = state.windows[date]
        window_htmls = [
            time_window_html(date, i, w.start, w.end)
            for i, w in enumerate(wins)
        ]
        date_rows += date_row_html(date, window_htmls)
    # Pass saved dates to JS for flatpickr initialization
    saved_dates_json = json.dumps(sorted(state.windows.keys()))
    template = (_TEMPLATES / "index.html").read_text()
    template = template.replace("/*SAVED_DATES*/", saved_dates_json)
    template = template.replace("<!--DATE_ROWS-->", date_rows)
    return template


@app.post("/dates/add", response_class=HTMLResponse)
def add_date(date: str = Form()) -> str:
    state = load_state()
    if date not in state.windows:
        state.windows[date] = [TimeWindow("09:00", "17:00")]
        save_state(state)
    wins = state.windows[date]
    window_htmls = [
        time_window_html(date, i, w.start, w.end)
        for i, w in enumerate(wins)
    ]
    return date_row_html(date, window_htmls)


@app.post("/dates/{date}/window", response_class=HTMLResponse)
def add_window(date: str) -> str:

    state = load_state()
    state.windows.setdefault(date, []).append(TimeWindow("09:00", "17:00"))
    save_state(state)
    idx = len(state.windows[date]) - 1
    return time_window_html(date, idx)


@app.delete("/dates/{date}/window/{idx}", response_class=HTMLResponse)
def remove_window(date: str, idx: int) -> str:
    state = load_state()
    wins = state.windows.get(date, [])
    if idx < len(wins):
        wins.pop(idx)
    if not wins:
        state.windows.pop(date, None)
    save_state(state)
    return ""


@app.delete("/dates/{date}", response_class=HTMLResponse)
def remove_date(date: str) -> str:
    state = load_state()
    state.windows.pop(date, None)
    save_state(state)
    return ""


@app.post("/results", response_class=HTMLResponse)
async def results(
    request: Request, fetch_fn: FetchFn = Depends(get_fetch_fn)
) -> str:


    form = await request.form()
    sort = str(form.get("sort", "time"))
    state = load_state()
    showings: list[Showing] = fetch_all_showings(
        theater_ids=state.theaters or None, fetch=fetch_fn
    )
    unique_titles = list({s.normalized_title for s in showings})
    scores = get_scores_batch(unique_titles)
    html_parts: list[str] = []

    dates: set[str] = set()
    for key in form.keys():
        if key.startswith("start-"):
            dates.add(key.removeprefix("start-").removesuffix("[]"))

    # Persist current window selections
    state.windows = {}
    for date in sorted(dates):
        starts = [str(v) for v in form.getlist(f"start-{date}[]")]
        ends = [str(v) for v in form.getlist(f"end-{date}[]")]
        state.windows[date] = [
            TimeWindow(s, e) for s, e in zip(starts, ends)
        ]
        for s, e in zip(starts, ends):
            window_start = datetime.fromisoformat(f"{date}T{s}")
            window_end = datetime.fromisoformat(f"{date}T{e}")
            matched = filter_showings(
                showings,
                window_start,
                window_end,
                dismissed=state.dismissed,
                sort=sort,
            )
            label = f"{date} · {s}–{e}"
            html_parts.append(
                render_window_results(
                    matched, label, state.wishlisted, scores
                )
            )

    save_state(state)
    if not html_parts:
        return "<p>No windows selected.</p>"
    time_sel = " selected" if sort == "time" else ""
    title_sel = " selected" if sort == "title" else ""
    sort_control = (
        '<div class="time-window sort-control">'
        '<span class="to-label">Sort by</span>'
        '<select id="sort-select" name="sort" form="planner-form" '
        'onchange="document.getElementById(\'planner-form\').requestSubmit()">'
        f'<option value="time"{time_sel}>Start time</option>'
        f'<option value="title"{title_sel}>Title</option>'
        "</select></div>"
    )
    return sort_control + "\n".join(html_parts)


@app.post("/dismiss", response_class=HTMLResponse)
def dismiss(title: str = Form()) -> str:

    state = load_state()
    state.dismiss(title)
    save_state(state)
    t_esc = escape(title, quote=True)
    return (
        f'<div class="showing dismissed">'
        f"Dismissed <em>{title}</em> "
        f'<form style="display:inline" hx-post="/undo/dismiss" '
        f'hx-target="closest .showing" hx-swap="outerHTML">'
        f'<input type="hidden" name="title" value="{t_esc}">'
        f'<button type="submit" class="undo-btn">Undo</button></form>'
        f"</div>"
    )


@app.post("/wishlist", response_class=HTMLResponse)
def wishlist_toggle(title: str = Form()) -> str:

    state = load_state()
    if title in state.wishlisted:
        state.unwishlist(title)
        star = "☆"
    else:
        state.wishlist(title)
        star = "★"
    save_state(state)
    t_esc = escape(title, quote=True)
    return (
        f'<form style="display:inline" hx-post="/wishlist" '
        f'hx-target="this" hx-swap="outerHTML">'
        f'<input type="hidden" name="title" value="{t_esc}">'
        f'<button type="submit" title="Wishlist">{star}</button></form>'
    )


@app.post("/undo/dismiss", response_class=HTMLResponse)
def undo_dismiss(title: str = Form()) -> str:
    state = load_state()
    state.undismiss(title)
    save_state(state)
    return '<div class="showing">↩ Restored — will reappear on next search</div>'


@app.get("/movies/list", response_class=HTMLResponse)
def movies_list(fetch_fn: FetchFn = Depends(get_fetch_fn)) -> str:
    """Return just the movie list fragment (main + dismissed)."""

    state = load_state()
    showings = fetch_all_showings(
        theater_ids=state.theaters or None, fetch=fetch_fn
    )
    scores = get_scores_batch(
        list({s.normalized_title for s in showings})
    )

    # Group: title -> {formats, locations, count}
    titles: dict[str, dict] = {}
    for s in showings:
        t = s.normalized_title
        if t not in titles:
            titles[t] = {"formats": set(), "locations": set(), "count": 0}
        titles[t]["formats"].add(s.format_name)
        titles[t]["locations"].add(s.location)
        titles[t]["count"] += 1

    rows: list[str] = []
    for title in sorted(titles):
        if title in state.dismissed:
            continue
        info = titles[title]
        format_tags = " ".join(
            f'<span class="tag tag-format" '
            f"onclick=\"toggleFilter('format', '{escape(f, quote=True)}')\">"
            f"{f}</span>"
            for f in sorted(info["formats"])
        )
        location_tags = " ".join(
            f'<span class="tag tag-location" '
            f"onclick=\"toggleFilter('location', '{escape(loc, quote=True)}')\">"
            f"{loc}</span>"
            for loc in sorted(info["locations"])
        )
        t_esc = escape(title, quote=True)
        trailer_url = (
            "https://www.youtube.com/results?search_query="
            + quote_plus(title + " trailer")
        )
        star = "★" if title in state.wishlisted else "☆"
        count = info["count"]
        sc = scores.get(title)
        score_html = f' <span class="rt-score">{sc}</span>' if sc else ""
        locs = " ".join(sorted(info["locations"]))
        fmts = " ".join(sorted(info["formats"]))
        rows.append(
            f'<div class="showing-card" '
            f'data-location="{escape(locs, quote=True)}" '
            f'data-format="{escape(fmts, quote=True)}">'
            f'<div class="info">'
            f'<div class="title">{title} '
            f'<a href="{trailer_url}" target="_blank" '
            f'class="trailer-link" title="Search trailer">🎬</a>'
            f"{score_html}"
            f"</div>"
            f'<div class="time">{count} showing{"s" if count != 1 else ""}</div>'
            f'<div class="tags">{location_tags} {format_tags}</div>'
            f"</div>"
            f'<div class="actions">'
            f'<form style="display:inline" hx-post="/wishlist" '
            f'hx-target="this" hx-swap="outerHTML">'
            f'<input type="hidden" name="title" value="{t_esc}">'
            f'<button type="submit" title="Wishlist">{star}</button></form>'
            f'<form style="display:inline" hx-post="/movies/dismiss" '
            f'hx-target="#movie-list" hx-swap="innerHTML">'
            f'<input type="hidden" name="title" value="{t_esc}">'
            f'<button type="submit" title="Dismiss">✗</button></form>'
            f"</div></div>"
        )

    body = "\n".join(rows) if rows else '<p class="no-results">No movies found.</p>'

    dismissed_rows: list[str] = []
    for title in sorted(state.dismissed):
        t_esc = escape(title, quote=True)
        dismissed_rows.append(
            f'<div class="movie-row dismissed-row">'
            f"<s>{title}</s> "
            f'<form style="display:inline" '
            f'hx-post="/movies/undismiss" '
            f'hx-target="#movie-list" hx-swap="innerHTML">'
            f'<input type="hidden" name="title" value="{t_esc}">'
            f'<button type="submit">Undo</button></form>'
            f"</div>"
        )
    dismissed_html = (
        "<h2>Dismissed</h2>\n" + "\n".join(dismissed_rows)
        if dismissed_rows
        else ""
    )
    return f"{body}{dismissed_html}"


@app.post("/movies/dismiss", response_class=HTMLResponse)
def movies_dismiss(
    title: str = Form(), fetch_fn: FetchFn = Depends(get_fetch_fn)
) -> str:
    state = load_state()
    state.dismiss(title)
    save_state(state)
    return movies_list(fetch_fn)


@app.post("/movies/undismiss", response_class=HTMLResponse)
def movies_undismiss(
    title: str = Form(), fetch_fn: FetchFn = Depends(get_fetch_fn)
) -> str:
    state = load_state()
    state.undismiss(title)
    save_state(state)
    return movies_list(fetch_fn)


@app.get("/movies", response_class=HTMLResponse)
def all_movies(fetch_fn: FetchFn = Depends(get_fetch_fn)) -> str:
    content = movies_list(fetch_fn)
    return (
        "<!DOCTYPE html><html><head>"
        '<meta charset="UTF-8">'
        '<link rel="icon" href="/static/favicon.svg" type="image/svg+xml">'
        '<link rel="stylesheet" href="/static/style.css">'
        '<script src="https://unpkg.com/htmx.org@2.0.4"></script>'
        "<title>All Movies - Schedule the Alamo</title>"
        "</head><body>"
        '<div class="header"><h1>Schedule the Alamo</h1>'
        '<nav><a href="/">Planner</a> '
        '<a href="/movies" class="active">All Movies</a> '
        '<a href="/theaters">Theaters</a></nav></div>'
        f'<div class="container">'
        f'<input type="search" id="movie-search" class="search-input" '
        f'placeholder="Search movies…" oninput="filterMovies(this.value)">'
        f'<div id="filter-bar" class="filter-bar"></div>'
        f'<div id="movie-list">{content}</div></div>'
        '<script src="/static/filter.js"></script>'
        "<script>"
        "function filterMovies(q){"
        "const cards=document.querySelectorAll('#movie-list .showing-card');"
        "const lq=q.toLowerCase();"
        "cards.forEach(c=>{"
        "const t=c.querySelector('.title').textContent.toLowerCase();"
        "c.hidden=lq&&!t.includes(lq);"
        "});}</script>"
        "</body></html>"
    )


_THEATERS_FILE = Path(__file__).parent / "theaters.json"


def _load_theaters() -> list[dict]:
    return json.loads(_THEATERS_FILE.read_text())


@app.get("/theaters", response_class=HTMLResponse)
def theaters_page() -> str:
    all_theaters = _load_theaters()
    state = load_state()
    selected = set(state.theaters)

    # Group by market
    markets: dict[str, list[dict]] = {}
    for t in all_theaters:
        markets.setdefault(t["marketSlug"], []).append(t)

    rows: list[str] = []
    for market in sorted(markets):
        theaters = sorted(markets[market], key=lambda t: t["name"])
        items = ""
        for t in theaters:
            checked = " checked" if t["id"] in selected else ""
            items += (
                f'<label class="theater-option">'
                f'<input type="checkbox" name="theater" '
                f'value="{t["id"]}"{checked}>'
                f' {t["name"]}'
                f"</label>"
            )
        rows.append(
            f'<div class="market-group">'
            f'<h3>{market.replace("-", " ").title()}</h3>'
            f"{items}</div>"
        )

    body = "\n".join(rows)
    count = len(selected)
    subtitle = (
        f"{count} theater{'s' if count != 1 else ''} selected"
        if count
        else "No theaters selected"
    )

    return (
        "<!DOCTYPE html><html><head>"
        '<meta charset="UTF-8">'
        '<link rel="icon" href="/static/favicon.svg" type="image/svg+xml">'
        '<link rel="stylesheet" href="/static/style.css">'
        '<script src="https://unpkg.com/htmx.org@2.0.4"></script>'
        "<title>Theaters - Schedule the Alamo</title>"
        "</head><body>"
        '<div class="header"><h1>Schedule the Alamo</h1>'
        '<nav><a href="/">Planner</a> '
        '<a href="/movies">All Movies</a> '
        '<a href="/theaters" class="active">Theaters</a></nav></div>'
        f'<div class="container">'
        f'<form method="post" action="/theaters">'
        f'<p class="subtitle">{subtitle}</p>'
        f"{body}"
        f'<button type="submit" class="btn btn-primary">Save</button>'
        f"</form></div>"
        "</body></html>"
    )


@app.post("/theaters", response_class=HTMLResponse)
async def theaters_save(request: Request) -> str:
    form = await request.form()
    selected = [str(v) for v in form.getlist("theater")]
    state = load_state()
    state.theaters = selected
    save_state(state)
    # Redirect back via a meta refresh (PRG pattern without 303 complexity)
    return (
        "<!DOCTYPE html><html><head>"
        '<meta http-equiv="refresh" content="0;url=/theaters">'
        "</head><body>Saved.</body></html>"
    )
