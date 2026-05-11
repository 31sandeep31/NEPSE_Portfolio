from __future__ import annotations

import os
from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine

DB_PATH = Path(os.environ.get("NEPSE_DB", Path(__file__).resolve().parents[2] / "data" / "app.db"))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

_engine = create_engine(
    f"sqlite:///{DB_PATH}",
    echo=False,
    connect_args={"check_same_thread": False},
)


def engine():
    return _engine


def init_db() -> None:
    from . import models  # noqa: F401  ensures tables register on SQLModel.metadata
    SQLModel.metadata.create_all(_engine)


def session() -> Session:
    # expire_on_commit=False: we never need lazy reload after commit, and disabling it
    # lets routes safely read attribute values after the `with session()` block closes.
    return Session(_engine, expire_on_commit=False)
