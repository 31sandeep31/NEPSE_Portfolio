"""Probe NEPSE historical OHLC sources. Goal: find a working endpoint to bootstrap ~60 days of history."""
from __future__ import annotations

import io
import sys
from datetime import date, timedelta

import httpx
from bs4 import BeautifulSoup

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def banner(s: str) -> None:
    print("\n" + "=" * 60 + "\n  " + s + "\n" + "=" * 60)


def probe_sharesansar_archive(d: date) -> None:
    banner(f"Sharesansar today-share-price archive @ {d}")
    url = f"https://www.sharesansar.com/today-share-price?date={d.isoformat()}"
    with httpx.Client(timeout=15.0, headers=HEADERS, follow_redirects=True) as c:
        r = c.get(url)
    print(f"  HTTP {r.status_code}  bytes={len(r.content)}")
    soup = BeautifulSoup(r.text, "html.parser")
    tables = soup.find_all("table")
    print(f"  tables found: {len(tables)}")
    for i, t in enumerate(tables[:3]):
        rows = t.find_all("tr")
        if len(rows) < 2:
            continue
        header = [c.get_text(strip=True) for c in rows[0].find_all(["th", "td"])]
        sample = [c.get_text(strip=True) for c in rows[1].find_all(["th", "td"])]
        print(f"  table[{i}]: {len(rows)} rows, header={header[:10]}, sample={sample[:10]}")


def probe_merolagani_company_history() -> None:
    banner("Mero Lagani CompanyDetail (looking for embedded history table)")
    url = "https://merolagani.com/CompanyDetail.aspx?symbol=NABIL"
    with httpx.Client(timeout=15.0, headers=HEADERS, follow_redirects=True) as c:
        r = c.get(url)
    print(f"  HTTP {r.status_code}  bytes={len(r.content)}")
    soup = BeautifulSoup(r.text, "html.parser")
    # Look for tables with date-looking first column.
    for i, t in enumerate(soup.find_all("table")):
        rows = t.find_all("tr")
        if len(rows) < 3:
            continue
        first_data = [c.get_text(strip=True) for c in rows[1].find_all(["td", "th"])]
        looks_like_date = first_data and any(
            ch.isdigit() and "-" in first_data[0] or "/" in first_data[0] for ch in first_data[0][:10]
        )
        if looks_like_date or "date" in " ".join(
            c.get_text(strip=True).lower() for c in rows[0].find_all(["th", "td"])
        ):
            print(f"  candidate table[{i}]: {len(rows)} rows")
            header = [c.get_text(strip=True) for c in rows[0].find_all(["th", "td"])]
            print(f"    header: {header}")
            for r2 in rows[1:4]:
                print(f"    row: {[c.get_text(strip=True) for c in r2.find_all(['td','th'])]}")


def main() -> int:
    # Try a few recent weekdays for Sharesansar archive
    today = date.today()
    for delta in (1, 2, 3, 7, 14, 30):
        target = today - timedelta(days=delta)
        # Skip Fri/Sat (NEPSE closed)
        if target.weekday() in (4, 5):
            continue
        probe_sharesansar_archive(target)
        break  # one is enough to see the structure
    probe_merolagani_company_history()
    return 0


if __name__ == "__main__":
    sys.exit(main())
