from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Showing:
    normalized_title: str
    original_title: str
    showtime: datetime
    runtime_minutes: int
    location: str
    format_name: str
    series_name: str | None
