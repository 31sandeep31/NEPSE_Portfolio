from __future__ import annotations

from datetime import datetime, timezone

from sqlmodel import Session, select

from ..scraper.types import DailyBar
from ..scraper.types import Fundamentals as ScrapedFundamentals
from ..scraper.types import LiveSnapshot
from .models import Holding, PriceHistory, Stock, StockFundamentals, User


def upsert_live_snapshot(s: Session, snap: LiveSnapshot) -> int:
    """Overwrite per-symbol live state. Returns count written."""
    n = 0
    for p in snap.prices:
        existing = s.get(Stock, p.symbol)
        if existing is None:
            existing = Stock(symbol=p.symbol, updated_at=snap.fetched_at)
        existing.ltp = p.ltp
        existing.point_change = p.point_change
        existing.pct_change = p.pct_change
        existing.open = p.open
        existing.high = p.high
        existing.low = p.low
        existing.qty = p.qty
        existing.prev_close = p.prev_close
        existing.updated_at = snap.fetched_at
        s.add(existing)
        n += 1
    s.commit()
    return n


def upsert_fundamentals(s: Session, f: ScrapedFundamentals) -> None:
    existing = s.get(StockFundamentals, f.symbol)
    if existing is None:
        existing = StockFundamentals(symbol=f.symbol, fetched_at=f.fetched_at)
    existing.sector = f.sector
    existing.eps = f.eps
    existing.eps_period = f.eps_period
    existing.pe_ratio = f.pe_ratio
    existing.book_value = f.book_value
    existing.market_cap = f.market_cap
    existing.week_52_high = f.week_52_high
    existing.week_52_low = f.week_52_low
    existing.avg_120_day = f.avg_120_day
    existing.avg_180_day = f.avg_180_day
    existing.yield_pct = f.yield_pct
    existing.dividend_pct = f.dividend_pct
    existing.dividend_period = f.dividend_period
    existing.listed_shares = f.listed_shares
    existing.paidup_value = f.paidup_value
    existing.total_paidup_value = f.total_paidup_value
    existing.fetched_at = f.fetched_at
    s.add(existing)

    # Mirror sector onto the live row too — handy for /stocks listings.
    stock = s.get(Stock, f.symbol)
    if stock is not None and f.sector and not stock.sector:
        stock.sector = f.sector
        s.add(stock)
    s.commit()


def upsert_daily_bars(s: Session, bars: list[DailyBar]) -> int:
    n = 0
    for b in bars:
        existing = s.get(PriceHistory, (b.symbol, b.date))
        if existing is None:
            existing = PriceHistory(symbol=b.symbol, date=b.date)
        existing.open = b.open
        existing.high = b.high
        existing.low = b.low
        existing.close = b.close
        existing.volume = b.volume
        s.add(existing)
        n += 1
    s.commit()
    return n


def history_for(s: Session, symbol: str, limit: int = 90) -> list[PriceHistory]:
    rows = s.exec(
        select(PriceHistory)
        .where(PriceHistory.symbol == symbol)
        .order_by(PriceHistory.date.desc())
        .limit(limit)
    ).all()
    rows.reverse()  # oldest first for charting
    return rows


def history_min_max_date(s: Session) -> tuple[str | None, str | None]:
    rows = s.exec(select(PriceHistory.date).distinct()).all()
    if not rows:
        return None, None
    dates = sorted(rows)
    return dates[0], dates[-1]


def held_symbols(s: Session) -> list[str]:
    """All distinct symbols anyone is holding — used to decide whose fundamentals to refresh."""
    rows = s.exec(select(Holding.symbol).distinct()).all()
    return [r for r in rows]


def held_symbols_for_user(s: Session, username: str) -> list[str]:
    rows = s.exec(select(Holding.symbol).where(Holding.username == username).distinct()).all()
    return list(rows)


def all_known_symbols(s: Session) -> list[str]:
    rows = s.exec(select(Stock.symbol)).all()
    return list(rows)


def ensure_user(s: Session, username: str) -> User:
    existing = s.get(User, username)
    if existing is not None:
        return existing
    u = User(username=username, created_at=datetime.now(timezone.utc))
    s.add(u)
    s.commit()
    return u
