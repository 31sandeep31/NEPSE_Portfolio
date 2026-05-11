"""Run with: python -m app.scraper._smoke   (from backend/)."""
from __future__ import annotations

import io
import logging
import sys

from . import fetch_fundamentals, fetch_live_prices

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")


def main() -> int:
    print("=== live prices ===")
    snap = fetch_live_prices()
    print(f"fetched_at={snap.fetched_at.isoformat()}  market_open={snap.market_open}  rows={len(snap.prices)}")
    for p in snap.prices[:5]:
        print(f"  {p.symbol:8s} ltp={p.ltp:>9.2f}  chg={p.pct_change!s:>7}%  vol={p.qty}")

    print("\n=== fundamentals ===")
    for symbol in ("NABIL", "NIFRA", "NTC"):
        try:
            f = fetch_fundamentals(symbol)
        except Exception as e:  # noqa: BLE001
            print(f"  {symbol}: FAILED -- {type(e).__name__}: {e}")
            continue
        print(
            f"  {symbol:6s} sector={f.sector!s:18s} "
            f"pe={f.pe_ratio} eps={f.eps} bv={f.book_value} "
            f"52w={f.week_52_low}-{f.week_52_high} "
            f"yld={f.yield_pct} div={f.dividend_pct}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
