from __future__ import annotations

import logging
import re
from datetime import date

import httpx
from bs4 import BeautifulSoup

from ._http import USER_AGENT
from ._parse import to_float, to_int
from .types import DailyBar

log = logging.getLogger(__name__)

PAGE_URL = "https://www.sharesansar.com/today-share-price"
AJAX_URL = "https://www.sharesansar.com/ajaxtodayshareprice"

# Verified columns: S.No | Symbol | Conf | Open | High | Low | Close | LTP | Close-LTP | Close-LTP %
# "Conf." appears to be a turnover-in-millions figure, not share volume — we drop it for now.
_COL_SYMBOL = 1
_COL_CONF = 2
_COL_OPEN = 3
_COL_HIGH = 4
_COL_LOW = 5
_COL_CLOSE = 6


class HistoryError(RuntimeError):
    pass


class HistoryClient:
    """Holds the CSRF token + session cookies needed to POST to the AJAX endpoint.

    Sharesansar requires:
      - GET the page once to capture the _token CSRF and laravel_session cookie.
      - POST the date along with the same token; the cookie carries the session.

    Tokens appear to rotate per-session; we refresh on 419 (CSRF mismatch).
    """

    def __init__(self) -> None:
        self._client = httpx.Client(
            timeout=20.0,
            headers={
                "User-Agent": USER_AGENT,
                "Referer": PAGE_URL,
                "X-Requested-With": "XMLHttpRequest",
            },
            follow_redirects=True,
            http2=False,
        )
        self._token: str | None = None

    def __enter__(self) -> "HistoryClient":
        self._refresh_token()
        return self

    def __exit__(self, *exc) -> None:
        self._client.close()

    def _refresh_token(self) -> None:
        r = self._client.get(PAGE_URL)
        m = re.search(r'name="_token"\s+value="([^"]+)"', r.text)
        if not m:
            raise HistoryError("could not extract CSRF token from today-share-price")
        self._token = m.group(1)

    def fetch_bars(self, d: date) -> list[DailyBar]:
        if self._token is None:
            self._refresh_token()
        r = self._client.post(
            AJAX_URL,
            data={"_token": self._token, "date": d.isoformat()},
        )
        if r.status_code == 419:  # CSRF mismatch — refresh + retry once
            self._refresh_token()
            r = self._client.post(
                AJAX_URL, data={"_token": self._token, "date": d.isoformat()}
            )
        if r.status_code != 200:
            raise HistoryError(f"ajaxtodayshareprice HTTP {r.status_code} for {d}")

        return _parse_bars(r.text, d)


def _parse_bars(html: str, d: date) -> list[DailyBar]:
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table") or soup
    rows = table.find_all("tr")
    if len(rows) < 2:
        return []

    bars: list[DailyBar] = []
    iso = d.isoformat()
    for tr in rows[1:]:
        cells = [c.get_text(strip=True) for c in tr.find_all(["td", "th"])]
        if len(cells) <= _COL_CLOSE:
            continue
        sym = cells[_COL_SYMBOL]
        close = to_float(cells[_COL_CLOSE])
        if not sym or close is None:
            continue
        bars.append(
            DailyBar(
                symbol=sym,
                date=iso,
                open=to_float(cells[_COL_OPEN]),
                high=to_float(cells[_COL_HIGH]),
                low=to_float(cells[_COL_LOW]),
                close=close,
                volume=to_int(cells[_COL_CONF]),  # placeholder: turnover/conf
            )
        )
    return bars


def fetch_daily_bars(d: date) -> list[DailyBar]:
    """Single-shot fetch. For bulk backfill, use `HistoryClient` directly to reuse the session."""
    with HistoryClient() as h:
        bars = h.fetch_bars(d)
    log.info("history: %d bars for %s", len(bars), d.isoformat())
    return bars
