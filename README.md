# Schedule the Alamo

A local web app that helps you plan movie nights at Alamo Drafthouse. Pick your free time, see what fits, and manage your watchlist.

## What it does

- **Theater selection** — Choose any Alamo Drafthouse location(s) from the full list
- **Calendar planner** — Select dates and free-time windows (30-min increments)
- **Smart filtering** — Shows only movies whose runtime (plus 30-min buffer each side) fits your window
- **All Movies view** — Browse every title at your selected theaters, dismiss or wishlist
- **Persistence** — Dismissals, wishlists, theater choices, and time windows saved between sessions
- **Tag filtering** — Click location/format/series tags to filter results instantly
- **Trailer links** — One click to search YouTube for any movie's trailer
- **Rotten Tomatoes scores** — Shown inline when available (requires free OMDb API key)

## Quick start

Requires [uv](https://docs.astral.sh/uv/) (Python package manager) and [just](https://github.com/casey/just) (command runner).

```bash
cp .env.example .env   # add your OMDb API key (optional)
just serve
```

Open http://127.0.0.1:8000.

1. Go to **Theaters** and select your location(s)
2. Pick dates on the calendar, set your free-time windows
3. Click **Find Movies**

Custom port:

```bash
just serve --port 9999
```

## Development

```bash
just check    # lint + typecheck + test
just test     # pytest only
just lint     # ruff
just typecheck # ty
just smoke    # hit live Alamo API
just format   # auto-format
```

## Stack

- **Backend**: Python 3.13, FastAPI, uvicorn
- **Frontend**: HTMX, flatpickr, vanilla CSS/JS
- **State**: Single JSON file (`alamo_state.json`)
- **Tooling**: uv, ruff, ty, pytest
- **API**: Alamo Drafthouse public feed (no auth required)

## How it works

The app fetches showtimes from the Alamo Drafthouse public API for your selected theaters. Titles are normalized (stripping format prefixes like "IMAX:" and series prefixes like "Terror Tuesday:") so variants are grouped together.

The 30-minute buffer on each side of your free window accounts for travel and settling in — a movie starting at 2:30 won't match a window ending at 3:00.

## Data

All state lives in `alamo_state.json` (git-ignored). Showtimes are fetched fresh from the API on every search. Delete the state file to start over.

## License

MIT
