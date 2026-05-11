"""
Round 2 fundamentals probe.

Strategy:
  A. Mero Lagani CompanyDetail.aspx — known to have a clean fundamentals table.
  B. Dump raw HTML around 'EPS' on Sharesansar page to understand structure.
"""
from __future__ import annotations

import io
import re
import sys

import httpx
from bs4 import BeautifulSoup

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

SYMBOL = "NABIL"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}


def section(title: str) -> None:
    print("\n" + "=" * 60 + f"\n  {title}\n" + "=" * 60)


def merolagani(symbol: str) -> dict[str, str]:
    section("A. Mero Lagani CompanyDetail")
    url = f"https://merolagani.com/CompanyDetail.aspx?symbol={symbol}"
    with httpx.Client(timeout=15.0, headers=HEADERS, follow_redirects=True) as c:
        r = c.get(url)
    print(f"HTTP {r.status_code}  bytes={len(r.content)}")
    if r.status_code != 200:
        return {}

    soup = BeautifulSoup(r.text, "html.parser")

    # Mero Lagani uses a definition-list-ish structure: <th>Label</th><td>Value</td>
    out: dict[str, str] = {}
    for tr in soup.find_all("tr"):
        cells = tr.find_all(["th", "td"])
        if len(cells) >= 2:
            label = cells[0].get_text(strip=True)
            value = cells[1].get_text(strip=True)
            if label and value and len(label) < 60:
                out[label] = value

    # Also try the company-info panel which uses divs
    for row in soup.select(".company-info .row, .accordion-inner .row"):
        cells = row.find_all(["div", "span"])
        if len(cells) >= 2:
            label = cells[0].get_text(strip=True)
            value = cells[1].get_text(strip=True)
            if label and value:
                out.setdefault(label, value)

    interesting = {
        k: v for k, v in out.items()
        if any(kw in k.lower() for kw in
               ["eps", "p/e", "pe ratio", "book", "market cap", "ltp",
                "52", "dividend", "sector", "yield", "high", "low",
                "average", "listed", "paid", "share"])
    }
    print(f"total rows extracted: {len(out)}, interesting: {len(interesting)}")
    for k, v in interesting.items():
        print(f"  {k:40s} = {v}")
    return interesting


def sharesansar_inspect(symbol: str) -> None:
    section("B. Sharesansar HTML around 'EPS'")
    url = f"https://www.sharesansar.com/company/{symbol}"
    with httpx.Client(timeout=15.0, headers=HEADERS, follow_redirects=True) as c:
        r = c.get(url)
    html = r.text
    print(f"HTTP {r.status_code}  bytes={len(html)}")

    # Find all occurrences of 'EPS' as a standalone word and show surrounding 200 chars
    for m in re.finditer(r"\bEPS\b", html):
        start = max(0, m.start() - 80)
        end = min(len(html), m.end() + 200)
        snippet = re.sub(r"\s+", " ", html[start:end])
        print(f"\n  @{m.start()}: ...{snippet}...")
        if m.start() > 50000:  # don't dump endless menu items
            break

    # Also list IDs and classes that look like data containers
    soup = BeautifulSoup(html, "html.parser")
    print("\n  elements with id containing 'company' or 'essential' or 'financial':")
    for el in soup.find_all(attrs={"id": re.compile(r"(company|essential|financial|info)", re.I)}):
        print(f"    <{el.name} id='{el.get('id')}' class='{el.get('class')}'> children={len(list(el.children))}")


def main() -> int:
    ml = merolagani(SYMBOL)
    sharesansar_inspect(SYMBOL)

    section("VERDICT")
    if ml:
        print(f"  Mero Lagani: extracted {len(ml)} fundamentals fields — VIABLE")
    else:
        print(f"  Mero Lagani: FAILED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
