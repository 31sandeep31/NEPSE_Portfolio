from __future__ import annotations

import json
from dataclasses import asdict

from fastapi import APIRouter
from sqlmodel import select

from ..db import MacroSnap, session
from ..policy_data import (
    CURRENT_FISCAL_HIGHLIGHTS,
    CURRENT_POLICY_RATES,
    EXTERNAL_LINKS,
)

router = APIRouter(prefix="/policy", tags=["policy"])


@router.get("/rates")
def get_rates():
    return {
        "monetary_rates": [asdict(r) for r in CURRENT_POLICY_RATES],
        "fiscal_highlights": CURRENT_FISCAL_HIGHLIGHTS,
        "links": EXTERNAL_LINKS,
    }


@router.get("/macro")
def get_macro():
    with session() as s:
        row = s.exec(select(MacroSnap).order_by(MacroSnap.as_of.desc()).limit(1)).first()
    if row is None:
        return {"available": False}

    forex = []
    try:
        forex = json.loads(row.forex_json) if row.forex_json else []
    except json.JSONDecodeError:
        forex = []

    return {
        "available": True,
        "as_of": row.as_of,
        "fetched_at": row.fetched_at.isoformat() if row.fetched_at else None,
        "banking": {
            "total_deposits_npr_bn": row.total_deposits_npr_bn,
            "commercial_banks_deposits_npr_bn": row.commercial_banks_deposits_npr_bn,
            "other_bfis_deposits_npr_bn": row.other_bfis_deposits_npr_bn,
            "total_lending_npr_bn": row.total_lending_npr_bn,
            "commercial_banks_lending_npr_bn": row.commercial_banks_lending_npr_bn,
            "other_bfis_lending_npr_bn": row.other_bfis_lending_npr_bn,
            "cd_ratio_pct": row.cd_ratio_pct,
        },
        "forex": forex,
    }
