default_port := "8000"

lint:
    uv run ruff check src tests

format:
    uv run ruff format src tests

typecheck:
    uv run ty check src

test:
    uv run python -m pytest

smoke:
    uv run python -c "from schedule_the_alamo.fetch import fetch_all_showings; s = fetch_all_showings(); print(f'{len(s)} showings parsed'); assert len(s) > 0"

serve *ARGS:
    uv run python -m schedule_the_alamo {{ARGS}}

check: lint typecheck test
