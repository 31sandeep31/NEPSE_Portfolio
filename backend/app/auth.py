from __future__ import annotations

from fastapi import HTTPException

from .config import ALLOWED_USERNAMES

# Lower-cased set, or None to mean "no restriction".
_ALLOWED_SET: set[str] | None = (
    {u.strip().lower() for u in ALLOWED_USERNAMES if u.strip()} if ALLOWED_USERNAMES else None
)


def is_allowlist_enabled() -> bool:
    return _ALLOWED_SET is not None


def assert_username_allowed(username: str) -> None:
    if _ALLOWED_SET is None:
        return
    if username.strip().lower() not in _ALLOWED_SET:
        raise HTTPException(
            status_code=403,
            detail="This username is not on the allowlist. Ask the owner of this app to add it.",
        )


def require_allowed_username(username: str) -> str:
    """FastAPI dependency form — use with `Depends(require_allowed_username)` on
    routes that take a `username` path param."""
    assert_username_allowed(username)
    return username
