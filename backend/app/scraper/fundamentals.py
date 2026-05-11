from __future__ import annotations

import logging
from datetime import datetime, timezone

from bs4 import BeautifulSoup

from ._http import client
from ._parse import split_high_low, split_parenthetical, to_float
from .types import Fundamentals

log = logging.getLogger(__name__)

URL_TEMPLATE = "https://merolagani.com/CompanyDetail.aspx?symbol={symbol}"


class FundamentalsError(RuntimeError):
    pass


def fetch_fundamentals(symbol: str) -> Fundamentals:
    symbol = symbol.upper().strip()
    with client() as c:
        r = c.get(URL_TEMPLATE.format(symbol=symbol))
    if r.status_code != 200:
        raise FundamentalsError(f"merolagani returned HTTP {r.status_code} for {symbol}")

    rows = _extract_label_value_pairs(r.text)
    if not rows:
        raise FundamentalsError(f"merolagani: no label/value rows for {symbol}")

    f = Fundamentals(symbol=symbol, fetched_at=datetime.now(timezone.utc))

    f.sector = rows.get("Sector")

    if (raw := rows.get("EPS")):
        v, period = split_parenthetical(raw)
        f.eps = to_float(v)
        f.eps_period = period

    f.pe_ratio = to_float(rows.get("P/E Ratio"))
    f.book_value = to_float(rows.get("Book Value"))
    f.market_cap = to_float(rows.get("Market Capitalization"))

    if (raw := rows.get("52 Weeks High - Low") or rows.get("52 Weeks High-Low")):
        hi, lo = split_high_low(raw)
        f.week_52_high, f.week_52_low = hi, lo

    f.avg_120_day = to_float(rows.get("120 Day Average"))
    f.avg_180_day = to_float(rows.get("180 Day Average"))
    f.yield_pct = to_float(rows.get("1 Year Yield"))

    if (raw := rows.get("% Dividend")):
        v, period = split_parenthetical(raw)
        f.dividend_pct = to_float(v)
        f.dividend_period = period

    f.listed_shares = to_float(rows.get("Listed Shares") or rows.get("Shares Outstanding"))
    f.paidup_value = to_float(rows.get("Paidup Value"))
    f.total_paidup_value = to_float(rows.get("Total Paidup Value"))

    log.info("fundamentals[%s]: pe=%s eps=%s bv=%s", symbol, f.pe_ratio, f.eps, f.book_value)
    return f


def _extract_label_value_pairs(html: str) -> dict[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    out: dict[str, str] = {}
    for tr in soup.find_all("tr"):
        cells = tr.find_all(["th", "td"])
        if len(cells) >= 2:
            label = cells[0].get_text(strip=True)
            value = cells[1].get_text(strip=True)
            if label and value and len(label) < 60:
                # Don't overwrite: first occurrence on Mero Lagani's page is the canonical one.
                out.setdefault(label, value)
    return out
