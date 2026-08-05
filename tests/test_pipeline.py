"""Snapshot write + change-detection tests."""

import json
from pathlib import Path

from mmi_watch.models import MmiReading
from mmi_watch.pipeline import write_snapshot, load_previous, _change_key


def _reading(value=73.1):
    return MmiReading(value=value, zone="Extreme Greed", ts="2026-08-05T04:33:00+00:00")


def test_write_snapshot_creates_latest_and_history(tmp_path: Path):
    write_snapshot(_reading(), "tickertape", tmp_path)
    latest = json.loads((tmp_path / "latest.json").read_text(encoding="utf-8"))
    assert latest["value"] == 73.1
    assert latest["zone"] == "Extreme Greed"
    assert latest["source"] == "tickertape"
    hist = json.loads((tmp_path / "history" / "2026-08-05.json").read_text(encoding="utf-8"))
    assert len(hist) == 1
    assert hist[0]["value"] == 73.1


def test_history_appends_intraday(tmp_path: Path):
    write_snapshot(_reading(73.1), "tickertape", tmp_path)
    write_snapshot(_reading(74.5), "tickertape", tmp_path)
    hist = json.loads((tmp_path / "history" / "2026-08-05.json").read_text(encoding="utf-8"))
    assert len(hist) == 2
    assert [p["value"] for p in hist] == [73.1, 74.5]


def test_load_previous(tmp_path: Path):
    assert load_previous(tmp_path) is None
    write_snapshot(_reading(73.1), "tickertape", tmp_path)
    prev = load_previous(tmp_path)
    assert prev is not None and prev.value == 73.1


def test_change_key():
    assert _change_key(None) is None
    assert _change_key(_reading(73.14)) == _change_key(_reading(73.11))  # both round to 73.1
    assert _change_key(_reading(73.1)) != _change_key(_reading(74.2))
