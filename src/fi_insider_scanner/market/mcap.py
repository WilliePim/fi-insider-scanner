"""Market cap point-in-time (ADR-026).

mcap_SEK(d) = azioni(d) * close_raw(d)
- close_raw(d): ultimo Close Yahoo <= d (split-adjusted) * prodotto degli split con data > d
- azioni(d): ultima osservazione `shares_full` con data <= d - lag, portata a d moltiplicando per
  gli split tra la data dell'osservazione e d. `shares_full` è il totale societario (tutte le classi):
  per un emittente dual class la mcap usa il prezzo della classe acquistata (dichiarato).
Nessun forward-fill oltre la data: se manca un pezzo la mcap è None con il motivo.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .prices import split_factor_after

MAX_PRICE_STALE_DAYS = 10


@dataclass(frozen=True)
class McapPoint:
    mcap_sek: float | None
    shares: float | None
    shares_date: pd.Timestamp | None
    close_raw: float | None
    reason: str


def _splits(history: pd.DataFrame) -> pd.Series:
    if history is None or "Stock Splits" not in history:
        return pd.Series(dtype=float)
    s = history["Stock Splits"]
    return s[s.fillna(0) > 0]


def mcap_at(history: pd.DataFrame | None, shares: pd.Series | None, day: pd.Timestamp, lag_days: int) -> McapPoint:
    day = pd.Timestamp(day).normalize()
    if history is None or history.empty:
        return McapPoint(None, None, None, None, "NO_HISTORY")
    upto = history[history.index <= day]
    if upto.empty or (day - upto.index[-1]).days > MAX_PRICE_STALE_DAYS:
        return McapPoint(None, None, None, None, "NO_PRICE_AT_DATE")
    close_raw = float(upto["Close"].iloc[-1]) * float(split_factor_after(history, pd.Series([day]))[0])
    if shares is None or shares.empty:
        return McapPoint(None, None, None, close_raw, "NO_SHARES")
    avail = shares[shares.index <= day - pd.Timedelta(days=lag_days)]
    if avail.empty:
        return McapPoint(None, None, None, close_raw, "SHARES_NOT_YET_PUBLIC")
    obs_date, obs = avail.index[-1], float(avail.iloc[-1])
    between = _splits(history)
    between = between[(between.index > obs_date) & (between.index <= day)]
    adj = obs * float(np.prod(between.to_numpy(dtype=float))) if not between.empty else obs
    if not adj > 0 or not close_raw > 0:
        return McapPoint(None, adj, obs_date, close_raw, "NON_POSITIVE")
    return McapPoint(adj * close_raw, adj, obs_date, close_raw, "OK")


def mcap_panel(history: pd.DataFrame | None, shares: pd.Series | None, days: pd.DatetimeIndex, lag_days: int) -> np.ndarray:
    """Versione vettoriale di `mcap_at` su molte date (per il pool del matched control)."""
    out = np.full(len(days), np.nan)
    if history is None or history.empty or shares is None or shares.empty or len(days) == 0:
        return out
    d = days.normalize().to_numpy()
    hidx = history.index.to_numpy()
    pos = hidx.searchsorted(d, side="right") - 1
    ok = pos >= 0
    stale = np.zeros(len(d), dtype=bool)
    stale[ok] = (d[ok] - hidx[pos[ok]]) > np.timedelta64(MAX_PRICE_STALE_DAYS, "D")
    ok &= ~stale
    close = np.full(len(d), np.nan)
    close[ok] = history["Close"].to_numpy(dtype=float)[pos[ok]]
    close_raw = close * split_factor_after(history, pd.Series(days))
    sidx = shares.index.to_numpy()
    spos = sidx.searchsorted(d - np.timedelta64(lag_days, "D"), side="right") - 1
    sok = spos >= 0
    obs = np.full(len(d), np.nan)
    obs_date = np.full(len(d), np.datetime64("NaT", "ns"), dtype="datetime64[ns]")
    obs[sok] = shares.to_numpy(dtype=float)[spos[sok]]
    obs_date[sok] = sidx[spos[sok]]
    # split tra osservazione e data: rapporto dei fattori "dopo"
    f_obs = np.ones(len(d))
    f_obs[sok] = split_factor_after(history, pd.Series(pd.to_datetime(obs_date[sok])))
    f_day = split_factor_after(history, pd.Series(days))
    adj = obs * (f_obs / f_day)
    out = adj * close_raw
    out[~(ok & sok)] = np.nan
    return out


def band_label(mcap_usd: float | None, low: float, high: float) -> str | None:
    if mcap_usd is None or not np.isfinite(mcap_usd):
        return None
    if mcap_usd < low:
        return "lt50"
    if mcap_usd < high:
        return "50_300"
    return "gt300"
