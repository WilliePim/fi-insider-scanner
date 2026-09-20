"""Event statistics (ADR-030). Every formula is spelled out.

- iid t = mean / (sd / sqrt(n)), sample sd (n-1)
- CR1 (the mean as a regression on a constant, cluster g): V = G/(G-1) * sum_g (sum_{i in g} e_i)^2 / n^2,
  with e_i = x_i - mean; t = mean / sqrt(V). None when G < min_groups.
- two-way (issuer, month): V = V_1 + V_2 - V_12, V_12 over the intersection clusters; None when V <= 0.
- percentile bootstrap 95% over the events, fixed seed.
- MDE (alpha 5% two-sided, power 80%) = (1.96 + 0.8416) * sd / sqrt(n).
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd

Z_ALPHA = 1.959964
Z_POWER = 0.841621


def t_iid(x) -> float | None:
    a = np.asarray(x, dtype=float)
    a = a[~np.isnan(a)]
    if len(a) < 2:
        return None
    sd = a.std(ddof=1)
    if sd == 0:
        return None
    return float(a.mean() / (sd / math.sqrt(len(a))))


def _cr1_var(e: np.ndarray, groups: np.ndarray) -> tuple[float, int]:
    n = len(e)
    sums = pd.Series(e).groupby(groups).sum().to_numpy()
    g = len(sums)
    if g < 2:
        return float("nan"), g
    return float(g / (g - 1) * np.sum(sums**2) / n**2), g


def t_cluster(x, groups, min_groups: int = 10) -> float | None:
    a = np.asarray(x, dtype=float)
    grp = np.asarray(groups)
    keep = ~np.isnan(a)
    a, grp = a[keep], grp[keep]
    if len(a) < 2:
        return None
    e = a - a.mean()
    var, g = _cr1_var(e, grp)
    if g < min_groups or not var > 0:
        return None
    return float(a.mean() / math.sqrt(var))


def t_two_way(x, groups1, groups2, min_groups: int = 10) -> float | None:
    a = np.asarray(x, dtype=float)
    g1, g2 = np.asarray(groups1), np.asarray(groups2)
    keep = ~np.isnan(a)
    a, g1, g2 = a[keep], g1[keep], g2[keep]
    if len(a) < 2:
        return None
    e = a - a.mean()
    v1, n1 = _cr1_var(e, g1)
    v2, n2 = _cr1_var(e, g2)
    v12, _ = _cr1_var(e, np.array([f"{p}|{q}" for p, q in zip(g1, g2, strict=True)]))
    if min(n1, n2) < min_groups:
        return None
    var = v1 + v2 - v12
    if not var > 0:
        return None
    return float(a.mean() / math.sqrt(var))


def bootstrap_ci(x, draws: int, seed: int) -> tuple[float | None, float | None]:
    a = np.asarray(x, dtype=float)
    a = a[~np.isnan(a)]
    if len(a) < 2:
        return None, None
    rng = np.random.default_rng(seed)
    means = a[rng.integers(0, len(a), size=(draws, len(a)))].mean(axis=1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def mde(sd: float | None, n: int) -> float | None:
    if sd is None or n < 2 or not sd > 0:
        return None
    return float((Z_ALPHA + Z_POWER) * sd / math.sqrt(n))


def calendar_time_t(monthly: pd.DataFrame) -> tuple[float | None, int]:
    """`monthly`: columns month, excess (one event's excess return in that month).

    Equal-weight portfolio per calendar month, then an iid t on the monthly series.
    """
    if monthly.empty:
        return None, 0
    series = monthly.groupby("month")["excess"].mean()
    return t_iid(series.to_numpy()), len(series)


@dataclass
class Summary:
    n: int
    mean: float | None
    median: float | None
    sd: float | None
    share_positive: float | None
    t_iid: float | None
    t_cr1_issuer: float | None
    t_cr1_month: float | None
    t_two_way: float | None
    ci_low: float | None
    ci_high: float | None
    mde: float | None
    n_issuers: int
    n_months: int

    def as_dict(self) -> dict:
        return asdict(self)


def summarize(values, issuers, months, draws: int = 1000, seed: int = 12345, min_groups: int = 10) -> Summary:
    a = np.asarray(values, dtype=float)
    keep = ~np.isnan(a)
    a = a[keep]
    iss = np.asarray(issuers)[keep]
    mon = np.asarray(months)[keep]
    n = len(a)
    sd = float(a.std(ddof=1)) if n >= 2 else None
    lo, hi = bootstrap_ci(a, draws, seed)
    return Summary(
        n=n,
        mean=float(a.mean()) if n else None,
        median=float(np.median(a)) if n else None,
        sd=sd,
        share_positive=float((a > 0).mean()) if n else None,
        t_iid=t_iid(a),
        t_cr1_issuer=t_cluster(a, iss, min_groups),
        t_cr1_month=t_cluster(a, mon, min_groups),
        t_two_way=t_two_way(a, iss, mon, min_groups),
        ci_low=lo,
        ci_high=hi,
        mde=mde(sd, n),
        n_issuers=len(set(iss)),
        n_months=len(set(mon)),
    )
