"""CLI: python -m mmi_watch [--data DIR] [--no-llm] [--no-notify]
[--iterations N] [--interval S]

Self-loop (--iterations>1) approximates sub-hourly polling inside one GitHub
Actions run, since GitHub throttles high-frequency cron.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from .pipeline import run
from .util import configure_logging, log


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="mmi_watch", description="Tickertape MMI watch")
    p.add_argument("--data", default="data", help="data dir for JSON snapshots")
    p.add_argument("--no-llm", action="store_true", help="skip g4f commentary")
    p.add_argument("--no-notify", action="store_true", help="skip Telegram/ntfy")
    p.add_argument("--iterations", type=int, default=1, help="self-loop count")
    p.add_argument("--interval", type=int, default=60, help="seconds between iterations")
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args(argv)

    configure_logging(args.verbose)
    data_dir = Path(args.data)

    rc = 0
    for i in range(1, args.iterations + 1):
        log.info("=== iteration %d/%d ===", i, args.iterations)
        try:
            reading, changed = run(
                data_dir=data_dir,
                with_llm=not args.no_llm,
                with_notify=not args.no_notify,
            )
            log.info("done: MMI %.2f (%s), changed=%s", reading.value, reading.zone, changed)
        except Exception as e:  # noqa: BLE001
            log.error("iteration %d failed: %s", i, e)
            rc = 1
            break
        if i < args.iterations:
            time.sleep(args.interval)
    return rc


if __name__ == "__main__":
    sys.exit(main())
