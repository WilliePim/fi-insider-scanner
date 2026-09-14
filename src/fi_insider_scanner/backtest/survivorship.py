"""Survivorship (ADR-032): copertura e scenari per gli eventi senza rendimento osservabile.

Scenari di eccesso a 126 giorni assegnati agli eventi non risolti:
- S_minus100: titolo a -100%        -> eccesso = -1 - r_bench
- S_minus50:  titolo a -50%         -> eccesso = -0,5 - r_bench
- S0:         eccesso nullo         -> 0
- S_plus:     uscita per acquisizione -> +15%
- S_draw:     estrazione dalla distribuzione osservata (seed fisso)
r_bench = rendimento medio del benchmark sugli eventi osservati dello stesso insieme.

Break-even: quota p* dei non risolti che, a -100%, porta a zero la media osservata.
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
    """`observed`/`added`: colonne value_col, issuer_key, month."""
    both = pd.concat([observed[[value_col, "issuer_key", "month"]], added[[value_col, "issuer_key", "month"]]], ignore_index=True)
    return summarize(both[value_col], both["issuer_key"], both["month"], draws, seed, min_groups)


def acquired_likely(rows: pd.DataFrame, lookback_days: int) -> set[str]:
    """Emittenti con >= 2 persone che vendono fuori mercato allo stesso prezzo nei giorni prima dell'ultima riga.

    `rows`: righe correnti del registro (issuer_key, trade_date, txn_kind, venue_class, price, name_key).
    Indizio di offerta pubblica accettata, non prova.
    """
    last = rows.groupby("issuer_key")["trade_date"].max()
    sales = rows[rows["txn_kind"].eq("disp_sale") & rows["venue_class"].eq("off_venue") & (rows["price"].fillna(0) > 0)]
    sales = sales.assign(last=sales["issuer_key"].map(last))
    sales = sales[sales["trade_date"] >= sales["last"] - pd.Timedelta(days=lookback_days)]
    counts = sales.groupby(["issuer_key", "price"])["name_key"].nunique()
    return set(counts[counts >= 2].index.get_level_values(0))
