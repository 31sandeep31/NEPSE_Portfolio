"""Probe for the real Sharesansar historical endpoint."""
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


def main() -> int:
    with httpx.Client(timeout=15.0, headers=HEADERS, follow_redirects=True) as c:
        # 1. Look at the today-share-price page source for AJAX hints.
        r = c.get("https://www.sharesansar.com/today-share-price")
        html = r.text
        # Find any AJAX URLs referenced.
        ajax_urls = set(re.findall(r"['\"](/[^'\"\s]+ajax[^'\"\s]*)['\"]", html, re.IGNORECASE))
        for u in sorted(ajax_urls):
            print(f"  ajax-like: {u}")
        # Find any URLs with "history" or "today" or "data"
        for kw in ("history", "today-share", "data"):
            urls = set(re.findall(rf"['\"]([^'\"\s]*{kw}[^'\"\s]*)['\"]", html, re.IGNORECASE))
            for u in sorted(urls):
                if u.startswith("/") or u.startswith("http"):
                    print(f"  '{kw}': {u}")
        # CSRF token
        m = re.search(r'name="_token"\s+value="([^"]+)"', html)
        print(f"\n  csrf token present: {bool(m)}  token={m.group(1)[:20] + '...' if m else None}")

        # 2. Try the AJAX endpoint with a date param via POST
        if m:
            for ajax_path in ("/ajaxtodayshareprice", "/ajax/today-share-price", "/ajaxhistory", "/ajaxhistoryprice"):
                try:
                    r2 = c.post(
                        f"https://www.sharesansar.com{ajax_path}",
                        data={"_token": m.group(1), "date": "2026-04-15"},
                        headers={"X-Requested-With": "XMLHttpRequest"},
                    )
                    print(f"\n  POST {ajax_path}  HTTP {r2.status_code}  bytes={len(r2.content)}")
                    if r2.status_code == 200 and len(r2.content) > 500:
                        soup = BeautifulSoup(r2.text, "html.parser")
                        rows = soup.find_all("tr")
                        print(f"    rows: {len(rows)}")
                        for tr in rows[:2]:
                            cells = [c.get_text(strip=True) for c in tr.find_all(["td", "th"])]
                            print(f"    {cells[:10]}")
                except Exception as e:  # noqa: BLE001
                    print(f"  POST {ajax_path} EXC: {e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
