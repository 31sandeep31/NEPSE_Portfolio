"""Run with: python -m app._smoke_db   (from backend/).

Exercises the full pipeline: init DB -> seed user/holdings -> run scheduler jobs once
-> read back from DB and print summary.
"""
from __future__ import annotations

import io
import logging
import sys
from datetime import datetime, timezone

from sqlmodel import select

from .db import Holding, Stock, StockFundamentals, User, init_db, session
from .db.repo import ensure_user
from .scheduler import _job_refresh_fundamentals_for_held, _job_refresh_live

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")


def seed() -> None:
    with session() as s:
        ensure_user(s, "smoketest")
        # Wipe + re-seed holdings for the test user so the script is idempotent.
        existing = s.exec(select(Holding).where(Holding.username == "smoketest")).all()
        for h in existing:
            s.delete(h)
        for sym, qty, price in [("NABIL", 10, 500.0), ("NIFRA", 50, 280.0), ("NTC", 5, 800.0)]:
            s.add(
                Holding(
                    username="smoketest",
                    symbol=sym,
                    qty=qty,
                    buy_price=price,
                    buy_date=datetime(2025, 1, 1, tzinfo=timezone.utc),
                    created_at=datetime.now(timezone.utc),
                )
            )
        s.commit()


def report() -> None:
    with session() as s:
        stock_count = len(s.exec(select(Stock)).all())
        fund_count = len(s.exec(select(StockFundamentals)).all())
        users = s.exec(select(User)).all()
        holdings = s.exec(select(Holding)).all()
        sample_stock = s.exec(select(Stock).where(Stock.symbol == "NABIL")).first()
        sample_fund = s.exec(select(StockFundamentals).where(StockFundamentals.symbol == "NABIL")).first()

    print("\n=== DB after one cycle ===")
    print(f"stocks rows:        {stock_count}")
    print(f"fundamentals rows:  {fund_count}")
    print(f"users:              {[u.username for u in users]}")
    print(f"holdings:           {len(holdings)}  -> {[(h.symbol, h.qty, h.buy_price) for h in holdings]}")
    if sample_stock:
        print(
            f"NABIL live:         ltp={sample_stock.ltp}  pct={sample_stock.pct_change}  "
            f"vol={sample_stock.qty}  updated_at={sample_stock.updated_at}"
        )
    if sample_fund:
        print(
            f"NABIL fundamentals: pe={sample_fund.pe_ratio}  eps={sample_fund.eps}  "
            f"bv={sample_fund.book_value}  52w={sample_fund.week_52_low}-{sample_fund.week_52_high}"
        )


def main() -> int:
    init_db()
    seed()
    print("\n--- running live job ---")
    _job_refresh_live()
    print("\n--- running fundamentals job ---")
    _job_refresh_fundamentals_for_held()
    report()
    return 0


if __name__ == "__main__":
    sys.exit(main())
