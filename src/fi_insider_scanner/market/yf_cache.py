"""Immutable on-disk cache of the yfinance calls (ADR-025).

One network call per ticker and kind, then everything is read from disk. An empty response is recorded as
empty (a marker), so it is never repeated. A fixed pause separates the network calls.
"""

from __future__ import annotations

import re
import time
from pathlib import Path

import pandas as pd

from .. import config

_last_call = [0.0]


def _pause() -> None:
    wait = config.load()["resolver"]["pause_seconds"] - (time.monotonic() - _last_call[0])
    if wait > 0:
        time.sleep(wait)
    _last_call[0] = time.monotonic()


def _yf():
    import yfinance as yf

    tz_dir = config.CACHE_DIR / "yf_tz"
    tz_dir.mkdir(parents=True, exist_ok=True)
    yf.set_tz_cache_location(str(tz_dir))
    return yf


def _path(kind: str, key: str) -> Path:
    safe = re.sub(r"[^A-Za-z0-9._=^-]", "_", key)
    p = config.CACHE_DIR / "yf" / kind / f"{safe}.csv"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _empty_marker(p: Path) -> Path:
    return p.with_suffix(".empty")


def history(ticker: str, start: str = "2015-01-01") -> pd.DataFrame | None:
    """OHLC not adjusted for dividends (auto_adjust=False), with Adj Close, Dividends and Stock Splits."""
    p = _path("history", ticker)
    if p.exists():
        df = pd.read_csv(p, parse_dates=["Date"], index_col="Date")
        return df
    if _empty_marker(p).exists():
        return None
    _pause()
    try:
        df = _yf().Ticker(ticker).history(start=start, auto_adjust=False, actions=True, repair=False, raise_errors=False)
    except Exception:
        df = None
    if df is None or df.empty:
        _empty_marker(p).touch()
        return None
    df.index = pd.DatetimeIndex(df.index.tz_localize(None) if df.index.tz is not None else df.index).normalize()
    df.index.name = "Date"
    df = df[~df.index.duplicated(keep="last")]
    df.to_csv(p)
    return df


def shares_full(ticker: str, start: str = "2015-01-01") -> pd.Series | None:
    p = _path("shares", ticker)
    if p.exists():
        s = pd.read_csv(p, parse_dates=["date"], index_col="date")["shares"]
        return s
    if _empty_marker(p).exists():
        return None
    _pause()
    try:
        s = _yf().Ticker(ticker).get_shares_full(start=start)
    except Exception:
        s = None
    if s is None or len(s) == 0:
        _empty_marker(p).touch()
        return None
    idx = pd.DatetimeIndex(s.index.tz_localize(None) if getattr(s.index, "tz", None) is not None else s.index).normalize()
    s = pd.Series(s.to_numpy(dtype=float), index=idx, name="shares")
    s = s[~s.index.duplicated(keep="last")].sort_index()
    s.index.name = "date"
    s.to_frame().to_csv(p)
    return s


def earnings_dates(ticker: str) -> pd.DatetimeIndex | None:
    p = _path("earnings", ticker)
    if p.exists():
        return pd.DatetimeIndex(pd.read_csv(p, parse_dates=["date"])["date"])
    if _empty_marker(p).exists():
        return None
    _pause()
    try:
        ed = _yf().Ticker(ticker).get_earnings_dates(limit=100)
    except Exception:
        ed = None
    if ed is None or len(ed) == 0:
        _empty_marker(p).touch()
        return None
    idx = ed.index.tz_convert("Europe/Stockholm").tz_localize(None) if ed.index.tz is not None else ed.index
    dates = pd.DatetimeIndex(sorted(set(idx.normalize())))
    pd.DataFrame({"date": dates}).to_csv(p, index=False)
    return dates


def search_isin(isin: str) -> list[dict]:
    p = _path("search", isin)
    if p.exists():
        return pd.read_csv(p).to_dict("records") if p.stat().st_size > 1 else []
    if _empty_marker(p).exists():
        return []
    _pause()
    try:
        quotes = _yf().Search(isin, max_results=8, news_count=0).quotes
    except Exception:
        quotes = []
    rows = [
        {"symbol": q.get("symbol"), "exchange": q.get("exchange"), "shortname": q.get("shortname"), "quoteType": q.get("quoteType")}
        for q in quotes
    ]
    if not rows:
        _empty_marker(p).touch()
        return []
    pd.DataFrame(rows).to_csv(p, index=False)
    return rows


def search_text(text: str) -> list[dict]:
    key = "name_" + text
    p = _path("search", key)
    if p.exists():
        return pd.read_csv(p).to_dict("records")
    if _empty_marker(p).exists():
        return []
    _pause()
    try:
        quotes = _yf().Search(text, max_results=8, news_count=0).quotes
    except Exception:
        quotes = []
    rows = [
        {"symbol": q.get("symbol"), "exchange": q.get("exchange"), "shortname": q.get("shortname"), "quoteType": q.get("quoteType")}
        for q in quotes
    ]
    if not rows:
        _empty_marker(p).touch()
        return []
    pd.DataFrame(rows).to_csv(p, index=False)
    return rows
