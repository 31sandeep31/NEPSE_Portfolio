"""
Rule-based signal engine. Pure functions, no I/O beyond the DB query for sector medians.

Each rule takes a `RuleContext` and returns `Signal | None`. The engine runs all rules
and returns the resulting list along with summary P&L numbers.

Important: these are heuristic signals based on fundamentals + price levels. They are
NOT price predictions. Each Signal includes the raw numbers it used, so the UI can
display 'why' instead of treating the output as a black box.
"""
from __future__ import annotations

import statistics
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

from pydantic import BaseModel
from sqlmodel import Session, select

from .db.models import Holding, Stock, StockFundamentals
from .scheduler import is_market_open


# ---------- output models ----------

class Signal(BaseModel):
    rule: str
    level: str  # info | hold | watch | consider_sell | target_hit | loss_alert
    title: str
    explanation: str
    data: dict


class HoldingAnalysis(BaseModel):
    holding_id: int
    symbol: str
    qty: float
    buy_price: float
    cost_basis: float
    current_price: float | None
    current_value: float | None
    unrealized_pl: float | None
    unrealized_pl_pct: float | None
    target_pct: float | None
    signals: list[Signal]


class PortfolioAnalysis(BaseModel):
    username: str
    as_of: datetime
    market_open: bool | None
    last_price_update: datetime | None
    total_cost_basis: float
    total_current_value: float | None
    total_unrealized_pl: float | None
    total_unrealized_pl_pct: float | None
    holdings: list[HoldingAnalysis]
    warnings: list[str]


# ---------- rule context ----------

@dataclass
class RuleContext:
    holding: Holding
    stock: Stock
    fund: StockFundamentals | None
    sector_pe_median: float | None
    sector_pb_median: float | None
    unrealized_pl_pct: float | None


# ---------- helpers ----------

def _pb_ratio(ltp: float | None, book_value: float | None) -> float | None:
    if ltp is None or not book_value:
        return None
    return ltp / book_value


def _pct_near(value: float, target: float) -> float:
    """How close `value` is to `target`, as a fraction of target. 0.0 = equal."""
    if target == 0:
        return float("inf")
    return abs(value - target) / abs(target)


# ---------- rules ----------

def rule_target_hit(ctx: RuleContext) -> Signal | None:
    if ctx.holding.target_pct is None or ctx.unrealized_pl_pct is None:
        return None
    if ctx.unrealized_pl_pct < ctx.holding.target_pct:
        return None
    return Signal(
        rule="target_hit",
        level="target_hit",
        title="Profit target reached",
        explanation=(
            f"You set a target of {ctx.holding.target_pct:.1f}%. "
            f"Your position is up {ctx.unrealized_pl_pct:.1f}% — consider booking profit."
        ),
        data={
            "target_pct": ctx.holding.target_pct,
            "current_pl_pct": round(ctx.unrealized_pl_pct, 2),
        },
    )


def rule_near_52w_high(ctx: RuleContext) -> Signal | None:
    if ctx.fund is None or ctx.fund.week_52_high is None or ctx.stock.ltp is None:
        return None
    nearness = _pct_near(ctx.stock.ltp, ctx.fund.week_52_high)
    if nearness > 0.03 or ctx.stock.ltp < ctx.fund.week_52_high * 0.97:
        return None
    return Signal(
        rule="near_52w_high",
        level="watch",
        title="Near 52-week high",
        explanation=(
            f"Currently {ctx.stock.ltp:.2f}, within 3% of the 52-week high "
            f"of {ctx.fund.week_52_high:.2f}. Stocks near recent highs often "
            f"consolidate or pull back — a common moment to take partial profit."
        ),
        data={"ltp": ctx.stock.ltp, "week_52_high": ctx.fund.week_52_high},
    )


def rule_near_52w_low(ctx: RuleContext) -> Signal | None:
    if ctx.fund is None or ctx.fund.week_52_low is None or ctx.stock.ltp is None:
        return None
    if _pct_near(ctx.stock.ltp, ctx.fund.week_52_low) > 0.03 or ctx.stock.ltp > ctx.fund.week_52_low * 1.03:
        return None
    return Signal(
        rule="near_52w_low",
        level="watch",
        title="Near 52-week low",
        explanation=(
            f"Currently {ctx.stock.ltp:.2f}, within 3% of the 52-week low "
            f"of {ctx.fund.week_52_low:.2f}. Could be value, could be continuing decline — "
            f"check fundamentals and recent news before adding."
        ),
        data={"ltp": ctx.stock.ltp, "week_52_low": ctx.fund.week_52_low},
    )


def rule_below_moving_avg(ctx: RuleContext) -> Signal | None:
    f, p = ctx.fund, ctx.stock.ltp
    if f is None or p is None or f.avg_120_day is None or f.avg_180_day is None:
        return None
    if p >= f.avg_120_day or p >= f.avg_180_day:
        return None
    return Signal(
        rule="below_moving_avg",
        level="watch",
        title="Below moving averages",
        explanation=(
            f"Price ({p:.2f}) is below both the 120-day ({f.avg_120_day:.2f}) "
            f"and 180-day ({f.avg_180_day:.2f}) averages — short-term downtrend. "
            f"Wait for price to reclaim averages before adding."
        ),
        data={"ltp": p, "avg_120": f.avg_120_day, "avg_180": f.avg_180_day},
    )


def rule_overvalued_vs_sector(ctx: RuleContext) -> Signal | None:
    if ctx.fund is None or ctx.fund.pe_ratio is None or ctx.stock.ltp is None:
        return None
    if ctx.sector_pe_median is None:
        return None
    pe = ctx.fund.pe_ratio
    pb = _pb_ratio(ctx.stock.ltp, ctx.fund.book_value)
    pe_premium = pe / ctx.sector_pe_median
    if pe_premium < 1.5:
        return None
    pb_part = ""
    if pb is not None and ctx.sector_pb_median:
        pb_premium = pb / ctx.sector_pb_median
        if pb_premium < 1.3:
            return None
        pb_part = f" P/B of {pb:.2f} is also above sector median ({ctx.sector_pb_median:.2f})."
    return Signal(
        rule="overvalued_vs_sector",
        level="consider_sell",
        title="Valuation stretched vs sector",
        explanation=(
            f"P/E ratio of {pe:.2f} is {pe_premium:.1f}x the {ctx.fund.sector or 'sector'} "
            f"median ({ctx.sector_pe_median:.2f}).{pb_part} If the business hasn't fundamentally "
            f"improved, the premium may not last — consider whether to trim."
        ),
        data={
            "pe": pe,
            "sector_pe_median": ctx.sector_pe_median,
            "pb": pb,
            "sector_pb_median": ctx.sector_pb_median,
        },
    )


def rule_strong_dividend(ctx: RuleContext) -> Signal | None:
    if ctx.fund is None:
        return None
    y = ctx.fund.yield_pct
    d = ctx.fund.dividend_pct
    if y is None or y < 8.0 or d is None or d <= 0:
        return None
    return Signal(
        rule="strong_dividend",
        level="hold",
        title="Strong dividend",
        explanation=(
            f"Pays {d:.1f}% dividend with current yield of {y:.2f}% — solid income. "
            f"Usually worth holding through short-term volatility."
        ),
        data={"yield_pct": y, "dividend_pct": d},
    )


def rule_loss_with_downtrend(ctx: RuleContext) -> Signal | None:
    if ctx.unrealized_pl_pct is None or ctx.unrealized_pl_pct > -15:
        return None
    f, p = ctx.fund, ctx.stock.ltp
    if f is None or p is None or f.avg_120_day is None:
        return None
    if p >= f.avg_120_day:
        return None
    return Signal(
        rule="loss_with_downtrend",
        level="loss_alert",
        title="Loss + downtrend",
        explanation=(
            f"Down {ctx.unrealized_pl_pct:.1f}% on this position, and price is below the "
            f"120-day average. Decide your max loss tolerance — averaging down only makes "
            f"sense if fundamentals still support the thesis."
        ),
        data={"pl_pct": round(ctx.unrealized_pl_pct, 2), "ltp": p, "avg_120": f.avg_120_day},
    )


RULES: list[Callable[[RuleContext], Signal | None]] = [
    rule_target_hit,
    rule_overvalued_vs_sector,
    rule_near_52w_high,
    rule_near_52w_low,
    rule_below_moving_avg,
    rule_strong_dividend,
    rule_loss_with_downtrend,
]


# ---------- engine ----------

def analyze_portfolio(s: Session, username: str) -> PortfolioAnalysis:
    holdings = s.exec(select(Holding).where(Holding.username == username)).all()

    sector_medians = _build_sector_medians(s)

    warnings: list[str] = []
    market_open: bool | None = is_market_open()
    last_price_update: datetime | None = None

    holding_analyses: list[HoldingAnalysis] = []
    total_cost = 0.0
    total_value: float | None = 0.0
    total_value_known = True

    for h in holdings:
        stock = s.get(Stock, h.symbol)
        fund = s.get(StockFundamentals, h.symbol)
        cost_basis = h.qty * h.buy_price
        total_cost += cost_basis

        current_price = stock.ltp if stock else None
        if stock and stock.updated_at:
            if last_price_update is None or stock.updated_at > last_price_update:
                last_price_update = stock.updated_at

        if current_price is None:
            current_value = None
            unrealized_pl = None
            unrealized_pl_pct = None
            total_value_known = False
        else:
            current_value = current_price * h.qty
            unrealized_pl = current_value - cost_basis
            unrealized_pl_pct = (unrealized_pl / cost_basis * 100.0) if cost_basis > 0 else None
            if total_value is not None:
                total_value += current_value

        sector_pe = sector_medians["pe"].get(fund.sector) if fund and fund.sector else None
        sector_pb = sector_medians["pb"].get(fund.sector) if fund and fund.sector else None

        if fund is None:
            warnings.append(
                f"{h.symbol}: fundamentals not yet fetched — only price-based signals available."
            )

        ctx = RuleContext(
            holding=h,
            stock=stock or Stock(symbol=h.symbol, updated_at=datetime.now(timezone.utc)),
            fund=fund,
            sector_pe_median=sector_pe,
            sector_pb_median=sector_pb,
            unrealized_pl_pct=unrealized_pl_pct,
        )

        signals = [sig for rule in RULES if (sig := rule(ctx)) is not None]

        holding_analyses.append(
            HoldingAnalysis(
                holding_id=h.id,
                symbol=h.symbol,
                qty=h.qty,
                buy_price=h.buy_price,
                cost_basis=round(cost_basis, 2),
                current_price=current_price,
                current_value=round(current_value, 2) if current_value is not None else None,
                unrealized_pl=round(unrealized_pl, 2) if unrealized_pl is not None else None,
                unrealized_pl_pct=round(unrealized_pl_pct, 2) if unrealized_pl_pct is not None else None,
                target_pct=h.target_pct,
                signals=signals,
            )
        )

    if not total_value_known:
        total_value = None
        total_pl = None
        total_pl_pct = None
    else:
        total_pl = total_value - total_cost
        total_pl_pct = (total_pl / total_cost * 100.0) if total_cost > 0 else None

    return PortfolioAnalysis(
        username=username,
        as_of=datetime.now(timezone.utc),
        market_open=market_open,
        last_price_update=last_price_update,
        total_cost_basis=round(total_cost, 2),
        total_current_value=round(total_value, 2) if total_value is not None else None,
        total_unrealized_pl=round(total_pl, 2) if total_pl is not None else None,
        total_unrealized_pl_pct=round(total_pl_pct, 2) if total_pl_pct is not None else None,
        holdings=holding_analyses,
        warnings=warnings,
    )


# ---------- sector medians ----------

# Sector comparison only fires if we have at least this many comparable stocks.
_MIN_SECTOR_SAMPLE = 3


def _build_sector_medians(s: Session) -> dict[str, dict[str, float]]:
    funds = s.exec(select(StockFundamentals)).all()

    by_sector_pe: dict[str, list[float]] = {}
    by_sector_pb: dict[str, list[float]] = {}
    for f in funds:
        if not f.sector:
            continue
        if f.pe_ratio is not None and f.pe_ratio > 0:
            by_sector_pe.setdefault(f.sector, []).append(f.pe_ratio)
        stock = s.get(Stock, f.symbol)
        if stock and stock.ltp and f.book_value and f.book_value > 0:
            by_sector_pb.setdefault(f.sector, []).append(stock.ltp / f.book_value)

    return {
        "pe": {sec: statistics.median(vs) for sec, vs in by_sector_pe.items() if len(vs) >= _MIN_SECTOR_SAMPLE},
        "pb": {sec: statistics.median(vs) for sec, vs in by_sector_pb.items() if len(vs) >= _MIN_SECTOR_SAMPLE},
    }
