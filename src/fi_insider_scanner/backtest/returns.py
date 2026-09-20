"""Event returns (ADR-028).

The calendar is the benchmark's own sessions (^OMXSPI).
- entry session = the first session dated after the publication day D
- the stock's entry bar = the first bar dated on or after the entry session, within `max_stale_sessions`
  (never an earlier price: it would predate the publication)
- exit session = entry session + h; exit bar = the stock's last bar on or before the exit session
- r = Close_exit / Close_entry - 1 (split-adjusted, dividends excluded); the benchmark over the same dates
- excess = r - r_bench
Statuses: OK, TOO_RECENT, NO_HISTORY, NO_ENTRY_BAR, ENDED_IN_WINDOW, ARTEFACT (|r| above the threshold).
The "bar parity" variant exits at entry bar + h in the stock's own series, as the US test does.
`expost_*` columns are diagnostics computed with future data: never used to select an event.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd


@dataclass
class EventReturn:
    status: str
    entry_date: pd.Timestamp | None = None
    exit_date: pd.Timestamp | None = None
    stale_entry_sessions: int | None = None
    stale_exit_sessions: int | None = None
    r_stock: float | None = None
    r_bench: float | None = None
    excess: float | None = None
    r_stock_adj: float | None = None
    excess_adj: float | None = None
    excess_last_flat: float | None = None
    expost_max_abs_daily: float | None = None

    def as_dict(self, prefix: str = "") -> dict:
        return {f"{prefix}{k}": v for k, v in asdict(self).items()}


def _asof_value(series: pd.Series, day: pd.Timestamp) -> float | None:
    pos = int(series.index.searchsorted(day, side="right")) - 1
    return None if pos < 0 else float(series.iloc[pos])


def event_return(
    history: pd.DataFrame | None,
    bench: pd.Series,
    event_day: pd.Timestamp,
    horizon: int,
    max_stale_sessions: int,
    artefact: float,
    own_bars: bool = False,
) -> EventReturn:
    sessions = bench.index
    i0 = int(sessions.searchsorted(pd.Timestamp(event_day).normalize() + pd.Timedelta(days=1), side="left"))
    if i0 + horizon >= len(sessions):
        return EventReturn("TOO_RECENT")
    if history is None or history.empty:
        return EventReturn("NO_HISTORY")
    entry_session = sessions[i0]
    hidx = history.index
    j0 = int(hidx.searchsorted(entry_session, side="left"))
    if j0 >= len(hidx):
        return EventReturn("NO_ENTRY_BAR")
    entry_date = hidx[j0]
    stale_entry = int(sessions.searchsorted(entry_date, side="left")) - i0
    if stale_entry > max_stale_sessions:
        return EventReturn("NO_ENTRY_BAR", stale_entry_sessions=stale_entry)
    close = history["Close"].to_numpy(dtype=float, copy=False)
    adj = history["Adj Close"].to_numpy(dtype=float, copy=False) if "Adj Close" in history else close
    p0, a0 = float(close[j0]), float(adj[j0])
    if not p0 > 0:
        return EventReturn("NO_ENTRY_BAR")

    if own_bars:
        if j0 + horizon >= len(hidx):
            return EventReturn("ENDED_IN_WINDOW", entry_date=entry_date)
        j1 = j0 + horizon
        exit_date = hidx[j1]
        stale_exit = 0
    else:
        exit_session = sessions[i0 + horizon]
        j1 = int(hidx.searchsorted(exit_session, side="right")) - 1
        exit_date = hidx[j1]
        stale_exit = i0 + horizon - int(sessions.searchsorted(exit_date, side="left"))
        if stale_exit > max_stale_sessions:
            last_flat = float(close[j1]) / p0 - 1
            b_flat = bench.iloc[i0 + horizon] / _asof_value(bench, entry_date) - 1
            return EventReturn(
                "ENDED_IN_WINDOW",
                entry_date=entry_date,
                exit_date=exit_date,
                stale_entry_sessions=stale_entry,
                stale_exit_sessions=stale_exit,
                excess_last_flat=float(last_flat - b_flat),
            )
        exit_date_for_bench = exit_session
    b0 = _asof_value(bench, entry_date)
    b1 = _asof_value(bench, exit_date if own_bars else exit_date_for_bench)
    r = float(close[j1]) / p0 - 1
    rb = b1 / b0 - 1
    ra = float(adj[j1]) / a0 - 1 if a0 > 0 else None
    window = close[j0 : j1 + 1]
    daily = np.abs(np.diff(window) / window[:-1]).max() if len(window) > 1 else 0.0
    status = "ARTEFACT" if abs(r) > artefact else "OK"
    return EventReturn(
        status=status,
        entry_date=entry_date,
        exit_date=exit_date,
        stale_entry_sessions=stale_entry,
        stale_exit_sessions=stale_exit,
        r_stock=r,
        r_bench=rb,
        excess=r - rb,
        r_stock_adj=ra,
        excess_adj=None if ra is None else ra - rb,
        expost_max_abs_daily=float(daily) if pd.notna(daily) else None,
    )


def monthly_excess(history: pd.DataFrame, bench: pd.Series, entry: pd.Timestamp, exit_: pd.Timestamp) -> pd.DataFrame:
    """Monthly excess returns of the event between entry and exit (for the calendar-time portfolio)."""
    close = history["Close"].astype(float)
    s = close[(close.index >= entry) & (close.index <= exit_)]
    b = bench[(bench.index >= entry) & (bench.index <= exit_)]
    if len(s) < 2 or len(b) < 2:
        return pd.DataFrame(columns=["month", "excess"])
    sm = s.groupby(s.index.to_period("M")).last()
    bm = b.groupby(b.index.to_period("M")).last()
    s0 = pd.Series([float(s.iloc[0])], index=[sm.index[0] - 1])
    b0 = pd.Series([float(b.iloc[0])], index=[bm.index[0] - 1])
    rs = pd.concat([s0, sm]).pct_change().dropna()
    rb = pd.concat([b0, bm]).pct_change().dropna()
    joined = pd.concat([rs.rename("s"), rb.rename("b")], axis=1).dropna()
    return pd.DataFrame({"month": joined.index.astype(str), "excess": (joined["s"] - joined["b"]).to_numpy()})
