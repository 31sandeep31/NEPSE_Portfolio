from __future__ import annotations

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from ..db import Stock, StockFundamentals, session

router = APIRouter(prefix="/stocks", tags=["stocks"])


@router.get("")
def list_stocks(sector: str | None = None, limit: int = 500):
    with session() as s:
        stmt = select(Stock)
        if sector:
            stmt = stmt.where(Stock.sector == sector)
        rows = s.exec(stmt.limit(limit)).all()
    return [_serialize_stock(r) for r in rows]


@router.get("/{symbol}")
def get_stock(symbol: str):
    symbol = symbol.upper().strip()
    with session() as s:
        stock = s.get(Stock, symbol)
        if stock is None:
            raise HTTPException(status_code=404, detail=f"{symbol} not found")
        fund = s.get(StockFundamentals, symbol)
    return {
        "live": _serialize_stock(stock),
        "fundamentals": _serialize_fundamentals(fund) if fund else None,
    }


def _serialize_stock(s: Stock) -> dict:
    return {
        "symbol": s.symbol,
        "sector": s.sector,
        "ltp": s.ltp,
        "point_change": s.point_change,
        "pct_change": s.pct_change,
        "open": s.open,
        "high": s.high,
        "low": s.low,
        "qty": s.qty,
        "prev_close": s.prev_close,
        "updated_at": s.updated_at.isoformat() if s.updated_at else None,
    }


def _serialize_fundamentals(f: StockFundamentals) -> dict:
    return {
        "sector": f.sector,
        "eps": f.eps,
        "eps_period": f.eps_period,
        "pe_ratio": f.pe_ratio,
        "book_value": f.book_value,
        "market_cap": f.market_cap,
        "week_52_high": f.week_52_high,
        "week_52_low": f.week_52_low,
        "avg_120_day": f.avg_120_day,
        "avg_180_day": f.avg_180_day,
        "yield_pct": f.yield_pct,
        "dividend_pct": f.dividend_pct,
        "dividend_period": f.dividend_period,
        "listed_shares": f.listed_shares,
        "paidup_value": f.paidup_value,
        "fetched_at": f.fetched_at.isoformat() if f.fetched_at else None,
    }
