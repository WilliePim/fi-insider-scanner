"""Market cap point-in-time (ADR-026).

mcap_SEK(d) = azioni(d) * prezzo(d)
- prezzo(d): per gli eventi, il prezzo di esecuzione in SEK delle righe del registro (reale, alla data);
  altrimenti Close Yahoo <= d * split_factor_after(d) * scale(d) (ADR-025: fattore di riscalamento stimato dal registro)
- azioni(d): ultima osservazione `shares_full` con data <= d - lag, portata a d con gli split intermedi.
  `shares_full` è il totale societario (tutte le classi): per un emittente dual class la mcap usa il prezzo
  della classe acquistata (dichiarato).
Nessun forward-fill oltre la data: se manca un pezzo la mcap è None con il motivo.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .prices import ScaleSegment, scale_at, split_factor_after

MAX_PRICE_STALE_DAYS = 10


@dataclass(frozen=True)
class McapPoint:
    mcap_sek: float | None
    shares: float | None
    shares_date: pd.Timestamp | None
    price_used: float | None
    price_source: str | None
    close_raw_yahoo: float | None
    reason: str


def _splits(history: pd.DataFrame | None) -> pd.Series:
    if history is None or "Stock Splits" not in history:
        return pd.Series(dtype=float)
    s = history["Stock Splits"]
    return s[s.fillna(0) > 0]


def shares_at(history: pd.DataFrame | None, shares: pd.Series | None, day: pd.Timestamp, lag_days: int) -> tuple[float | None, pd.Timestamp | None, str]:
    if shares is None or shares.empty:
        return None, None, "NO_SHARES"
    avail = shares[shares.index <= day - pd.Timedelta(days=lag_days)]
    if avail.empty:
        return None, None, "SHARES_NOT_YET_PUBLIC"
    obs_date, obs = avail.index[-1], float(avail.iloc[-1])
    between = _splits(history)
    between = between[(between.index > obs_date) & (between.index <= day)]
    adj = obs * float(np.prod(between.to_numpy(dtype=float))) if not between.empty else obs
    return adj, obs_date, "OK"


def yahoo_close_raw(history: pd.DataFrame | None, day: pd.Timestamp, segments: list[ScaleSegment] | None = None) -> float | None:
    if history is None or history.empty:
        return None
    upto = history[history.index <= day]
    if upto.empty or (day - upto.index[-1]).days > MAX_PRICE_STALE_DAYS:
        return None
    return float(upto["Close"].iloc[-1]) * float(split_factor_after(history, pd.Series([day]))[0]) * float(scale_at(segments or [], pd.Series([day]))[0])


def mcap_at(
    history: pd.DataFrame | None,
    shares: pd.Series | None,
    day: pd.Timestamp,
    lag_days: int,
    register_price: float | None = None,
    register_price_source: str | None = None,
    segments: list[ScaleSegment] | None = None,
) -> McapPoint:
    day = pd.Timestamp(day).normalize()
    yahoo = yahoo_close_raw(history, day, segments)
    if register_price is not None and register_price > 0:
        price, source = float(register_price), register_price_source or "register"
    elif yahoo is not None and yahoo > 0:
        price, source = yahoo, "yahoo_scaled"
    else:
        reason = "NO_PRICE_AT_DATE" if history is not None and not history.empty else "NO_HISTORY"
        return McapPoint(None, None, None, None, None, yahoo, reason)
    adj, obs_date, reason = shares_at(history, shares, day, lag_days)
    if adj is None:
        return McapPoint(None, None, None, price, source, yahoo, reason)
    if not adj > 0:
        return McapPoint(None, adj, obs_date, price, source, yahoo, "NON_POSITIVE")
    return McapPoint(adj * price, adj, obs_date, price, source, yahoo, "OK")


def mcap_panel(history: pd.DataFrame | None, shares: pd.Series | None, days: pd.DatetimeIndex, lag_days: int, segments: list[ScaleSegment] | None = None) -> np.ndarray:
    """Versione vettoriale su molte date (pool del matched control), prezzo Yahoo riscalato."""
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
    close_raw = close * split_factor_after(history, pd.Series(days)) * scale_at(segments or [], pd.Series(days))
    sidx = shares.index.to_numpy()
    spos = sidx.searchsorted(d - np.timedelta64(lag_days, "D"), side="right") - 1
    sok = spos >= 0
    obs = np.full(len(d), np.nan)
    obs_date = np.full(len(d), np.datetime64("NaT", "ns"), dtype="datetime64[ns]")
    obs[sok] = shares.to_numpy(dtype=float)[spos[sok]]
    obs_date[sok] = sidx[spos[sok]]
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
