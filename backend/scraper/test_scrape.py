"""
NEPSE data feasibility test.

Tries three sources in order:
  1. `nepse` PyPI package (wraps official nepalstock.com API with WASM token).
  2. Sharesansar live trading page (HTML scrape).
  3. Mero Lagani latest market page (HTML scrape).

Goal: confirm we can pull a current price + fundamentals for at least one stock.
"""
from __future__ import annotations

import json
import sys
import traceback
from typing import Any


def banner(name: str) -> None:
    print("\n" + "=" * 60)
    print(f"  {name}")
    print("=" * 60)


def try_nepse_package() -> dict[str, Any] | None:
    banner("Source 1: `nepse` PyPI package")
    try:
        from nepse import Nepse  # type: ignore
    except ImportError:
        print("  [skip] `nepse` package not installed")
        return None

    try:
        client = Nepse()
        client.setTLSVerification(False)
        status = client.isMarketOpen()
        print(f"  market open: {status}")

        prices = client.getPriceVolume()
        sample = prices[:3] if isinstance(prices, list) else prices
        print(f"  sample price/volume rows: {json.dumps(sample, indent=2, default=str)[:500]}")

        if isinstance(prices, list) and prices:
            return {"source": "nepse-pkg", "rows": len(prices), "first": prices[0]}
        return None
    except Exception as e:  # noqa: BLE001
        print(f"  [fail] {type(e).__name__}: {e}")
        traceback.print_exc(limit=2)
        return None


def try_sharesansar() -> dict[str, Any] | None:
    banner("Source 2: Sharesansar live trading")
    try:
        import httpx
        from bs4 import BeautifulSoup
    except ImportError:
        print("  [skip] httpx or bs4 missing")
        return None

    url = "https://www.sharesansar.com/live-trading"
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        with httpx.Client(timeout=15.0, headers=headers, follow_redirects=True) as c:
            r = c.get(url)
            print(f"  HTTP {r.status_code}  bytes={len(r.content)}")
            if r.status_code != 200:
                return None

        soup = BeautifulSoup(r.text, "html.parser")
        table = soup.find("table", id="headFixed") or soup.find("table")
        if not table:
            print("  [fail] no table found on page")
            return None

        rows = table.find_all("tr")
        print(f"  table rows found: {len(rows)}")
        if len(rows) < 2:
            return None

        header_cells = [c.get_text(strip=True) for c in rows[0].find_all(["th", "td"])]
        first_data = [c.get_text(strip=True) for c in rows[1].find_all(["th", "td"])]
        print(f"  headers: {header_cells[:8]}")
        print(f"  first row: {first_data[:8]}")
        return {"source": "sharesansar", "header_count": len(header_cells), "row_count": len(rows) - 1}
    except Exception as e:  # noqa: BLE001
        print(f"  [fail] {type(e).__name__}: {e}")
        traceback.print_exc(limit=2)
        return None


def try_merolagani() -> dict[str, Any] | None:
    banner("Source 3: Mero Lagani latest market")
    try:
        import httpx
        from bs4 import BeautifulSoup
    except ImportError:
        print("  [skip] httpx or bs4 missing")
        return None

    url = "https://merolagani.com/LatestMarket.aspx"
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        with httpx.Client(timeout=15.0, headers=headers, follow_redirects=True) as c:
            r = c.get(url)
            print(f"  HTTP {r.status_code}  bytes={len(r.content)}")
            if r.status_code != 200:
                return None

        soup = BeautifulSoup(r.text, "html.parser")
        tables = soup.find_all("table")
        print(f"  tables found: {len(tables)}")
        if not tables:
            return None

        for i, t in enumerate(tables[:3]):
            rows = t.find_all("tr")
            if len(rows) > 1:
                first_data = [c.get_text(strip=True) for c in rows[1].find_all(["th", "td"])]
                print(f"  table[{i}] first row: {first_data[:6]}")

        return {"source": "merolagani", "table_count": len(tables)}
    except Exception as e:  # noqa: BLE001
        print(f"  [fail] {type(e).__name__}: {e}")
        traceback.print_exc(limit=2)
        return None


def main() -> int:
    results: list[dict[str, Any]] = []
    for fn in (try_nepse_package, try_sharesansar, try_merolagani):
        res = fn()
        if res:
            results.append(res)

    banner("SUMMARY")
    if not results:
        print("  no source returned usable data")
        return 1
    for r in results:
        print(f"  OK  {r['source']}  ->  {r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
