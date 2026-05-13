from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel
from sqlmodel import select

from ..db import NewsItem, session

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


class RelevantRequest(BaseModel):
    symbols: list[str]


@router.post("/relevant")
def news_relevant(body: RelevantRequest, limit: int = 100):
    """Stateless: caller posts the symbols it cares about, server returns news
    that mentions any of them. Used by the 'Affecting my portfolio' filter."""
    interested = {s.strip().upper() for s in body.symbols if s.strip()}
    with session() as s:
        rows = s.exec(select(NewsItem).order_by(NewsItem.fetched_at.desc()).limit(500)).all()

    out = []
    for r in rows:
        mentioned = set(r.symbols_mentioned_csv.split(",")) if r.symbols_mentioned_csv else set()
        if not (mentioned & interested):
            continue
        out.append(_serialize(r))
        if len(out) >= limit:
            break
    return out


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
