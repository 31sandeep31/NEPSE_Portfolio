from __future__ import annotations

import re

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..auth import assert_username_allowed
from ..db import session
from ..db.repo import ensure_user
from ..rate_limit import limit_writes

router = APIRouter(prefix="/users", tags=["users"])

USERNAME_RX = re.compile(r"^[a-zA-Z0-9_.-]{2,40}$")


class UserIn(BaseModel):
    username: str


@router.post("", dependencies=[Depends(limit_writes)])
def claim_username(body: UserIn):
    """Idempotent: create the user if missing, return current state either way.

    No password, no secrets. Anyone who knows the username can read/write that portfolio.
    """
    if not USERNAME_RX.match(body.username):
        raise HTTPException(
            status_code=400,
            detail="username must be 2-40 chars, letters/digits/underscore/dot/hyphen only",
        )
    assert_username_allowed(body.username)
    with session() as s:
        u = ensure_user(s, body.username.strip())
    return {"username": u.username, "created_at": u.created_at.isoformat()}
