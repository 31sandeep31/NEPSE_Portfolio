"""Find the exact CSS structure of Sharesansar news articles + NRB rate table."""
from __future__ import annotations

import io
import re
import sys

import httpx
from bs4 import BeautifulSoup

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def section(s: str) -> None:
    print("\n" + "=" * 60 + f"\n  {s}\n" + "=" * 60)


def main() -> int:
    with httpx.Client(timeout=20.0, headers=HEADERS, follow_redirects=True) as c:
        section("Sharesansar /category/news structure")
        r = c.get("https://www.sharesansar.com/category/news")
        soup = BeautifulSoup(r.text, "html.parser")
        # Articles tend to be in .featured-news-list, .news-list, .article, h3, or h4 wrappers
        for selector in [
            "h4 a[href*='/newsdetail/']",
            "h3 a[href*='/newsdetail/']",
            "h2 a[href*='/newsdetail/']",
            ".featured-news-list a[href*='/newsdetail/']",
            ".news-list a[href*='/newsdetail/']",
            "article a[href*='/newsdetail/']",
            ".margin-bottom-15 a[href*='/newsdetail/']",
        ]:
            hits = soup.select(selector)
            if hits:
                print(f"\n  selector: {selector}  -> {len(hits)} hits")
                for a in hits[:5]:
                    parent = a.find_parent(class_=re.compile(r"news|article|featured", re.I)) or a.parent
                    date_node = (parent.find(class_=re.compile(r"date|time|pub", re.I))
                                 if parent else None) or parent.find("span")
                    print(f"    title: {a.get_text(strip=True)[:80]}")
                    print(f"    href:  {a.get('href')}")
                    if date_node:
                        print(f"    date?: {date_node.get_text(strip=True)[:30]}")
                break

        section("NRB home page tables")
        r = c.get("https://www.nrb.org.np/")
        soup = BeautifulSoup(r.text, "html.parser")
        for i, t in enumerate(soup.find_all("table")):
            rows = t.find_all("tr")
            print(f"\n  table[{i}]: {len(rows)} rows")
            for row in rows[:8]:
                cells = [c.get_text(" ", strip=True) for c in row.find_all(["td", "th"])]
                print(f"    {cells}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
