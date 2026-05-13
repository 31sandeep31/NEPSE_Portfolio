"""
Curated NEPSE policy reference data.

This is **manually maintained** because the underlying numbers change rarely (1-2x per
year via NRB's monetary policy review, once per year via the budget). Auto-scraping
the policy rate PDFs is fragile and high-risk for misinformation. Keeping this as
explicit, dated data is safer.

Update this file when NRB publishes a new monetary policy or when the budget changes
relevant tax rates.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PolicyRate:
    name: str  # e.g. "Policy Rate (Repo)"
    value: float
    unit: str  # e.g. "%"
    effective_date: str  # ISO date
    source: str  # human reference
    note: str = ""


# Source: NRB Monetary Policy for FY 2082-83 (2025-26), unified rates corridor
# Verify against https://www.nrb.org.np/category/monetary-policy/ when updating.
CURRENT_POLICY_RATES: list[PolicyRate] = [
    PolicyRate(
        name="Policy Rate (Repo)",
        value=5.0,
        unit="%",
        effective_date="2025-07-26",
        source="NRB Monetary Policy 2082-83",
        note="The mid-point of NRB's interest-rate corridor. Lower = easier money, often supportive of equity prices.",
    ),
    PolicyRate(
        name="Bank Rate",
        value=6.5,
        unit="%",
        effective_date="2025-07-26",
        source="NRB Monetary Policy 2082-83",
        note="Upper bound — rate at which NRB lends to banks via standing liquidity facility.",
    ),
    PolicyRate(
        name="Deposit Collection Rate",
        value=3.0,
        unit="%",
        effective_date="2025-07-26",
        source="NRB Monetary Policy 2082-83",
        note="Lower bound — rate NRB pays to absorb excess liquidity from banks.",
    ),
    PolicyRate(
        name="CRR (Cash Reserve Ratio)",
        value=4.0,
        unit="%",
        effective_date="2025-07-26",
        source="NRB Monetary Policy 2082-83",
        note="Share of deposits banks must hold with NRB as cash. Higher = less money to lend.",
    ),
    PolicyRate(
        name="SLR (Statutory Liquidity Ratio)",
        value=12.0,
        unit="%",
        effective_date="2025-07-26",
        source="NRB Monetary Policy 2082-83",
        note="Share of deposits banks must hold in cash + gold + approved securities.",
    ),
]


CURRENT_FISCAL_HIGHLIGHTS: list[dict] = [
    {
        "name": "Capital Gains Tax — Individual (Short-term, <365 days)",
        "value": 7.5,
        "unit": "%",
        "effective_date": "2025-07-17",
        "source": "Finance Act 2082-83",
        "note": "Levied on profit when you sell shares held less than one year.",
    },
    {
        "name": "Capital Gains Tax — Individual (Long-term, >=365 days)",
        "value": 5.0,
        "unit": "%",
        "effective_date": "2025-07-17",
        "source": "Finance Act 2082-83",
        "note": "Lower rate rewards longer holding periods.",
    },
    {
        "name": "Dividend Tax (Resident Individual)",
        "value": 5.0,
        "unit": "%",
        "effective_date": "2025-07-17",
        "source": "Finance Act 2082-83",
        "note": "Withheld at source — dividends arrive net of this tax.",
    },
    {
        "name": "SEBON Regulatory Levy",
        "value": 0.015,
        "unit": "%",
        "effective_date": "2024-07-17",
        "source": "SEBON levy schedule",
        "note": "Charged on every transaction (buy and sell) by SEBON.",
    },
]


EXTERNAL_LINKS = [
    {
        "title": "NRB — Monetary Policy publications",
        "url": "https://www.nrb.org.np/category/monetary-policy/",
        "blurb": "Annual monetary policy + mid-year review PDFs.",
    },
    {
        "title": "NRB — Macroeconomic indicators",
        "url": "https://www.nrb.org.np/",
        "blurb": "Forex rates, banking deposit/lending aggregates updated periodically.",
    },
    {
        "title": "Ministry of Finance — Budget speeches",
        "url": "https://mof.gov.np/en/archive-documents/budget-15.html",
        "blurb": "Annual budget speech + Finance Act with tax changes.",
    },
    {
        "title": "SEBON — Regulatory notices",
        "url": "https://www.sebon.gov.np/",
        "blurb": "Securities regulator — notices, rule changes, fee schedules.",
    },
    {
        "title": "NEPSE — Notices and circulars",
        "url": "https://www.nepalstock.com/",
        "blurb": "Trading hours changes, circuit-breaker decisions, listed-company actions.",
    },
]
