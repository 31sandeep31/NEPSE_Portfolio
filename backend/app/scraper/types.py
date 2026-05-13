from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class LivePrice(BaseModel):
    symbol: str
    ltp: float
    point_change: float | None = None
    pct_change: float | None = None
    open: float | None = None
    high: float | None = None
    low: float | None = None
    qty: int | None = None
    prev_close: float | None = None


class LiveSnapshot(BaseModel):
    fetched_at: datetime
    market_open: bool
    prices: list[LivePrice]


class DailyBar(BaseModel):
    symbol: str
    date: str  # ISO date
    open: float | None = None
    high: float | None = None
    low: float | None = None
    close: float | None = None
    volume: int | None = None


class Fundamentals(BaseModel):
    symbol: str
    sector: str | None = None
    eps: float | None = None
    eps_period: str | None = None
    pe_ratio: float | None = None
    book_value: float | None = None
    market_cap: float | None = None
    week_52_high: float | None = None
    week_52_low: float | None = None
    avg_120_day: float | None = None
    avg_180_day: float | None = None
    yield_pct: float | None = None
    dividend_pct: float | None = None
    dividend_period: str | None = None
    listed_shares: float | None = None
    paidup_value: float | None = None
    total_paidup_value: float | None = None
    fetched_at: datetime
