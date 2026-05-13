from __future__ import annotations

from collections import defaultdict
from statistics import mean

from fastapi import APIRouter
from sqlmodel import select

from ..db import Stock, session

router = APIRouter(prefix="/movers", tags=["movers"])


@router.get("")
def get_movers(limit: int = 5):
    """Top gainers, top losers, biggest volume, and a sector summary."""
    with session() as s:
        rows = s.exec(select(Stock).where(Stock.pct_change.is_not(None))).all()

    rows_priced = [r for r in rows if r.pct_change is not None]

    gainers = sorted(rows_priced, key=lambda r: r.pct_change, reverse=True)[:limit]
    losers = sorted(rows_priced, key=lambda r: r.pct_change)[:limit]
    volume = sorted(
        [r for r in rows if r.qty is not None], key=lambda r: r.qty, reverse=True
    )[:limit]

    by_sector: dict[str, list[Stock]] = defaultdict(list)
    for r in rows_priced:
        if r.sector:
            by_sector[r.sector].append(r)

    sector_summary = [
        {
            "sector": sec,
            "count": len(items),
            "avg_pct_change": round(mean(i.pct_change for i in items), 2),
            "up": sum(1 for i in items if i.pct_change > 0),
            "down": sum(1 for i in items if i.pct_change < 0),
        }
        for sec, items in by_sector.items()
        if len(items) >= 2
    ]
    sector_summary.sort(key=lambda x: x["avg_pct_change"], reverse=True)

    return {
        "gainers": [_serialize(r) for r in gainers],
        "losers": [_serialize(r) for r in losers],
        "by_volume": [_serialize(r) for r in volume],
        "sector_summary": sector_summary,
    }


def _serialize(r: Stock) -> dict:
    return {
        "symbol": r.symbol,
        "ltp": r.ltp,
        "pct_change": r.pct_change,
        "qty": r.qty,
        "sector": r.sector,
    }
