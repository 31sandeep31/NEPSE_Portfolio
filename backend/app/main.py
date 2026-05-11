from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db import init_db
from .routes import analysis, holdings, stocks, users
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

# Frontend is served separately during dev; allow common local ports.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stocks.router)
app.include_router(users.router)
app.include_router(holdings.router)
app.include_router(analysis.router)


@app.get("/health")
def health():
    return {"ok": True}
