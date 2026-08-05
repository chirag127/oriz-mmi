"""Tickertape MMI JSON API — https://api.tickertape.in/mmi/now

VERIFIED 2026-08-05 (httpx, keyless JSON — no scraping, no JS render needed).
The page HTML is JS-hydrated, but the value is served by a public JSON endpoint
`api.tickertape.in/mmi/now`. Shape (data key):
  indicator: 73.13   # current MMI 0..100
  raw:       70.81   # pre-smoothing
  date:      "2026-08-05T04:33:00.113Z"
  nifty/vix/fii/...  # the 6 factors that drive the index
  lastDay/lastWeek/lastMonth/lastYear: {date, indicator, ...}
"""

from __future__ import annotations

from ..models import Comparison, MmiReading
from ..util import classify_zone, fetch_json
from .base import Source

_HORIZONS = [
    ("lastDay", "Yesterday"),
    ("lastWeek", "Last week"),
    ("lastMonth", "Last month"),
    ("lastYear", "Last year"),
]


def parse_reading(data: dict, name: str = "tickertape") -> MmiReading:
    """Build an MmiReading from the api.tickertape.in/mmi/now `data` object."""
    ind = data.get("indicator")
    if ind is None:
        raise ValueError(f"{name}: no 'indicator' in payload")
    value = round(float(ind), 2)
    reading = MmiReading(
        value=value,
        zone=classify_zone(value),
        source_date=str(data.get("date", "")),
        raw=round(float(data["raw"]), 2) if data.get("raw") is not None else None,
        nifty=data.get("nifty"),
        vix=data.get("vix"),
        fii=data.get("fii"),
    )
    for key, label in _HORIZONS:
        sub = data.get(key)
        if isinstance(sub, dict) and sub.get("indicator") is not None:
            v = round(float(sub["indicator"]), 2)
            reading.comparisons.append(
                Comparison(label=label, value=v, zone=classify_zone(v), date=str(sub.get("date", "")))
            )
    return reading


class Tickertape(Source):
    name = "tickertape"
    url = "https://api.tickertape.in/mmi/now"

    def fetch(self) -> MmiReading:
        payload = fetch_json(self.url)
        data = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(data, dict):
            raise ValueError("tickertape: unexpected payload (no 'data')")
        return parse_reading(data, self.name)
