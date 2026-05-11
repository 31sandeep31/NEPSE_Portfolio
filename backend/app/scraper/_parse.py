from __future__ import annotations

import re


def to_float(s: str | None) -> float | None:
    if s is None:
        return None
    cleaned = s.replace(",", "").strip()
    if not cleaned or cleaned in {"-", "N/A", "NA"}:
        return None
    m = re.search(r"-?\d+(?:\.\d+)?", cleaned)
    if not m:
        return None
    try:
        return float(m.group(0))
    except ValueError:
        return None


def to_int(s: str | None) -> int | None:
    f = to_float(s)
    return None if f is None else int(f)


def split_parenthetical(s: str) -> tuple[str, str | None]:
    """'33.34(FY:082-083, Q:3)' -> ('33.34', 'FY:082-083, Q:3')."""
    m = re.match(r"^\s*([^\(]+?)\s*\(([^)]+)\)\s*$", s)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return s.strip(), None


def split_high_low(s: str) -> tuple[float | None, float | None]:
    """'562.00-471.00' -> (562.0, 471.0)."""
    parts = re.split(r"\s*-\s*", s.replace(",", ""))
    if len(parts) != 2:
        return None, None
    return to_float(parts[0]), to_float(parts[1])
