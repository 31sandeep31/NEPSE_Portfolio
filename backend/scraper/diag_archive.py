"""Diagnose: does Sharesansar's archive URL actually return different data per date?"""
from __future__ import annotations

import io
import sys

import httpx
from bs4 import BeautifulSoup

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def extract_nabil_row(html: str) -> list[str] | None:
    soup = BeautifulSoup(html, "html.parser")
    for table in soup.find_all("table"):
        for tr in table.find_all("tr"):
            cells = [c.get_text(strip=True) for c in tr.find_all(["td", "th"])]
            if len(cells) >= 7 and cells[1] == "NABIL":
                return cells
    return None


def main() -> int:
    with httpx.Client(timeout=15.0, headers=HEADERS, follow_redirects=True) as c:
        for date_str in ("2026-05-12", "2026-04-15", "2026-03-15", "2026-02-15"):
            url = f"https://www.sharesansar.com/today-share-price?date={date_str}"
            r = c.get(url)
            row = extract_nabil_row(r.text)
            # Also check final URL after any redirect
            print(f"date={date_str}  HTTP {r.status_code}  final_url={r.url}")
            print(f"  NABIL row: {row}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
