"""Routine (ADR-021).

Interpretazione di "numero acquisti 12 mesi ÷ taglia mediana": un piano si riconosce da
molti mesi con acquisti E importi mensili quasi uguali.
- mesi con acquisti nei 365 giorni prima di T >= 6
- dispersione = mediana(|x - mediana|) / mediana dei valori mensili in SEK <= 0,25
Label CMP (stesso mese di calendario nei 3 blocchi di 365 giorni) calcolata per ogni persona,
solo informativa.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .openmarket import base_purchase


@dataclass(frozen=True)
class RoutineMetrics:
    person_key: str
    n_buy_days: int
    n_buy_months: int
    median_month_value_sek: float | None
    dispersion: float | None
    is_routine: bool
    cmp_label: str


def cmp_label(trade_dates: pd.Series, as_of: pd.Timestamp) -> str:
    days = (as_of.normalize() - trade_dates.dt.normalize()).dt.days
    keep = (days > 0) & (days // 365 < 3)
    if not keep.any():
        return "novel"
    blocks = (days[keep] // 365).astype(int)
    months = trade_dates[keep].dt.month
    active = set(blocks)
    if len(active) < 3:
        return "sparse"
    per_block = [set(months[blocks == b]) for b in range(3)]
    return "routine" if per_block[0] & per_block[1] & per_block[2] else "opportunistic"


def routine_metrics(v: pd.DataFrame, person_key: str, as_of: pd.Timestamp, rc: dict) -> RoutineMetrics:
    own = v[base_purchase(v) & v["person_key"].eq(person_key)]
    start = as_of.normalize() - pd.Timedelta(days=rc["lookback_days"])
    recent = own[(own["trade_date"] >= start) & (own["trade_date"] < as_of.normalize())]
    n_days = int(recent["trade_date"].nunique())
    monthly = recent.groupby(recent["trade_date"].dt.to_period("M"))["value_sek"].sum(min_count=1).dropna()
    n_months = int(recent["trade_date"].dt.to_period("M").nunique())
    median = float(monthly.median()) if not monthly.empty else None
    dispersion = None
    if median and median > 0:
        dispersion = float(np.median(np.abs(monthly.to_numpy() - median)) / median)
    is_routine = n_months >= rc["min_months"] and dispersion is not None and dispersion <= rc["max_dispersion"]
    return RoutineMetrics(
        person_key=person_key,
        n_buy_days=n_days,
        n_buy_months=n_months,
        median_month_value_sek=median,
        dispersion=dispersion,
        is_routine=bool(is_routine),
        cmp_label=cmp_label(own["trade_date"], as_of),
    )
