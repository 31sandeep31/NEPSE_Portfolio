from __future__ import annotations

import logging
import re
from datetime import date, datetime, timezone

from bs4 import BeautifulSoup
from pydantic import BaseModel

from ._http import client

log = logging.getLogger(__name__)

LIST_URL = "https://www.sharesansar.com/category/news"
SLUG_DATE_RX = re.compile(r"(\d{4}-\d{2}-\d{2})$")


class NewsArticle(BaseModel):
    title: str
    url: str
    slug: str
    published_date: str | None  # ISO date if discoverable from slug
    fetched_at: datetime


class NewsError(RuntimeError):
    pass


def fetch_news_listing() -> list[NewsArticle]:
    with client() as c:
        r = c.get(LIST_URL)
    if r.status_code != 200:
        raise NewsError(f"sharesansar news listing HTTP {r.status_code}")

    soup = BeautifulSoup(r.text, "html.parser")
    out: list[NewsArticle] = []
    now = datetime.now(timezone.utc)

    seen_slugs: set[str] = set()
    for a in soup.select("a[href*='/newsdetail/']"):
        href = a.get("href", "")
        title = a.get_text(strip=True)
        # Quality filter: Sharesansar's sidebar nav uses /newsdetail/ links with 1-3 word
        # anchor texts ("Commercial Banks", "Insurance Companies"). Real article titles are
        # 5+ words. Filtering by word count cleanly separates the two.
        if not title or len(title.split()) < 5:
            continue
        slug = href.rstrip("/").split("/newsdetail/")[-1] if "/newsdetail/" in href else href
        slug = slug.split("?")[0]
        if slug in seen_slugs:
            continue
        seen_slugs.add(slug)
        full_url = href if href.startswith("http") else f"https://www.sharesansar.com{href}"
        published = _date_from_slug(slug)
        out.append(
            NewsArticle(
                title=title,
                url=full_url,
                slug=slug,
                published_date=published,
                fetched_at=now,
            )
        )
    log.info("news: scraped %d articles", len(out))
    return out


def _date_from_slug(slug: str) -> str | None:
    m = SLUG_DATE_RX.search(slug)
    if not m:
        return None
    s = m.group(1)
    try:
        date.fromisoformat(s)
    except ValueError:
        return None
    return s


# --- tag detection ---

# Policy keywords. Lowercase substring match against title.
POLICY_TAG_KEYWORDS: dict[str, list[str]] = {
    "monetary": [
        "monetary policy", "nrb", "rastra bank", "policy rate", "bank rate",
        "interest rate", "crr ", "slr ", "cash reserve", "statutory liquidity",
        "open market operation", "repo rate", "liquidity",
    ],
    "fiscal": [
        "budget", "fiscal policy", "finance minister", "ministry of finance",
        "tax rate", "income tax", "vat ", "customs duty", "sebon ",
        "capital gains tax", "fiscal deficit", "revenue collection",
    ],
    "macro": [
        "remittance", "gdp", "inflation", "cpi ", "balance of payment",
        "foreign reserve", "current account", "trade deficit",
    ],
    "corporate_action": [
        "bonus share", "right share", "dividend", "agm", "book close",
        "ipo ", "auction", "rights issue", "fpo", "merger",
    ],
}

# Standard NEPSE sector names. Title-cased; we match case-insensitively.
SECTOR_KEYWORDS: list[str] = [
    "commercial bank", "development bank", "finance compan", "microfinance",
    "hydropower", "hotel", "tourism", "insurance", "investment",
    "manufacturing", "trading", "non life insurance", "life insurance",
]


def detect_tags(title: str, held_symbols: list[str], all_known_symbols: set[str]) -> dict:
    """Return a dict of detected tags for an article title.

    Result has shape:
        {
            "policy": ["monetary", "fiscal", ...],
            "sectors": ["insurance", ...],
            "symbols_mentioned": ["NABIL", ...],  (drawn from all_known_symbols)
            "symbols_held": ["NABIL", ...],       (intersection with held_symbols)
        }
    """
    t = title.lower()
    policy = [tag for tag, kws in POLICY_TAG_KEYWORDS.items() if any(kw in t for kw in kws)]
    sectors = [kw for kw in SECTOR_KEYWORDS if kw in t]

    # Symbol mentions: word-boundary, uppercase. Stricter to avoid false positives on common words.
    upper = title
    symbols_mentioned: list[str] = []
    for sym in all_known_symbols:
        if re.search(rf"\b{re.escape(sym)}\b", upper):
            symbols_mentioned.append(sym)

    symbols_held = sorted(set(symbols_mentioned) & set(held_symbols))
    return {
        "policy": policy,
        "sectors": sectors,
        "symbols_mentioned": sorted(symbols_mentioned),
        "symbols_held": symbols_held,
    }
