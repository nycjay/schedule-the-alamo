"""Fetch Rotten Tomatoes scores via OMDb API with disk cache."""

import json
import os
from pathlib import Path

import httpx

_CACHE_FILE = Path("omdb_cache.json")
_cache: dict[str, str | None] = {}


def _load_cache() -> None:
    global _cache
    if not _cache and _CACHE_FILE.exists():
        _cache = json.loads(_CACHE_FILE.read_text())


def _save_cache() -> None:
    _CACHE_FILE.write_text(json.dumps(_cache, indent=2))


def get_rt_score(title: str) -> str | None:
    """Return RT score like '93%' or None if not found."""
    _load_cache()
    if title in _cache:
        return _cache[title]

    api_key = os.environ.get("OMDB_API_KEY", "")
    if not api_key:
        return None

    try:
        resp = httpx.get(
            "http://www.omdbapi.com/",
            params={"t": title, "apikey": api_key},
            timeout=5,
        )
        data = resp.json()
        score = None
        for r in data.get("Ratings", []):
            if "Rotten" in r.get("Source", ""):
                score = "🍅 " + r["Value"]
                break
        if not score:
            for r in data.get("Ratings", []):
                if "Internet Movie" in r.get("Source", ""):
                    score = "⭐ " + r["Value"]
                    break
        _cache[title] = score
        if score:
            _save_cache()
        return score
    except Exception:
        return None


def get_scores_batch(titles: list[str]) -> dict[str, str | None]:
    """Fetch scores for multiple titles, using cache."""
    _load_cache()
    results: dict[str, str | None] = {}
    for title in titles:
        results[title] = get_rt_score(title)
    return results
