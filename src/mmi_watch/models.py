"""Data models for MMI readings."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(slots=True)
class Comparison:
    """A point-in-time MMI value for a comparison horizon (day/week/month/year)."""

    label: str          # "Yesterday" | "Last week" | ...
    value: float | None = None
    zone: str = ""
    date: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class MmiReading:
    value: float                       # current MMI 0..100 (the "indicator")
    zone: str                          # Extreme Fear | Fear | Greed | Extreme Greed
    ts: str = field(default_factory=_now_iso)   # our capture time (UTC iso)
    source_date: str = ""              # timestamp the source reported
    raw: float | None = None           # pre-smoothing raw indicator
    nifty: float | None = None
    vix: float | None = None
    fii: float | None = None
    comparisons: list[Comparison] = field(default_factory=list)
    summary: str = ""                  # g4f / template one-line commentary

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["comparisons"] = [c.to_dict() for c in self.comparisons]
        return d
