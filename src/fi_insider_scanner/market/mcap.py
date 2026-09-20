"""Point-in-time market cap (ADR-026).

mcap_SEK(d) = shares(d) * price(d)
- price(d): for an event, the SEK execution price of the register rows (real, on that date); otherwise the
  Yahoo close on or before d * split_factor_after(d) * scale(d) (ADR-025: the rescaling factor estimated
  from the register)
- shares(d): the last `shares_full` observation dated no later than d - lag, carried to d through the
  splits in between. `shares_full` is the company total (every class), so for a dual-class issuer the
  market cap uses the price of the class that was bought (stated as such).
No forward-fill beyond the date: when a piece is missing the market cap is None with a reason.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .prices import ScaleSegment, scale_at, split_factor_after, split_ratios

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


def _asof_position(index: pd.Index, day: pd.Timestamp) -> int:
    """Position of the last entry on or before `day`, or -1 when there is none."""
    return int(index.searchsorted(day, side="right")) - 1


def shares_at(
    history: pd.DataFrame | None,
    shares: pd.Series | None,
    day: pd.Timestamp,
    lag_days: int,
    splits: pd.Series | None = None,
) -> tuple[float | None, pd.Timestamp | None, str]:
    """Share count usable at `day`: last observation published at least `lag_days` earlier, split-adjusted to `day`."""
    if shares is None or shares.empty:
        return None, None, "NO_SHARES"
    pos = _asof_position(shares.index, day - pd.Timedelta(days=lag_days))
    if pos < 0:
        return None, None, "SHARES_NOT_YET_PUBLIC"
    obs_date, obs = shares.index[pos], float(shares.iloc[pos])
    if splits is None:
        splits = split_ratios(history) if history is not None else pd.Series(dtype=float)
    between = splits[(splits.index > obs_date) & (splits.index <= day)]
    return (obs * float(np.prod(between.to_numpy(dtype=float))) if len(between) else obs), obs_date, "OK"


def yahoo_close_raw(
    history: pd.DataFrame | None,
    day: pd.Timestamp,
    segments: list[ScaleSegment] | None = None,
    splits: pd.Series | None = None,
) -> float | None:
    """Yahoo close reconstructed to the price actually paid that day (splits and rescaling undone)."""
    if history is None or history.empty:
        return None
    pos = _asof_position(history.index, day)
    if pos < 0 or (day - history.index[pos]).days > MAX_PRICE_STALE_DAYS:
        return None
    if splits is None:
        splits = split_ratios(history)
    factor = float(np.prod(splits[splits.index > day].to_numpy(dtype=float))) if len(splits) else 1.0
    return float(history["Close"].to_numpy()[pos]) * factor * float(scale_at(segments or [], pd.Series([day]))[0])


def mcap_at(
    history: pd.DataFrame | None,
    shares: pd.Series | None,
    day: pd.Timestamp,
    lag_days: int,
    register_price: float | None = None,
    register_price_source: str | None = None,
    segments: list[ScaleSegment] | None = None,
    splits: pd.Series | None = None,
) -> McapPoint:
    """Market cap at `day`; `splits` may be passed precomputed to avoid rescanning the price history."""
    day = pd.Timestamp(day).normalize()
    if splits is None and history is not None:
        splits = split_ratios(history)
    yahoo = yahoo_close_raw(history, day, segments, splits)
    if register_price is not None and register_price > 0:
        price, source = float(register_price), register_price_source or "register"
    elif yahoo is not None and yahoo > 0:
        price, source = yahoo, "yahoo_scaled"
    else:
        reason = "NO_PRICE_AT_DATE" if history is not None and not history.empty else "NO_HISTORY"
        return McapPoint(None, None, None, None, None, yahoo, reason)
    adj, obs_date, reason = shares_at(history, shares, day, lag_days, splits)
    if adj is None:
        return McapPoint(None, None, None, price, source, yahoo, reason)
    if not adj > 0:
        return McapPoint(None, adj, obs_date, price, source, yahoo, "NON_POSITIVE")
    return McapPoint(adj * price, adj, obs_date, price, source, yahoo, "OK")


def mcap_panel(
    history: pd.DataFrame | None,
    shares: pd.Series | None,
    days: pd.DatetimeIndex,
    lag_days: int,
    segments: list[ScaleSegment] | None = None,
) -> np.ndarray:
    """Vectorised version over many dates (the matched-control pool), on the rescaled Yahoo price."""
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
