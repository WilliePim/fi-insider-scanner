"""Prezzi raw ricostruiti e verifica di un ticker contro i prezzi del registro (ADR-024, ADR-025).

Yahoo restituisce OHLC aggiustati per split (non per dividendi con auto_adjust=False).
prezzo raw alla data d = prezzo Yahoo * prodotto dei rapporti di split con data > d.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


def split_factor_after(history: pd.DataFrame, dates: pd.Series) -> np.ndarray:
    splits = history["Stock Splits"] if "Stock Splits" in history else pd.Series(dtype=float)
    splits = splits[splits.fillna(0) > 0]
    if splits.empty:
        return np.ones(len(dates))
    s_dates = splits.index.to_numpy()
    ratios = splits.to_numpy(dtype=float)
    # prodotto cumulato dalla fine: factor[k] = prodotto dei rapporti con indice >= k
    suffix = np.append(np.cumprod(ratios[::-1])[::-1], 1.0)
    pos = s_dates.searchsorted(pd.to_datetime(dates).to_numpy(), side="right")
    return suffix[pos]


def raw_close(history: pd.DataFrame, dates: pd.Series) -> np.ndarray:
    idx = history.index.to_numpy()
    d = pd.to_datetime(dates).to_numpy()
    pos = idx.searchsorted(d, side="right") - 1
    out = np.full(len(d), np.nan)
    ok = pos >= 0
    out[ok] = history["Close"].to_numpy(dtype=float)[pos[ok]]
    return out * split_factor_after(history, dates)


@dataclass(frozen=True)
class Verification:
    verified: bool | None
    n_checked: int
    share_in_range: float | None
    median_ratio: float | None
    reason: str


def verify_against_register(history: pd.DataFrame, trades: pd.DataFrame, tolerance: float, min_rows: int, min_share: float) -> Verification:
    """`trades`: colonne trade_date, price (valuta del listino). Controlla price in [Low, High] raw ±tol."""
    if history is None or history.empty:
        return Verification(False, 0, None, None, "NO_HISTORY")
    t = trades.dropna(subset=["trade_date", "price"])
    t = t[(t["price"] > 0) & t["trade_date"].isin(history.index)]
    n = len(t)
    if n < min_rows:
        return Verification(None, n, None, None, "TOO_FEW_ROWS")
    hist = history.loc[t["trade_date"]]
    factor = split_factor_after(history, t["trade_date"])
    low = hist["Low"].to_numpy(dtype=float) * factor
    high = hist["High"].to_numpy(dtype=float) * factor
    close = hist["Close"].to_numpy(dtype=float) * factor
    price = t["price"].to_numpy(dtype=float)
    inside = (price >= low * (1 - tolerance)) & (price <= high * (1 + tolerance))
    share = float(inside.mean())
    ratio = float(np.nanmedian(price / np.where(close > 0, close, np.nan)))
    if share >= min_share:
        return Verification(True, n, share, ratio, "OK")
    if ratio > 0 and (50 <= ratio <= 200 or 1 / 200 <= ratio <= 1 / 50):
        return Verification(False, n, share, ratio, "SCALE_SUSPECT")
    return Verification(False, n, share, ratio, "PRICE_MISMATCH")
