"""User state: dismissals, wishlist, free windows. Persisted to JSON."""

import json
from dataclasses import dataclass, field
from pathlib import Path

STATE_FILE = Path("alamo_state.json")


def _state_path() -> Path:
    return STATE_FILE


@dataclass
class TimeWindow:
    start: str  # "HH:MM"
    end: str  # "HH:MM"


@dataclass
class UserState:
    dismissed: set[str] = field(default_factory=set)
    wishlisted: set[str] = field(default_factory=set)
    theaters: list[str] = field(default_factory=list)  # selected cinema IDs
    # date -> list of time windows
    windows: dict[str, list[TimeWindow]] = field(default_factory=dict)

    def dismiss(self, title: str) -> None:
        self.dismissed.add(title)

    def undismiss(self, title: str) -> None:
        self.dismissed.discard(title)

    def wishlist(self, title: str) -> None:
        self.wishlisted.add(title)

    def unwishlist(self, title: str) -> None:
        self.wishlisted.discard(title)


def save_state(state: UserState, path: Path | None = None) -> None:
    path = path or _state_path()
    data = {
        "dismissed": sorted(state.dismissed),
        "wishlisted": sorted(state.wishlisted),
        "theaters": state.theaters,
        "windows": {
            date: [{"start": w.start, "end": w.end} for w in wins]
            for date, wins in state.windows.items()
        },
    }
    path.write_text(json.dumps(data, indent=2))


def load_state(path: Path | None = None) -> UserState:
    path = path or _state_path()
    if not path.exists():
        return UserState()
    data = json.loads(path.read_text())
    windows = {
        date: [TimeWindow(w["start"], w["end"]) for w in wins]
        for date, wins in data.get("windows", {}).items()
    }
    return UserState(
        dismissed=set(data.get("dismissed", [])),
        wishlisted=set(data.get("wishlisted", [])),
        theaters=data.get("theaters", []),
        windows=windows,
    )
