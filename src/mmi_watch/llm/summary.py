"""g4f (GPT4Free) commentary — keyless, best-effort. Deterministic fallback so a
missing/failed LLM never blocks the pipeline or the notification.

g4f's public API drifts; we import lazily and catch everything. If g4f is absent
or every provider fails, `commentary` returns a clean template one-liner built
from the reading — the pipeline never depends on the LLM succeeding.
"""

from __future__ import annotations

import logging
import os

from ..models import MmiReading

log = logging.getLogger("mmi_watch")

_ADVICE = {
    "Extreme Fear": "historically a buy-the-fear zone — markets may be oversold.",
    "Fear": "caution in the air; contrarians watch for accumulation.",
    "Greed": "momentum-positive but late-cycle; stay selective.",
    "Extreme Greed": "froth risk — a correction may be due, trim/hedge.",
}


def _trend(reading: MmiReading) -> str:
    yday = next((c for c in reading.comparisons if c.label == "Yesterday"), None)
    if yday and yday.value is not None:
        d = reading.value - yday.value
        if abs(d) < 0.5:
            return "flat vs yesterday"
        return f"{'up' if d > 0 else 'down'} {abs(d):.1f} vs yesterday"
    return ""


def _template(reading: MmiReading) -> str:
    parts = [f"MMI {reading.value:.1f} — {reading.zone}"]
    t = _trend(reading)
    if t:
        parts.append(t)
    parts.append(_ADVICE.get(reading.zone, ""))
    return ". ".join(p for p in parts if p)


def _g4f_complete(prompt: str) -> str | None:
    """One best-effort g4f call. None on any failure."""
    if os.environ.get("MMI_DISABLE_LLM") == "1":
        return None
    try:
        from g4f.client import Client  # lazy — g4f may be absent
    except Exception as e:  # noqa: BLE001
        log.info("g4f unavailable: %s", e)
        return None
    try:
        client = Client()
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            timeout=45,
        )
        text = (resp.choices[0].message.content or "").strip()
        return text or None
    except Exception as e:  # noqa: BLE001 - any provider failure -> fallback
        log.info("g4f completion failed: %s", e)
        return None


def commentary(reading: MmiReading) -> str:
    """One-line market-mood take. LLM if available, else deterministic template."""
    cmp_lines = "; ".join(
        f"{c.label} {c.value:.0f}" for c in reading.comparisons if c.value is not None
    ) or "no history"
    prompt = (
        "You are an equity-desk analyst. In ONE concise sentence (max 25 words), "
        "give a neutral read on the Indian market's Tickertape Market Mood Index. "
        "No hype, no disclaimer, no financial advice.\n\n"
        f"MMI now: {reading.value:.1f} ({reading.zone})\n"
        f"Nifty: {reading.nifty}  India VIX chg: {reading.vix}\n"
        f"History: {cmp_lines}"
    )
    return _g4f_complete(prompt) or _template(reading)
