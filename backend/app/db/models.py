from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Stock(SQLModel, table=True):
    symbol: str = Field(primary_key=True)
    sector: Optional[str] = None
    ltp: Optional[float] = None
    point_change: Optional[float] = None
    pct_change: Optional[float] = None
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    qty: Optional[int] = None
    prev_close: Optional[float] = None
    updated_at: datetime


class StockFundamentals(SQLModel, table=True):
    symbol: str = Field(primary_key=True)
    sector: Optional[str] = None
    eps: Optional[float] = None
    eps_period: Optional[str] = None
    pe_ratio: Optional[float] = None
    book_value: Optional[float] = None
    market_cap: Optional[float] = None
    week_52_high: Optional[float] = None
    week_52_low: Optional[float] = None
    avg_120_day: Optional[float] = None
    avg_180_day: Optional[float] = None
    yield_pct: Optional[float] = None
    dividend_pct: Optional[float] = None
    dividend_period: Optional[str] = None
    listed_shares: Optional[float] = None
    paidup_value: Optional[float] = None
    total_paidup_value: Optional[float] = None
    fetched_at: datetime


class User(SQLModel, table=True):
    username: str = Field(primary_key=True, min_length=2, max_length=40)
    created_at: datetime


class Holding(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(foreign_key="user.username", index=True)
    symbol: str = Field(index=True)
    qty: float
    buy_price: float
    buy_date: datetime
    target_pct: Optional[float] = None
    created_at: datetime
