"""Zone classification + util tests."""

from mmi_watch.util import classify_zone, zone_emoji


def test_classify_zone_boundaries():
    assert classify_zone(0) == "Extreme Fear"
    assert classify_zone(29.9) == "Extreme Fear"
    assert classify_zone(30) == "Fear"
    assert classify_zone(49.9) == "Fear"
    assert classify_zone(50) == "Greed"
    assert classify_zone(69.9) == "Greed"
    assert classify_zone(70) == "Extreme Greed"
    assert classify_zone(73.13) == "Extreme Greed"
    assert classify_zone(100) == "Extreme Greed"


def test_zone_emoji():
    assert zone_emoji("Extreme Fear")
    assert zone_emoji("Greed")
    assert zone_emoji("unknown") == "⚪"
