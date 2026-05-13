from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from datetime import timedelta

import json

from .db import MacroSnap, NewsItem, init_db, session
from .db.models import NewsItem as NewsItemModel
from .db.repo import (
    all_known_symbols,
    history_min_max_date,
    upsert_daily_bars,
    upsert_fundamentals,
    upsert_live_snapshot,
)
from .scraper import (
    FundamentalsError,
    HistoryError,
    ScrapeError,
    fetch_daily_bars,
    fetch_fundamentals,
    fetch_live_prices,
)
from .scraper.history import HistoryClient
from .scraper.macro import MacroError, fetch_macro_snapshot
from .scraper.news import NewsError, detect_tags, fetch_news_listing

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


HISTORY_BACKFILL_DAYS = 60
HISTORY_PER_REQUEST_DELAY = 1.0


def _job_refresh_history_today() -> None:
    """Daily: scrape today's archive (NEPSE doesn't trade Fri/Sat)."""
    today = datetime.now(timezone.utc).date()
    if today.weekday() in (4, 5):
        return
    try:
        bars = fetch_daily_bars(today)
    except HistoryError as e:
        log.warning("history-today failed: %s", e)
        return
    if not bars:
        log.info("history-today: empty (holiday or before close)")
        return
    with session() as s:
        n = upsert_daily_bars(s, bars)
    log.info("history-today: wrote %d bars", n)


def _bootstrap_history_if_needed() -> None:
    """One-time backfill of recent days. Skips if history is already populated.

    Uses a single HistoryClient session to reuse the CSRF token + cookies across requests.
    """
    with session() as s:
        oldest, newest = history_min_max_date(s)
    today = datetime.now(timezone.utc).date()
    if newest:
        return
    log.info("history bootstrap: filling last %d days", HISTORY_BACKFILL_DAYS)
    with HistoryClient() as h:
        for delta in range(1, HISTORY_BACKFILL_DAYS + 1):
            d = today - timedelta(days=delta)
            if d.weekday() in (4, 5):
                continue
            try:
                bars = h.fetch_bars(d)
            except HistoryError as e:
                log.warning("history[%s] skipped: %s", d, e)
                continue
            if bars:
                with session() as s:
                    upsert_daily_bars(s, bars)
            time.sleep(HISTORY_PER_REQUEST_DELAY)
    log.info("history bootstrap: done")


def _job_refresh_news() -> None:
    try:
        articles = fetch_news_listing()
    except NewsError as e:
        log.warning("news fetch failed: %s", e)
        return
    if not articles:
        return
    with session() as s:
        # With server-side portfolios removed, we tag every known NEPSE symbol that
        # appears in a headline; the frontend filters by its own localStorage holdings.
        all_syms = set(all_known_symbols(s))
        n_new = 0
        for a in articles:
            existing = s.get(NewsItem, a.slug)
            if existing is not None:
                continue
            tags = detect_tags(a.title, [], all_syms)
            row = NewsItem(
                slug=a.slug,
                title=a.title,
                url=a.url,
                published_date=a.published_date,
                fetched_at=a.fetched_at,
                policy_tags_csv=",".join(tags["policy"]),
                sector_tags_csv=",".join(tags["sectors"]),
                symbols_mentioned_csv=",".join(tags["symbols_mentioned"]),
            )
            s.add(row)
            n_new += 1
        s.commit()
    log.info("news: %d new articles", n_new)


def _job_refresh_macro() -> None:
    try:
        snap = fetch_macro_snapshot()
    except MacroError as e:
        log.warning("macro fetch failed: %s", e)
        return
    if snap.banking is None:
        log.info("macro: banking aggregates not found, skipping save")
        return
    with session() as s:
        existing = s.get(MacroSnap, snap.banking.as_of)
        if existing is None:
            existing = MacroSnap(as_of=snap.banking.as_of, fetched_at=snap.fetched_at)
        existing.fetched_at = snap.fetched_at
        existing.total_deposits_npr_bn = snap.banking.total_deposits_npr_bn
        existing.commercial_banks_deposits_npr_bn = snap.banking.commercial_banks_deposits_npr_bn
        existing.other_bfis_deposits_npr_bn = snap.banking.other_bfis_deposits_npr_bn
        existing.total_lending_npr_bn = snap.banking.total_lending_npr_bn
        existing.commercial_banks_lending_npr_bn = snap.banking.commercial_banks_lending_npr_bn
        existing.other_bfis_lending_npr_bn = snap.banking.other_bfis_lending_npr_bn
        existing.cd_ratio_pct = snap.banking.cd_ratio_pct
        existing.forex_json = json.dumps([f.model_dump() for f in snap.forex])
        s.add(existing)
        s.commit()
    log.info("macro: saved snapshot as_of=%s", snap.banking.as_of)


def _job_refresh_fundamentals_for_all() -> None:
    """Refresh fundamentals for every known NEPSE symbol. ~300 stocks × 1.5s delay
    is ~8 minutes total — fine for a once-daily after-close job."""
    with session() as s:
        symbols = all_known_symbols(s)
    if not symbols:
        log.info("fundamentals: no symbols yet, skipping")
        return
    log.info("fundamentals: refreshing %d symbols", len(symbols))
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
        _job_refresh_fundamentals_for_all,
        CronTrigger(day_of_week="sun,mon,tue,wed,thu", hour=10, minute=30, timezone="UTC"),
        id="refresh_fundamentals_all",
        max_instances=1,
        coalesce=True,
    )
    sched.add_job(
        _job_refresh_history_today,
        # Daily after NEPSE close: 15:00 NPT = 09:15 UTC, run at 09:30 UTC.
        CronTrigger(day_of_week="sun,mon,tue,wed,thu", hour=9, minute=30, timezone="UTC"),
        id="refresh_history_today",
        max_instances=1,
        coalesce=True,
    )
    # Schedule the bootstrap to run once shortly after startup so it doesn't
    # block the FastAPI lifespan.
    sched.add_job(
        _bootstrap_history_if_needed,
        "date",
        run_date=datetime.now(timezone.utc) + timedelta(seconds=5),
        id="history_bootstrap",
        max_instances=1,
        coalesce=True,
    )
    # News every 30 minutes, with an immediate first run shortly after startup.
    sched.add_job(
        _job_refresh_news,
        IntervalTrigger(minutes=30),
        id="refresh_news",
        max_instances=1,
        coalesce=True,
        next_run_time=datetime.now(timezone.utc) + timedelta(seconds=10),
    )
    # Macro daily at 09:30 UTC + immediate first run on startup.
    sched.add_job(
        _job_refresh_macro,
        CronTrigger(hour=9, minute=45, timezone="UTC"),
        id="refresh_macro",
        max_instances=1,
        coalesce=True,
    )
    sched.add_job(
        _job_refresh_macro,
        "date",
        run_date=datetime.now(timezone.utc) + timedelta(seconds=15),
        id="macro_bootstrap",
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
