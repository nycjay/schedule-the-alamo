"""HTML fragment builders for the planner UI."""

_TIME_OPTIONS = [f"{h:02d}:{m:02d}" for h in range(24) for m in (0, 30)]


def display_time(t: str, fmt: str) -> str:
    """Format 'HH:MM' for display. Value always stays 24h."""
    if fmt == "24h":
        return t
    h, m = int(t[:2]), t[3:]
    suffix = "AM" if h < 12 else "PM"
    h12 = h % 12 or 12
    return f"{h12}:{m} {suffix}"


def time_options_html(selected: str = "", time_format: str = "12h") -> str:
    opts = []
    for t in _TIME_OPTIONS:
        sel = " selected" if t == selected else ""
        label = display_time(t, time_format)
        opts.append(f'<option value="{t}"{sel}>{label}</option>')
    return "\n".join(opts)


def time_window_html(
    date: str, idx: int, start: str = "09:00", end: str = "17:00",
    time_format: str = "12h",
) -> str:
    return (
        f'<div class="time-window" id="window-{date}-{idx}">'
        f"<select name=\"start-{date}[]\">"
        f"{time_options_html(start, time_format)}</select>"
        f'<span class="to-label">to</span>'
        f"<select name=\"end-{date}[]\">"
        f"{time_options_html(end, time_format)}</select>"
        f'<button type="button" class="remove-btn" '
        f"hx-delete=\"/dates/{date}/window/{idx}\" "
        f"hx-target=\"#window-{date}-{idx}\" "
        f'hx-swap="outerHTML">×</button>'
        f"</div>"
    )


def date_row_html(date: str, window_htmls: list[str]) -> str:
    windows = "".join(window_htmls)
    return (
        f'<div class="date-row" id="date-{date}">'
        f'<button type="button" class="remove-btn remove-date-btn" '
        f"onclick=\"removeDate('{date}', this.parentElement)\">×</button>"
        f"<h3>{date}</h3>"
        f'<div id="windows-{date}">{windows}</div>'
        f'<button type="button" class="add-window-btn" '
        f"hx-post=\"/dates/{date}/window\" "
        f"hx-target=\"#windows-{date}\" "
        f'hx-swap="beforeend">+ Add window</button>'
        f"</div>"
    )
