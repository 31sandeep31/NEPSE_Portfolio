from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException, Query
from sqlmodel import select

from ..db import NewsItem, User, session
from ..db.repo import held_symbols_for_user

router = APIRouter(prefix="/news", tags=["news"])


@router.get("")
def list_news(
    filter: str = Query("all", pattern="^(all|monetary|fiscal|macro|corporate_action)$"),
    limit: int = 100,
):
    with session() as s:
        rows = s.exec(select(NewsItem).order_by(NewsItem.fetched_at.desc()).limit(limit * 2)).all()
    out = []
    for r in rows:
        if filter != "all":
            tags = r.policy_tags_csv.split(",") if r.policy_tags_csv else []
            if filter not in tags:
                continue
        out.append(_serialize(r))
        if len(out) >= limit:
            break
    return out


@router.get("/for-user/{username}")
def news_for_user(username: str, limit: int = 100):
    with session() as s:
        if s.get(User, username) is None:
            raise HTTPException(status_code=404, detail="user not found")
        held = set(held_symbols_for_user(s, username))
        rows = s.exec(select(NewsItem).order_by(NewsItem.fetched_at.desc()).limit(500)).all()

    relevant = []
    for r in rows:
        mentioned = set(r.symbols_mentioned_csv.split(",")) if r.symbols_mentioned_csv else set()
        if not (mentioned & held):
            continue
        relevant.append(_serialize(r))
        if len(relevant) >= limit:
            break
    return relevant


def _serialize(r: NewsItem) -> dict:
    return {
        "slug": r.slug,
        "title": r.title,
        "url": r.url,
        "published_date": r.published_date,
        "fetched_at": r.fetched_at.isoformat() if r.fetched_at else None,
        "policy_tags": r.policy_tags_csv.split(",") if r.policy_tags_csv else [],
        "sector_tags": r.sector_tags_csv.split(",") if r.sector_tags_csv else [],
        "symbols_mentioned": r.symbols_mentioned_csv.split(",") if r.symbols_mentioned_csv else [],
    }
