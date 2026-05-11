from __future__ import annotations

import logging
from datetime import datetime, timezone

from bs4 import BeautifulSoup

from ._http import client
from ._parse import to_float, to_int
from .types import LivePrice, LiveSnapshot

log = logging.getLogger(__name__)

URL = "https://www.sharesansar.com/live-trading"

# Column index → field on LivePrice. Sharesansar's table is fixed-width.
# Verified columns: S.No | Symbol | LTP | Point Change | % Change | Open | High | Low | Qty | Prev. Close
_COL_SYMBOL = 1
_COL_LTP = 2
_COL_POINT_CHANGE = 3
_COL_PCT_CHANGE = 4
_COL_OPEN = 5
_COL_HIGH = 6
_COL_LOW = 7
_COL_QTY = 8
_COL_PREV_CLOSE = 9


class ScrapeError(RuntimeError):
    pass


def fetch_live_prices() -> LiveSnapshot:
    with client() as c:
        r = c.get(URL)
    if r.status_code != 200:
        raise ScrapeError(f"sharesansar live-trading returned HTTP {r.status_code}")

    soup = BeautifulSoup(r.text, "html.parser")
    table = soup.find("table", id="headFixed") or soup.find("table")
    if table is None:
        raise ScrapeError("live-trading: no table on page")

    rows = table.find_all("tr")
    if len(rows) < 2:
        raise ScrapeError("live-trading: table has no data rows")

    market_open = _is_market_open(soup)

    prices: list[LivePrice] = []
    for tr in rows[1:]:
        cells = [c.get_text(strip=True) for c in tr.find_all(["td", "th"])]
        if len(cells) < _COL_LTP + 1:
            continue
        symbol = cells[_COL_SYMBOL]
        ltp = to_float(cells[_COL_LTP])
        if not symbol or ltp is None:
            continue
        prices.append(
            LivePrice(
                symbol=symbol,
                ltp=ltp,
                point_change=_safe(cells, _COL_POINT_CHANGE, to_float),
                pct_change=_safe(cells, _COL_PCT_CHANGE, to_float),
                open=_safe(cells, _COL_OPEN, to_float),
                high=_safe(cells, _COL_HIGH, to_float),
                low=_safe(cells, _COL_LOW, to_float),
                qty=_safe(cells, _COL_QTY, to_int),
                prev_close=_safe(cells, _COL_PREV_CLOSE, to_float),
            )
        )

    if not prices:
        raise ScrapeError("live-trading: parsed 0 rows")

    log.info("live-trading: %d rows, market_open=%s", len(prices), market_open)
    return LiveSnapshot(
        fetched_at=datetime.now(timezone.utc),
        market_open=market_open,
        prices=prices,
    )


def _safe(cells: list[str], idx: int, fn):
    if idx >= len(cells):
        return None
    return fn(cells[idx])


def _is_market_open(soup: BeautifulSoup) -> bool:
    # Sharesansar shows a "Market Open" / "Market Closed" badge in the header.
    text = soup.get_text(" ", strip=True).lower()
    if "market open" in text:
        return True
    if "market close" in text:
        return False
    return False
