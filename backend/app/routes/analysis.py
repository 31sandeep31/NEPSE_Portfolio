from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ..auth import require_allowed_username
from ..db import User, session
from ..signals import PortfolioAnalysis, analyze_portfolio

router = APIRouter(prefix="/users/{username}/analysis", tags=["analysis"])


@router.get("", response_model=PortfolioAnalysis, dependencies=[Depends(require_allowed_username)])
def get_analysis(username: str):
    with session() as s:
        if s.get(User, username) is None:
            raise HTTPException(status_code=404, detail="user not found")
        return analyze_portfolio(s, username)
