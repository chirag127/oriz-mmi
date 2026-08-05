"""Playwright fallback — reads the MMI value straight off the rendered dial page
if the JSON API is ever blocked/changed. Last resort; only used if the httpx
JSON source fails AND playwright is installed.

Scrapes the JSON out of Next.js `__NEXT_DATA__` (the page embeds the same
nowData payload), so no fragile DOM-selector guessing.
"""

from __future__ import annotations

import json

from ..models import MmiReading
from .base import Source
from .tickertape import parse_reading

PAGE = "https://www.tickertape.in/market-mood-index"


def _extract_now_data(next_data: dict) -> dict | None:
    """Walk the __NEXT_DATA__ blob for the object holding an 'indicator'."""
    stack = [next_data]
    while stack:
        node = stack.pop()
        if isinstance(node, dict):
            if "indicator" in node and "date" in node and "lastDay" in node:
                return node
            stack.extend(node.values())
        elif isinstance(node, list):
            stack.extend(node)
    return None


class PlaywrightDial(Source):
    name = "tickertape-playwright"
    url = PAGE

    def fetch(self) -> MmiReading:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as e:  # playwright not installed
            raise RuntimeError("playwright not available") from e

        last_err: Exception | None = None
        for attempt in range(3):  # launch is flaky on this host
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(
                        headless=True,
                        args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"],
                    )
                    try:
                        page = browser.new_page(
                            user_agent="Mozilla/5.0 (X11; Linux x86_64) Chrome/126.0"
                        )
                        page.goto(self.url, wait_until="domcontentloaded", timeout=45000)
                        raw = page.eval_on_selector(
                            "#__NEXT_DATA__", "el => el.textContent"
                        )
                        data = _extract_now_data(json.loads(raw))
                        if not data:
                            raise ValueError("no MMI nowData in __NEXT_DATA__")
                        return parse_reading(data, self.name)
                    finally:
                        browser.close()
            except Exception as e:  # noqa: BLE001 - retry launch
                last_err = e
        raise RuntimeError(f"playwright dial failed after 3 attempts: {last_err}")
