"""
Runtime config — currently just the username allowlist.

To add or remove allowed usernames: edit ALLOWED_USERNAMES below, save, restart
the backend. Names are case-insensitive (so "Mansangkot" matches "mansangkot").

If ALLOWED_USERNAMES is an empty list, the allowlist is disabled and anyone
can claim any username. Set to None or [] to disable.
"""
from __future__ import annotations

ALLOWED_USERNAMES: list[str] = [
    "Mansangkot",
]
