from __future__ import annotations

import logging
import threading
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import select

from ..auth import require_allowed_username
from ..db import Holding, Stock, User, session
from ..db.repo import upsert_fundamentals
from ..rate_limit import limit_writes
from ..scraper import FundamentalsError, fetch_fundamentals

log = logging.getLogger(__name__)
router = APIRouter(prefix="/users/{username}/holdings", tags=["holdings"])


class HoldingIn(BaseModel):
    symbol: str
    qty: float
    buy_price: float
    buy_date: datetime
    target_pct: float | None = None


@router.get("", dependencies=[Depends(require_allowed_username)])
def list_holdings(username: str):
    _require_user(username)
    with session() as s:
        rows = s.exec(select(Holding).where(Holding.username == username)).all()
    return [_serialize(h) for h in rows]


@router.post("", dependencies=[Depends(limit_writes), Depends(require_allowed_username)])
def add_holding(username: str, body: HoldingIn):
    _require_user(username)
    symbol = body.symbol.upper().strip()

    with session() as s:
        if s.get(Stock, symbol) is None:
            raise HTTPException(status_code=400, detail=f"unknown symbol: {symbol}")

        h = Holding(
            username=username,
            symbol=symbol,
            qty=body.qty,
            buy_price=body.buy_price,
            buy_date=body.buy_date,
            target_pct=body.target_pct,
            created_at=datetime.now(timezone.utc),
        )
        s.add(h)
        s.commit()
        s.refresh(h)
        holding_id = h.id

    # Kick off a one-shot fundamentals fetch in the background so the first analysis
    # call has data even before tomorrow's daily refresh.
    threading.Thread(target=_warm_fundamentals, args=(symbol,), daemon=True).start()

    with session() as s:
        h = s.get(Holding, holding_id)
        return _serialize(h)


@router.delete("/{holding_id}", dependencies=[Depends(limit_writes), Depends(require_allowed_username)])
def delete_holding(username: str, holding_id: int):
    _require_user(username)
    with session() as s:
        h = s.get(Holding, holding_id)
        if h is None or h.username != username:
            raise HTTPException(status_code=404, detail="holding not found")
        s.delete(h)
        s.commit()
    return {"deleted": holding_id}


def _require_user(username: str) -> None:
    with session() as s:
        if s.get(User, username) is None:
            raise HTTPException(status_code=404, detail="user not found")


def _warm_fundamentals(symbol: str) -> None:
    try:
        f = fetch_fundamentals(symbol)
    except FundamentalsError as e:
        log.warning("warm_fundamentals[%s] failed: %s", symbol, e)
        return
    with session() as s:
        upsert_fundamentals(s, f)
    log.info("warm_fundamentals[%s]: ok", symbol)


def _serialize(h: Holding) -> dict:
    return {
        "id": h.id,
        "username": h.username,
        "symbol": h.symbol,
        "qty": h.qty,
        "buy_price": h.buy_price,
        "buy_date": h.buy_date.isoformat() if h.buy_date else None,
        "target_pct": h.target_pct,
        "created_at": h.created_at.isoformat() if h.created_at else None,
    }
