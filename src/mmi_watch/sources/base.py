"""Source base + registry. Each source returns an MmiReading or raises."""

from __future__ import annotations

from ..models import MmiReading


class Source:
    name: str = "base"
    url: str = ""

    def fetch(self) -> MmiReading:  # pragma: no cover - interface
        raise NotImplementedError
