"""Probe news + policy data sources."""
from __future__ import annotations

import io
import re
import sys

import httpx
from bs4 import BeautifulSoup

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def section(s: str) -> None:
    print("\n" + "=" * 60 + f"\n  {s}\n" + "=" * 60)


def probe(c: httpx.Client, name: str, url: str) -> str | None:
    try:
        r = c.get(url)
    except Exception as e:  # noqa: BLE001
        print(f"[{name}] EXC: {e}")
        return None
    print(f"[{name}]  HTTP {r.status_code}  bytes={len(r.content)}  url={url}")
    return r.text if r.status_code == 200 else None


def main() -> int:
    with httpx.Client(timeout=20.0, headers=HEADERS, follow_redirects=True) as c:
        section("Sharesansar news listings")
        for name, url in [
            ("category/news", "https://www.sharesansar.com/category/news"),
            ("category/latest", "https://www.sharesansar.com/category/latest"),
            ("news-feed", "https://www.sharesansar.com/news-feed"),
        ]:
            html = probe(c, name, url)
            if html:
                soup = BeautifulSoup(html, "html.parser")
                # Common patterns for news links
                articles = soup.select("a[href*='/newsdetail/']") or soup.select("article a")
                print(f"  candidate article links: {len(articles)}")
                for a in articles[:3]:
                    title = a.get_text(strip=True) or "(no text)"
                    href = a.get("href", "")
                    print(f"    {title[:80]}  ->  {href[:80]}")

        section("Mero Lagani news")
        html = probe(c, "News.aspx", "https://merolagani.com/News.aspx")
        if html:
            soup = BeautifulSoup(html, "html.parser")
            items = soup.select("a[href*='/NewsDetail']")
            print(f"  candidate news items: {len(items)}")
            for a in items[:3]:
                title = a.get_text(strip=True)
                if title:
                    print(f"    {title[:80]}")

        section("NRB monetary policy + statistics")
        for name, url in [
            ("NRB home", "https://www.nrb.org.np/"),
            ("NRB monetary policy", "https://www.nrb.org.np/category/monetary-policy/"),
            ("NRB statistics", "https://www.nrb.org.np/category/statistics/"),
        ]:
            html = probe(c, name, url)
            if html:
                # Look for tables, downloadable files, or rate values
                soup = BeautifulSoup(html, "html.parser")
                tables = soup.find_all("table")
                pdfs = soup.select("a[href$='.pdf']")
                xls = soup.select("a[href$='.xls'], a[href$='.xlsx']")
                print(f"  tables={len(tables)}, pdfs={len(pdfs)}, xls={len(xls)}")
                # Extract first few rates-looking numbers
                rate_hits = re.findall(r"(?:Policy Rate|Bank Rate|CRR|SLR)[^\n]{0,80}", html, re.IGNORECASE)
                for h in rate_hits[:3]:
                    print(f"    rate-like: {h[:120]}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
