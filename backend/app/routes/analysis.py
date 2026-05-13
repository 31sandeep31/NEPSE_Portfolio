from __future__ import annotations

import logging
import threading

from fastapi import APIRouter
from pydantic import BaseModel

from ..db import session
from ..db.repo import upsert_fundamentals
from ..scraper import FundamentalsError, fetch_fundamentals
from ..signals import HoldingInput, PortfolioAnalysis, analyze_portfolio

log = logging.getLogger(__name__)
router = APIRouter(tags=["analysis"])


class AnalysisRequest(BaseModel):
    holdings: list[HoldingInput]


@router.post("/analysis", response_model=PortfolioAnalysis)
def post_analysis(body: AnalysisRequest):
    """Stateless analysis. The browser sends its localStorage holdings; server returns
    signals + P&L. No user record is created or stored. If the browser holds a symbol
    whose fundamentals we haven't fetched yet, we fire off a background fetch so the
    next call has data."""
    with session() as s:
        result = analyze_portfolio(s, body.holdings)

    # Best-effort warm of any symbols missing fundamentals (background, non-blocking).
    missing = [h.symbol for h in result.holdings if not _has_fundamentals(h.symbol)]
    for sym in missing[:5]:  # cap to avoid overloading on a huge portfolio
        threading.Thread(target=_warm_fundamentals, args=(sym,), daemon=True).start()

    return result


def _has_fundamentals(symbol: str) -> bool:
    from ..db import StockFundamentals
    with session() as s:
        return s.get(StockFundamentals, symbol) is not None


def _warm_fundamentals(symbol: str) -> None:
    try:
        f = fetch_fundamentals(symbol)
    except FundamentalsError as e:
        log.warning("warm_fundamentals[%s] failed: %s", symbol, e)
        return
    with session() as s:
        upsert_fundamentals(s, f)
    log.info("warm_fundamentals[%s]: ok", symbol)
