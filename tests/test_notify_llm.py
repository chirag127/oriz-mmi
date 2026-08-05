"""Notifier formatting + LLM fallback tests (no network, no real send)."""

from mmi_watch.models import Comparison, MmiReading
from mmi_watch.notify.channels import format_message, format_ntfy, send_telegram, send_ntfy
from mmi_watch.llm.summary import commentary, _template


def _reading(value=73.1, zone="Extreme Greed"):
    r = MmiReading(value=value, zone=zone, nifty=24603.25, vix=-11.86, fii=-153773)
    r.comparisons = [
        Comparison("Yesterday", 73.8, "Extreme Greed"),
        Comparison("Last week", 55.9, "Greed"),
    ]
    return r


def test_format_message_html():
    r = _reading()
    r.summary = "test take"
    m = format_message(r, "tickertape")
    assert "73.1" in m
    assert "Extreme Greed" in m
    assert "mmi.oriz.in" in m
    assert "Yesterday 74" in m
    assert "test take" in m


def test_format_ntfy_plain():
    r = _reading()
    m = format_ntfy(r, "tickertape")
    assert "<" not in m  # no HTML
    assert "73.1" in m
    assert "mmi.oriz.in" in m


def test_notifiers_noop_without_env(monkeypatch):
    for k in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID", "NTFY_TOPIC"):
        monkeypatch.delenv(k, raising=False)
    assert send_telegram("hi") is False
    assert send_ntfy("hi") is False


def test_template_commentary():
    r = _reading()
    out = _template(r)
    assert "73.1" in out
    assert "Extreme Greed" in out
    assert "down" in out.lower()  # 73.1 < 73.8 yesterday


def test_commentary_falls_back_without_llm(monkeypatch):
    monkeypatch.setenv("MMI_DISABLE_LLM", "1")
    out = commentary(_reading())
    assert isinstance(out, str) and len(out) > 10
    assert "Extreme Greed" in out
