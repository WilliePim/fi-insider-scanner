"""Survivorship (ADR-032): coverage and scenarios for the events with no observable return.

126-day excess scenarios assigned to the unresolved events:
- S_minus100: the stock at -100%          -> excess = -1 - r_bench
- S_minus50:  the stock at -50%           -> excess = -0.5 - r_bench
- S0:         no excess                   -> 0
- S_plus:     exit through an acquisition -> +15%
- S_draw:     a draw from the observed distribution (fixed seed)
r_bench = the mean benchmark return over the observed events of the same set.

Break-even: the share p* of the unresolved events that, at -100%, brings the observed mean to zero.
  (n_obs * m - p * n_u * (1 + r_bench)) / (n_obs + p * n_u) = 0  =>  p* = n_obs * m / (n_u * (1 + r_bench))
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .stats import Summary, summarize

SCENARIOS = ("S_minus100", "S_minus50", "S0", "S_plus", "S_draw")


def scenario_values(name: str, n: int, r_bench_mean: float, s_plus: float, observed: np.ndarray, seed: int) -> np.ndarray:
    if name == "S_minus100":
        return np.full(n, -1.0 - r_bench_mean)
    if name == "S_minus50":
        return np.full(n, -0.5 - r_bench_mean)
    if name == "S0":
        return np.zeros(n)
    if name == "S_plus":
        return np.full(n, s_plus)
    if name == "S_draw":
        rng = np.random.default_rng(seed)
        return rng.choice(observed, size=n, replace=True) if len(observed) else np.zeros(n)
    raise ValueError(name)


def break_even_share(mean: float, n_obs: int, n_unresolved: int, r_bench_mean: float) -> float | None:
    if n_unresolved <= 0 or mean is None or mean <= 0:
        return None
    return float(n_obs * mean / (n_unresolved * (1.0 + r_bench_mean)))


def pooled(observed: pd.DataFrame, added: pd.DataFrame, value_col: str, draws: int, seed: int, min_groups: int) -> Summary:
    """`observed`/`added`: columns value_col, issuer_key, month."""
    both = pd.concat([observed[[value_col, "issuer_key", "month"]], added[[value_col, "issuer_key", "month"]]], ignore_index=True)
    return summarize(both[value_col], both["issuer_key"], both["month"], draws, seed, min_groups)


def acquired_likely(rows: pd.DataFrame, lookback_days: int) -> set[str]:
    """Issuers with at least 2 persons selling off-venue at the same price in the days before the issuer's last row.

    `rows`: the register's current rows (issuer_key, trade_date, txn_kind, venue_class, price, name_key).
    A hint of an accepted tender offer, not a proof.
    """
    last = rows.groupby("issuer_key")["trade_date"].max()
    sales = rows[rows["txn_kind"].eq("disp_sale") & rows["venue_class"].eq("off_venue") & (rows["price"].fillna(0) > 0)]
    sales = sales.assign(last=sales["issuer_key"].map(last))
    sales = sales[sales["trade_date"] >= sales["last"] - pd.Timedelta(days=lookback_days)]
    counts = sales.groupby(["issuer_key", "price"])["name_key"].nunique()
    return set(counts[counts >= 2].index.get_level_values(0))
