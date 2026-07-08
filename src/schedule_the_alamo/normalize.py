import re

_SUFFIX = re.compile(
    r"[\s\-–—:]*\b("
    r"IMAX|3D|2D|OC|Open Captions?|CC|Closed Captions?|"
    r"Subtitled|D-BOX|Dolby Atmos|Dolby Cinema|"
    r"Sensory Friendly|Baby Day|Party|Fan Event"
    r")\s*$",
    re.IGNORECASE,
)

_PREFIX = re.compile(
    r"^("
    # Format prefixes
    r"Open Captions?|OC|CC|Closed Captions?|"
    r"IMAX|3D|2D|70mm|35mm|D-BOX|Dolby Atmos|Dolby Cinema|"
    r"HDR by Barco|"
    # Event/series prefixes
    r"Guest Selects|Queer Film Theory \d+|Live Q&A|Livestream Q&A|"
    r"Crunchyroll Anime Nights|Free Victory Screening|"
    r"Kids Camp|Movie Party|Family Party|Sad Girl Cinema Club|"
    r"Sing-Along|Terror Tuesday|Video Vortex|"
    r"Weird Wednesday|Graveyard Shift|Action Pack|Breakfast Club"
    r")[\s:–—\-]+",
    re.IGNORECASE,
)

_YEAR = re.compile(r"\s*\(\d{4}\)\s*$")


def normalize_title(title: str) -> str:
    result = _YEAR.sub("", title).strip()
    # Strip known prefixes like "Open Caption: MOVIE" or "70mm: MOVIE"
    result = _PREFIX.sub("", result).strip()
    # Strip known suffixes from end
    while True:
        m = _SUFFIX.search(result)
        if m:
            result = result[: m.start()].strip()
        else:
            break
    return result
