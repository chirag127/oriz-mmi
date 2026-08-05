"""Parser tests against the real Tickertape API fixture."""

import json
from pathlib import Path

from mmi_watch.sources.tickertape import parse_reading

FIXTURE = Path(__file__).parent / "fixtures" / "mmi_now.json"


def _data():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))["data"]


def test_parse_reading_value_and_zone():
    r = parse_reading(_data())
    assert 0 <= r.value <= 100
    assert r.zone in {"Extreme Fear", "Fear", "Greed", "Extreme Greed"}
    assert r.source_date  # source timestamp captured


def test_parse_reading_comparisons():
    r = parse_reading(_data())
    labels = {c.label for c in r.comparisons}
    # fixture has all four horizons
    assert {"Yesterday", "Last week", "Last month", "Last year"} <= labels
    for c in r.comparisons:
        assert c.value is not None
        assert c.zone


def test_parse_reading_factors():
    r = parse_reading(_data())
    assert r.nifty is not None
    assert r.raw is not None


def test_parse_reading_missing_indicator():
    import pytest

    with pytest.raises(ValueError):
        parse_reading({"date": "x"})
