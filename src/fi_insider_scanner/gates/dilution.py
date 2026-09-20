"""Swedish dilution veto (ADR-019), using only information visible at `as_of`.

BLOCKED when any of these holds:

- participation: a subscription or issue instrument traded in [last buy − 5 days, last buy];
- trap: the same, traded in (last buy, +75 days], and already published;
- share count up by at least 25% over about a year.

CAUTION at 10% growth, UNKNOWN without a share series, CLEAR otherwise. The gate passes unless the
verdict is BLOCKED, as in the US test.

Share growth: the last `shares_full` observation dated no later than `as_of` minus the publication lag,
against the baseline closest to a year earlier with a 180-700 day gap, normalised for splits in between.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .structural import issue_rows

BLOCKED, CAUTION, CLEAR, UNKNOWN = "BLOCKED", "CAUTION", "CLEAR", "UNKNOWN"


@dataclass(frozen=True)
class DilutionVerdict:
    verdict: str
    participation: bool
    trap: bool
    growth: float | None


def share_growth(shares: pd.Series | None, splits: pd.Series | None, as_of: pd.Timestamp, dc: dict) -> float | None:
    """Share-count growth over roughly one year, split-normalised, or None when not computable."""
    if shares is None or shares.empty:
        return None
    available = shares[shares.index <= as_of.normalize() - pd.Timedelta(days=dc["shares_lag_days"])]
    if available.empty:
        return None
    last_date, last = available.index[-1], float(available.iloc[-1])
    if last <= 0:
        return None
    gaps = (last_date - available.index).days
    eligible = available[(gaps >= dc["baseline_gap_min_days"]) & (gaps <= dc["baseline_gap_max_days"])]
    if eligible.empty:
        return None
    target = last_date - pd.Timedelta(days=365)
    base_date = eligible.index[int(abs((eligible.index - target).days).argmin())]
    base = float(eligible.loc[base_date])
    if base <= 0:
        return None
    factor = 1.0
    if splits is not None and not splits.empty:
        for ratio in splits[(splits.index > base_date) & (splits.index <= last_date)]:
            factor *= float(ratio)
    return last / (base * factor) - 1.0


def dilution_verdict(
    visible: pd.DataFrame,
    last_buy: pd.Timestamp,
    as_of: pd.Timestamp,
    dc: dict,
    shares: pd.Series | None = None,
    splits: pd.Series | None = None,
) -> DilutionVerdict:
    last_buy = last_buy.normalize()
    start = last_buy - pd.Timedelta(days=dc["participation_days"])
    end = last_buy + pd.Timedelta(days=dc["trap_days"])
    near = visible[visible["trade_date"].between(start, end)]
    issues = issue_rows(near)["trade_date"]
    participation = bool(issues.between(start, last_buy).any())
    trap = bool(((issues > last_buy) & (issues <= end)).any())
    growth = share_growth(shares, splits, as_of, dc)

    if participation or trap or (growth is not None and growth >= dc["growth_blocked"]):
        verdict = BLOCKED
    elif growth is None:
        verdict = UNKNOWN
    elif growth >= dc["growth_caution"]:
        verdict = CAUTION
    else:
        verdict = CLEAR
    return DilutionVerdict(verdict, participation, trap, growth)
