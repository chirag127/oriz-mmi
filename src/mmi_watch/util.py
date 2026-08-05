"""Shared helpers: HTTP JSON fetch, logging, zone classification."""

from __future__ import annotations

import logging
import sys

import httpx

log = logging.getLogger("mmi_watch")

_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)

# Tickertape MMI 4-zone model (the dial the site draws).
# <30 Extreme Fear · 30-50 Fear · 50-70 Greed · >70 Extreme Greed.
ZONES = (
    (30.0, "Extreme Fear"),
    (50.0, "Fear"),
    (70.0, "Greed"),
    (float("inf"), "Extreme Greed"),
)


def configure_logging(verbose: bool = False) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stderr,
    )


def classify_zone(value: float) -> str:
    """MMI value -> zone label."""
    for hi, label in ZONES:
        if value < hi:
            return label
    return "Extreme Greed"


def zone_emoji(zone: str) -> str:
    return {
        "Extreme Fear": "🟥",
        "Fear": "🟧",
        "Greed": "🟩",
        "Extreme Greed": "🟢",
    }.get(zone, "⚪")


def fetch_json(url: str, timeout: float = 25.0) -> dict:
    """GET a JSON endpoint. Raises httpx.HTTPError on failure."""
    headers = {
        "User-Agent": _UA,
        "Accept": "application/json,text/plain,*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.tickertape.in/market-mood-index",
    }
    with httpx.Client(headers=headers, timeout=timeout, follow_redirects=True) as client:
        r = client.get(url)
        r.raise_for_status()
        return r.json()
