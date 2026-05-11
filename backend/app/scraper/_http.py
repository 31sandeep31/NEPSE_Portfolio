from __future__ import annotations

import httpx

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

DEFAULT_TIMEOUT = httpx.Timeout(15.0, connect=10.0)


def client() -> httpx.Client:
    return httpx.Client(
        timeout=DEFAULT_TIMEOUT,
        headers={"User-Agent": USER_AGENT},
        follow_redirects=True,
        http2=False,
    )
