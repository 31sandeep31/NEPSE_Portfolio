"""
Test: can we pull fundamentals (P/E, EPS, book value, 52-week H/L) for a single stock?

Probes Sharesansar's company page + likely AJAX endpoints.
"""
from __future__ import annotations

import io
import re
import sys

import httpx
from bs4 import BeautifulSoup

# Force UTF-8 stdout on Windows so we don't choke on ‪ etc.
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

SYMBOL = "NABIL"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": f"https://www.sharesansar.com/company/{SYMBOL}",
}


def probe(client: httpx.Client, name: str, url: str) -> str | None:
    try:
        r = client.get(url)
    except Exception as e:  # noqa: BLE001
        print(f"\n[{name}]  {url}\n  EXC: {type(e).__name__}: {e}")
        return None
    print(f"\n[{name}]  {url}\n  HTTP {r.status_code}  bytes={len(r.content)}  ct={r.headers.get('content-type','?')[:40]}")
    if r.status_code != 200 or len(r.content) < 200:
        return None
    return r.text


def find_label_value(html: str, labels: list[str]) -> dict[str, str]:
    """Find label-value pairs in tables by looking for td/th containing the label."""
    soup = BeautifulSoup(html, "html.parser")
    out: dict[str, str] = {}
    for label in labels:
        # Find any cell whose stripped text equals or starts with label
        rx = re.compile(rf"^\s*{re.escape(label)}\s*:?\s*$", re.IGNORECASE)
        cell = soup.find(["td", "th"], string=rx)
        if cell:
            nxt = cell.find_next_sibling(["td", "th"])
            if nxt:
                out[label] = nxt.get_text(strip=True)
                continue
        # Fallback: label appears in text with value next to it
        rx2 = re.compile(re.escape(label), re.IGNORECASE)
        node = soup.find(string=rx2)
        if node and node.parent:
            sib = node.parent.find_next(["td", "span"])
            if sib:
                out[label] = sib.get_text(strip=True)[:60]
    return out


def main() -> int:
    with httpx.Client(timeout=15.0, headers=HEADERS, follow_redirects=True) as c:
        # 1. Main company page
        main_html = probe(c, "main", f"https://www.sharesansar.com/company/{SYMBOL}")

        # 2. Likely AJAX endpoints (guessed from common Sharesansar patterns)
        candidates = [
            ("essentials", f"https://www.sharesansar.com/company-essentials/{SYMBOL}"),
            ("financials", f"https://www.sharesansar.com/company-financials/{SYMBOL}"),
            ("trading",    f"https://www.sharesansar.com/company-trading/{SYMBOL}"),
            ("price-history", f"https://www.sharesansar.com/company/price-history?symbol={SYMBOL}"),
        ]
        ajax_results: dict[str, str | None] = {}
        for name, url in candidates:
            ajax_results[name] = probe(c, name, url)

    # Try to extract fundamentals from each successful fetch
    labels = [
        "EPS", "P/E Ratio", "Book Value", "Market Capitalization", "Market Cap",
        "52 Weeks High", "52 Weeks Low", "Listed Shares", "Sector",
        "180 Days Average", "120 Days Average", "Dividend",
    ]

    for name, html in [("main", main_html), *ajax_results.items()]:
        if not html:
            continue
        found = find_label_value(html, labels)
        if found:
            print(f"\n=== fundamentals from [{name}] ===")
            for k, v in found.items():
                print(f"  {k:30s} = {v}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
