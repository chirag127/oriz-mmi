# oriz-mmi — India Market Mood Index Tracker

Live at **[mmi.oriz.in](https://mmi.oriz.in)** · hourly Tickertape Market Mood Index (MMI) tracker + dark fear/greed dial site.

![license](https://img.shields.io/github/license/chirag127/oriz-mmi)
![last commit](https://img.shields.io/github/last-commit/chirag127/oriz-mmi)

Reads Tickertape's Market Mood Index (the 0–100 India fear/greed sentiment gauge), classifies the zone, writes a one-line market-mood commentary, and notifies Telegram + ntfy — every hour, via GitHub Actions. The committed JSON drives a static Astro dial site.

## How it works

```
read MMI (keyless JSON API) → classify zone → g4f one-line commentary (keyless,
  optional) → write data/latest.json + data/history/<date>.json → detect change
  → notify Telegram/ntfy (every hour) → commit → CF Pages rebuilds mmi.oriz.in
```

- **Language:** Python (reader) + Astro (site). No external DB — the repo IS the database (`data/latest.json` + `data/history/`), free + versioned.
- **Source (verified 2026-08-05):** `https://api.tickertape.in/mmi/now` — a **keyless JSON endpoint** (no scraping, no JS render). Failover: Playwright reads the same `nowData` off the page `__NEXT_DATA__` if the API is ever blocked.
- **Zones:** `<30` Extreme Fear · `30–50` Fear · `50–70` Greed · `>70` Extreme Greed.
- **LLM:** `g4f` (GPT4Free), keyless, best-effort — deterministic template one-liner if every provider fails. Never blocks the run.
- **Notify:** Telegram (`TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID`) + ntfy (`NTFY_TOPIC`). Sends **every hour** (MMI moves intraday).

## Run locally

```bash
pip install -e ".[dev]"
python -m mmi_watch --data data --no-notify   # read + classify + commentary
pytest -q                                     # tests
cd web && npm install && npm run build        # build the site (use npm, not pnpm)
```

Flags: `--no-llm`, `--no-notify`, `--iterations N --interval S` (self-loop).

## Deploy

CF Pages project `oriz-mmi` builds `web/` on push (`web/dist`). The hourly Action commits fresh data; the push triggers the rebuild. Set repo secrets: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `NTFY_TOPIC` (+ optional `NTFY_*`).

## Disclaimer

Not investment advice. MMI is a sentiment gauge, not a trade signal.
