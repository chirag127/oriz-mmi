"""Notifiers: Telegram (bot token from env) + ntfy. Both best-effort, both read
config from env, both no-op cleanly when unconfigured.

Telegram uses HTML parse_mode: a bold headline with the MMI value + zone linking
to mmi.oriz.in, followed by the trend vs yesterday/week/month/year, the driving
factors (Nifty / VIX / FII), and the one-line commentary.
"""

from __future__ import annotations

import logging
import os

import httpx

from ..models import MmiReading
from ..util import zone_emoji

log = logging.getLogger("mmi_watch")

SITE = "https://mmi.oriz.in"
TICKERTAPE = "https://www.tickertape.in/market-mood-index"


def _esc(s: object) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _cmp_line(reading: MmiReading) -> str | None:
    bits = [f"{c.label} {c.value:.0f}" for c in reading.comparisons if c.value is not None]
    return " · ".join(bits) if bits else None


def _factors_line(reading: MmiReading) -> str | None:
    bits = []
    if reading.nifty is not None:
        bits.append(f"Nifty {reading.nifty:g}")
    if reading.vix is not None:
        bits.append(f"VIX chg {reading.vix:g}")
    if reading.fii is not None:
        bits.append(f"FII {reading.fii:g}")
    return " · ".join(bits) if bits else None


def format_message(reading: MmiReading, source: str) -> str:
    """Telegram HTML message for one MMI reading."""
    emoji = zone_emoji(reading.zone)
    head = (
        f'{emoji} <a href="{SITE}"><b>MMI {reading.value:.1f} — '
        f'{_esc(reading.zone)}</b></a>'
    )
    lines = [head]
    cmp = _cmp_line(reading)
    if cmp:
        lines.append(_esc(cmp))
    fac = _factors_line(reading)
    if fac:
        lines.append(_esc(fac))
    if reading.summary:
        lines.append(_esc(reading.summary))
    lines.append(f'→ {SITE}')
    lines.append(f'<i>Source:</i> <a href="{TICKERTAPE}">Tickertape Market Mood Index</a>')
    return "\n".join(lines)


def format_ntfy(reading: MmiReading, source: str) -> str:
    """Plain-text version for ntfy (no HTML)."""
    lines = [f"MMI {reading.value:.1f} — {reading.zone}"]
    cmp = _cmp_line(reading)
    if cmp:
        lines.append(cmp)
    if reading.summary:
        lines.append(reading.summary)
    lines.append(SITE)
    lines.append(f"source: {TICKERTAPE}")
    return "\n".join(lines)


def send_telegram(message: str) -> bool:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id:
        log.info("telegram: TELEGRAM_BOT_TOKEN/CHAT_ID unset — skipping")
        return False
    try:
        r = httpx.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            },
            timeout=20,
        )
        r.raise_for_status()
        log.info("telegram: sent")
        return True
    except Exception as e:  # noqa: BLE001
        log.warning("telegram send failed: %s", e)
        return False


def send_ntfy(text: str) -> bool:
    topic = os.environ.get("NTFY_TOPIC", "").strip()
    if not topic:
        log.info("ntfy: NTFY_TOPIC unset — skipping")
        return False
    base = os.environ.get("NTFY_BASE_URL", "https://ntfy.sh").rstrip("/")
    headers = {"Title": "Market Mood Index", "Tags": "chart_with_upwards_trend"}
    user = os.environ.get("NTFY_USER", "").strip()
    pw = os.environ.get("NTFY_PASSWORD", "").strip()
    auth = (user, pw) if user and pw else None
    try:
        r = httpx.post(
            f"{base}/{topic}",
            content=text.encode("utf-8"),
            headers=headers,
            auth=auth,
            timeout=20,
        )
        r.raise_for_status()
        log.info("ntfy: sent to %s/%s", base, topic)
        return True
    except Exception as e:  # noqa: BLE001
        log.warning("ntfy send failed: %s", e)
        return False


def notify_all(reading: MmiReading, source: str) -> dict[str, bool]:
    return {
        "telegram": send_telegram(format_message(reading, source)),
        "ntfy": send_ntfy(format_ntfy(reading, source)),
    }
