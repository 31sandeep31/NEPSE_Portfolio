from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from .db import init_db, session
from .db.repo import held_symbols, upsert_fundamentals, upsert_live_snapshot
from .scraper import FundamentalsError, ScrapeError, fetch_fundamentals, fetch_live_prices

log = logging.getLogger(__name__)

# NEPSE trades Sun–Thu 11:00–15:00 NPT (UTC+5:45).
# In UTC that's roughly 05:15 – 09:15 on those days.
LIVE_HOURS_UTC = "5-9"
LIVE_MINUTES_UTC = "*/30 * * * *"  # not used; we use IntervalTrigger instead
LIVE_DAYS = "sun,mon,tue,wed,thu"

LIVE_REFRESH_SECONDS = 30
FUNDAMENTALS_PER_RUN_DELAY = 1.5  # seconds between requests — be polite to merolagani


def _job_refresh_live() -> None:
    if not _within_market_hours_utc(datetime.now(timezone.utc)):
        log.debug("live: outside market hours, skipping")
        return
    try:
        snap = fetch_live_prices()
    except ScrapeError as e:
        log.warning("live: scrape failed: %s", e)
        return
    with session() as s:
        n = upsert_live_snapshot(s, snap)
    log.info("live: wrote %d rows", n)


def _job_refresh_fundamentals_for_held() -> None:
    with session() as s:
        symbols = held_symbols(s)
    if not symbols:
        log.info("fundamentals: no held symbols, nothing to refresh")
        return
    log.info("fundamentals: refreshing %d held symbols", len(symbols))
    for sym in symbols:
        try:
            f = fetch_fundamentals(sym)
        except FundamentalsError as e:
            log.warning("fundamentals[%s] failed: %s", sym, e)
            continue
        with session() as s:
            upsert_fundamentals(s, f)
        time.sleep(FUNDAMENTALS_PER_RUN_DELAY)


def is_market_open(now: datetime | None = None) -> bool:
    # NPT = UTC+5:45 → 11:00 NPT = 05:15 UTC, 15:00 NPT = 09:15 UTC.
    # NEPSE trades Sun–Thu. Python weekday(): Mon=0..Sun=6.
    n = now or datetime.now(timezone.utc)
    if n.weekday() == 4 or n.weekday() == 5:  # Fri, Sat
        return False
    minute_of_day = n.hour * 60 + n.minute
    return 5 * 60 + 15 <= minute_of_day <= 9 * 60 + 15


_within_market_hours_utc = is_market_open  # backcompat alias


def build_scheduler() -> BackgroundScheduler:
    init_db()
    sched = BackgroundScheduler(timezone="UTC")
    sched.add_job(
        _job_refresh_live,
        IntervalTrigger(seconds=LIVE_REFRESH_SECONDS),
        id="refresh_live",
        max_instances=1,
        coalesce=True,
    )
    sched.add_job(
        _job_refresh_fundamentals_for_held,
        CronTrigger(day_of_week="sun,mon,tue,wed,thu", hour=10, minute=30, timezone="UTC"),
        id="refresh_fundamentals_held",
        max_instances=1,
        coalesce=True,
    )
    return sched


def run_once() -> None:
    """One-shot CLI: run each job synchronously and exit. For manual testing."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    init_db()
    log.info("--- run_once: refresh_live ---")
    _job_refresh_live()
    log.info("--- run_once: refresh_fundamentals_held ---")
    _job_refresh_fundamentals_for_held()


if __name__ == "__main__":
    run_once()
