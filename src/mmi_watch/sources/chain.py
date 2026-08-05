"""Source failover chain. Try each in order; first that yields a reading wins.

Order (VERIFIED 2026-08-05 — see verify-website-structure-before-scrapers rule):
  1. Tickertape JSON  httpx  ✓ keyless api.tickertape.in/mmi/now (server JSON)
  2. Playwright dial   JS    — reads __NEXT_DATA__ off the rendered page; only if
                              the JSON API is blocked AND playwright installed.
"""

from __future__ import annotations

import logging

from ..models import MmiReading
from .base import Source
from .playwright_source import PlaywrightDial
from .tickertape import Tickertape

log = logging.getLogger("mmi_watch")


def build_chain() -> list[Source]:
    return [Tickertape(), PlaywrightDial()]


def read_first_available() -> tuple[str, MmiReading]:
    """Return (source_name, reading) from the first working source. Raise if all fail."""
    errors: list[str] = []
    for src in build_chain():
        try:
            log.info("trying source: %s (%s)", src.name, src.url)
            reading = src.fetch()
            log.info("source %s OK: MMI %.2f (%s)", src.name, reading.value, reading.zone)
            return src.name, reading
        except Exception as e:  # noqa: BLE001 - failover is the point
            log.warning("source %s failed: %s", src.name, e)
            errors.append(f"{src.name}: {e}")
    raise RuntimeError("all MMI sources failed:\n  " + "\n  ".join(errors))
