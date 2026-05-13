from __future__ import annotations

import logging
import re
from datetime import datetime, timezone

from bs4 import BeautifulSoup
from pydantic import BaseModel

from ._http import client
from ._parse import to_float

log = logging.getLogger(__name__)

NRB_URL = "https://www.nrb.org.np/"


class ForexRate(BaseModel):
    currency: str
    buy: float
    sell: float


class BankingAggregates(BaseModel):
    as_of: str  # ISO date string from the page
    total_deposits_npr_bn: float | None = None
    commercial_banks_deposits_npr_bn: float | None = None
    other_bfis_deposits_npr_bn: float | None = None
    total_lending_npr_bn: float | None = None
    commercial_banks_lending_npr_bn: float | None = None
    other_bfis_lending_npr_bn: float | None = None
    cd_ratio_pct: float | None = None


class MacroSnapshot(BaseModel):
    fetched_at: datetime
    forex: list[ForexRate]
    banking: BankingAggregates | None


class MacroError(RuntimeError):
    pass


def _parse_dd_mm_yyyy(s: str) -> str | None:
    m = re.match(r"(\d{2})/(\d{2})/(\d{4})", s.strip())
    if not m:
        return None
    return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"


def fetch_macro_snapshot() -> MacroSnapshot:
    with client() as c:
        r = c.get(NRB_URL)
    if r.status_code != 200:
        raise MacroError(f"NRB HTTP {r.status_code}")

    soup = BeautifulSoup(r.text, "html.parser")
    tables = soup.find_all("table")

    forex: list[ForexRate] = []
    banking: BankingAggregates | None = None

    for t in tables:
        rows = t.find_all("tr")
        if not rows:
            continue
        header = [c.get_text(strip=True).lower() for c in rows[0].find_all(["th", "td"])]
        if "currency" in header and "buy" in header and "sell" in header:
            for tr in rows[1:]:
                cells = [c.get_text(strip=True) for c in tr.find_all(["td", "th"])]
                if len(cells) >= 3:
                    cur = cells[0]
                    b = to_float(cells[1])
                    s = to_float(cells[2])
                    if cur and b is not None and s is not None:
                        forex.append(ForexRate(currency=cur, buy=b, sell=s))
        elif any("last updated" in h for h in header) or any("total deposits" in (c.get_text(strip=True).lower())
                                                              for tr in rows for c in tr.find_all(["td", "th"])[:1]):
            # Banking aggregates table
            as_of = None
            data: dict[str, float | None] = {}
            for tr in rows:
                cells = [c.get_text(" ", strip=True) for c in tr.find_all(["td", "th"])]
                if len(cells) < 2:
                    continue
                label = cells[0].lower()
                if "last updated" in label:
                    as_of = _parse_dd_mm_yyyy(cells[1])
                    continue
                v = to_float(cells[1])
                if "commercial banks total deposits" in label:
                    data["commercial_banks_deposits_npr_bn"] = v
                elif "other bfis total deposits" in label:
                    data["other_bfis_deposits_npr_bn"] = v
                elif "total deposits" in label:
                    data["total_deposits_npr_bn"] = v
                elif "commercial banks total lending" in label:
                    data["commercial_banks_lending_npr_bn"] = v
                elif "other bfis total lending" in label:
                    data["other_bfis_lending_npr_bn"] = v
                elif "total lending" in label:
                    data["total_lending_npr_bn"] = v
                elif "cd ratio" in label or "cd-ratio" in label:
                    data["cd_ratio_pct"] = v
            if as_of:
                banking = BankingAggregates(as_of=as_of, **data)

    log.info("macro: forex=%d rates, banking=%s", len(forex), "yes" if banking else "no")
    return MacroSnapshot(
        fetched_at=datetime.now(timezone.utc),
        forex=forex,
        banking=banking,
    )
