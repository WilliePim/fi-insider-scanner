"""Exchange rates into SEK at a date (ADR-026). The native currency is kept; rate and date are stored per row.

yfinance series: `SEK=X` = SEK per USD, `EURSEK=X` = SEK per EUR, and so on.
The rate used is the last one available on or before the date, at most 7 days earlier.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import yf_cache

PAIRS = {
    "USD": "SEK=X",
    "EUR": "EURSEK=X",
    "NOK": "NOKSEK=X",
    "DKK": "DKKSEK=X",
    "GBP": "GBPSEK=X",
    "CHF": "CHFSEK=X",
    "CAD": "CADSEK=X",
}
MAX_STALE_DAYS = 7


class FxOrientationError(ValueError):
    pass


def load_fx(fetch=yf_cache.history) -> dict[str, pd.Series]:
    series: dict[str, pd.Series] = {}
    for ccy, ticker in PAIRS.items():
        hist = fetch(ticker)
        if hist is None or hist.empty:
            continue
        s = hist["Close"].astype(float)
        series[ccy] = s[s > 0].sort_index()
    check_orientation(series)
    return series


def check_orientation(series: dict[str, pd.Series]) -> None:
    usd = series.get("USD")
    if usd is not None and not 4.0 < float(usd.median()) < 20.0:
        raise FxOrientationError(f"SEK=X mediano {usd.median():.3f}: atteso SEK per USD tra 4 e 20")


def _asof(series: pd.Series, dates: pd.Series) -> tuple[np.ndarray, np.ndarray]:
    idx = series.index.to_numpy()
    vals = series.to_numpy()
    d = dates.to_numpy(dtype="datetime64[ns]")
    pos = idx.searchsorted(d, side="right") - 1
    ok = (pos >= 0) & ~pd.isna(dates).to_numpy()
    rate = np.full(len(d), np.nan)
    when = np.full(len(d), np.datetime64("NaT", "ns"), dtype="datetime64[ns]")
    rate[ok] = vals[pos[ok]]
    when[ok] = idx[pos[ok]]
    stale = ok & ((d - when) > np.timedelta64(MAX_STALE_DAYS, "D"))
    rate[stale] = np.nan
    when[stale] = np.datetime64("NaT", "ns")
    return rate, when


def attach_values(df: pd.DataFrame, fx: dict[str, pd.Series]) -> pd.DataFrame:
    """Adds value_native, fx_sek_per_unit, fx_date, value_sek, fx_usdsek, value_usd."""
    out = df.copy()
    native = out["volume"].astype(float) * out["price"].astype(float)
    native = native.where(out["volume_unit"].eq("antal"))
    rate = pd.Series(np.nan, index=out.index)
    when = pd.Series(pd.NaT, index=out.index, dtype="datetime64[ns]")
    sek = out["currency"].eq("SEK")
    rate[sek] = 1.0
    when[sek] = out.loc[sek, "trade_date"]
    for ccy, series in fx.items():
        m = out["currency"].eq(ccy)
        if m.any():
            r, w = _asof(series, out.loc[m, "trade_date"])
            rate[m] = r
            when[m] = w
    usd_rate, _ = _asof(fx["USD"], out["trade_date"]) if "USD" in fx else (np.full(len(out), np.nan), None)
    out["value_native"] = native
    out["fx_sek_per_unit"] = rate
    out["fx_date"] = when
    out["value_sek"] = native * rate
    out["fx_usdsek"] = usd_rate
    out["value_usd"] = out["value_sek"] / out["fx_usdsek"]
    return out
