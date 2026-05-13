from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db import init_db
from .routes import analysis, movers, news, policy, stocks
from .scheduler import build_scheduler

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    sched = build_scheduler()
    sched.start()
    log.info("scheduler started")
    try:
        yield
    finally:
        sched.shutdown(wait=False)
        log.info("scheduler stopped")


app = FastAPI(title="NEPSE Portfolio API", version="0.1.0", lifespan=lifespan)

_default_origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]
_extra_origins = [o.strip() for o in os.environ.get("ALLOWED_ORIGINS", "").split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_default_origins + _extra_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stocks.router)
app.include_router(analysis.router)
app.include_router(movers.router)
app.include_router(news.router)
app.include_router(policy.router)


@app.get("/health")
def health():
    return {"ok": True}
