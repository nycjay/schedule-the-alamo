"""HTML fragment builders for the planner UI."""

_TIME_OPTIONS = [f"{h:02d}:{m:02d}" for h in range(24) for m in (0, 30)]


def time_options_html(selected: str = "") -> str:
    opts = []
    for t in _TIME_OPTIONS:
        sel = " selected" if t == selected else ""
        opts.append(f'<option value="{t}"{sel}>{t}</option>')
    return "\n".join(opts)


def time_window_html(
    date: str, idx: int, start: str = "09:00", end: str = "17:00"
) -> str:
    return (
        f'<div class="time-window" id="window-{date}-{idx}">'
        f"<select name=\"start-{date}[]\">"
        f"{time_options_html(start)}</select>"
        f'<span class="to-label">to</span>'
        f"<select name=\"end-{date}[]\">"
        f"{time_options_html(end)}</select>"
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
