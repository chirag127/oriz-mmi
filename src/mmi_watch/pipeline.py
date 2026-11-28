"""Pipeline: read MMI -> classify zone -> g4f one-line commentary (template
fallback) -> write data/latest.json + data/history/<date>.json -> detect change
-> notify.

Notification policy (user directive 2026-08-05): SEND EVERY RUN — MMI moves
intraday and the user asked for an hourly notification. `changed` is still
computed + logged (drives the "moved" note), but does not gate the send.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from .llm.summary import commentary
from .models import MmiReading
from .sources import read_first_available

log = logging.getLogger("mmi_watch")


def _change_key(reading: MmiReading | None) -> float | None:
    return round(reading.value, 1) if reading else None


def load_previous(data_dir: Path) -> MmiReading | None:
    latest = data_dir / "latest.json"
    if not latest.exists():
        return None
    try:
        raw = json.loads(latest.read_text(encoding="utf-8"))
        return MmiReading(value=float(raw.get("value", 0.0)), zone=raw.get("zone", ""))
    except Exception as e:  # noqa: BLE001
        log.warning("could not read previous reading: %s", e)
        return None


def write_snapshot(reading: MmiReading, source: str, data_dir: Path) -> None:
    """latest.json = current reading. history/<date>.json = append-only intraday
    log for that UTC day (drives the sparkline)."""
    data_dir.mkdir(parents=True, exist_ok=True)
    payload = {"source": source, **reading.to_dict()}
    (data_dir / "latest.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    hist_dir = data_dir / "history"
    hist_dir.mkdir(exist_ok=True)
    day = reading.ts[:10] or "snapshot"
    hist_file = hist_dir / f"{day}.json"
    points: list[dict] = []
    if hist_file.exists():
        try:
            points = json.loads(hist_file.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            points = []
    points.append({"ts": reading.ts, "value": reading.value, "zone": reading.zone})
    hist_file.write_text(json.dumps(points, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info("wrote latest.json + history/%s.json (%d points)", day, len(points))


def run(
    data_dir: Path,
    with_llm: bool = True,
    with_notify: bool = True,
) -> tuple[MmiReading, bool]:
    """Full run. Returns (reading, changed)."""
    source, reading = read_first_available()

    if with_llm:
        reading.summary = commentary(reading)

    prev = load_previous(data_dir)
    changed = _change_key(prev) != _change_key(reading)
    log.info("MMI %.2f (%s), changed=%s", reading.value, reading.zone, changed)

    write_snapshot(reading, source, data_dir)

    # Notification moved to oriz-nifty-signal: its 1PM job reads this repo's
    # published data/latest.json and sends ONE combined Nifty+MMI message.
    # This repo stays a pure MMI data producer (writes latest.json + history).
    if with_notify:
        log.info("notify handled by oriz-nifty-signal (combined); skipping self-send")

    return reading, changed
