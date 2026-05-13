"""
Nepali transaction-cost model for NEPSE secondary-market equities (cash market).

Numbers as of 2026; verify with your broker before relying on them. SEBON publishes
fee schedules periodically and they do change. CGT rates are set by the Finance Act.

References:
- SEBON regulatory levy: 0.015% on transaction value (both buy and sell).
- Broker commission: tiered on transaction value (NEPSE policy).
- DP charge: Rs 25 fixed per scrip, charged on sell side only.
- Capital gains tax (individuals): 7.5% on profit, short-term (<365 days holding).
                                   5% on profit, long-term (>=365 days holding).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone


def broker_commission_rate(value: float) -> float:
    if value <= 50_000:
        return 0.00360
    if value <= 500_000:
        return 0.00330
    if value <= 2_000_000:
        return 0.00310
    if value <= 10_000_000:
        return 0.00270
    return 0.00240


SEBON_LEVY_RATE = 0.00015
DP_CHARGE = 25.0
CGT_SHORT_TERM = 0.075
CGT_LONG_TERM = 0.050


@dataclass
class BuyCosts:
    transaction_value: float
    broker_commission: float
    sebon_levy: float
    total: float

    @property
    def effective_cost(self) -> float:
        return self.transaction_value + self.total


@dataclass
class SellCosts:
    transaction_value: float
    broker_commission: float
    sebon_levy: float
    dp_charge: float
    capital_gains_tax: float
    cgt_rate: float
    profit_before_cgt: float
    total: float

    @property
    def net_proceeds(self) -> float:
        return self.transaction_value - self.total


def buy_costs(qty: float, price: float) -> BuyCosts:
    value = qty * price
    bc = round(value * broker_commission_rate(value), 2)
    sl = round(value * SEBON_LEVY_RATE, 2)
    return BuyCosts(
        transaction_value=round(value, 2),
        broker_commission=bc,
        sebon_levy=sl,
        total=round(bc + sl, 2),
    )


def sell_costs(
    qty: float,
    sell_price: float,
    cost_basis_per_share: float,
    buy_date: datetime | date | None,
    as_of: datetime | None = None,
) -> SellCosts:
    value = qty * sell_price
    bc = round(value * broker_commission_rate(value), 2)
    sl = round(value * SEBON_LEVY_RATE, 2)

    # Profit before CGT uses the effective cost (buy price + buy fees per share).
    # For simplicity we treat cost_basis_per_share as already including buy fees if caller
    # passes effective per-share cost; otherwise it's the raw buy price.
    profit = max(0.0, (sell_price - cost_basis_per_share) * qty)

    long_term = False
    if buy_date is not None:
        as_of_date = (as_of or datetime.now(timezone.utc)).date() if hasattr(buy_date, "year") else buy_date
        if isinstance(buy_date, datetime):
            bd = buy_date.date()
        else:
            bd = buy_date
        ad = as_of_date if isinstance(as_of_date, date) else (as_of or datetime.now(timezone.utc)).date()
        long_term = (ad - bd).days >= 365

    cgt_rate = CGT_LONG_TERM if long_term else CGT_SHORT_TERM
    cgt = round(profit * cgt_rate, 2)

    total = round(bc + sl + DP_CHARGE + cgt, 2)
    return SellCosts(
        transaction_value=round(value, 2),
        broker_commission=bc,
        sebon_levy=sl,
        dp_charge=DP_CHARGE,
        capital_gains_tax=cgt,
        cgt_rate=cgt_rate,
        profit_before_cgt=round(profit, 2),
        total=total,
    )
