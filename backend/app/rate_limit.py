from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request


class IPRateLimiter:
    """Tiny in-memory sliding-window limiter. Fine for single-instance deployments."""

    def __init__(self, max_requests: int, window_seconds: float):
        self.max = max_requests
        self.window = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str) -> None:
        now = time.monotonic()
        cutoff = now - self.window
        with self._lock:
            q = self._hits[key]
            while q and q[0] < cutoff:
                q.popleft()
            if len(q) >= self.max:
                raise HTTPException(status_code=429, detail="Too many requests")
            q.append(now)


write_limiter = IPRateLimiter(max_requests=30, window_seconds=60.0)


def limit_writes(request: Request) -> None:
    client = request.client.host if request.client else "unknown"
    write_limiter.check(client)
