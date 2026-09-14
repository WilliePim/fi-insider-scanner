"""Prezzi raw, fattori di scala Yahoo e verifica di un ticker contro i prezzi del registro (ADR-024, ADR-025).

Yahoo restituisce OHLC aggiustati per split (auto_adjust=False non toglie gli split). Per molti titoli di
Stoccolma la storia precedente a un'emissione di diritti o a uno spin-off è inoltre riscalata di un fattore
costante che NON compare in `Stock Splits` (verificato: Securitas 1,20x prima dell'ottobre 2022, Dustin 2,0x
prima del 2023, Scandic 1,4x prima del 2021, Sandvik 1,05x prima dello spin-off Alleima). Il registro FI
contiene prezzi di esecuzione reali: il rapporto prezzo registro / Close Yahoo, per tratti costante, stima
quel fattore. prezzo raw(d) = Close(d) * split_factor_after(d) * scale(d).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

SCALE_TOL = 0.03
RECENT_ROWS = 20


def split_factor_after(history: pd.DataFrame, dates: pd.Series) -> np.ndarray:
    splits = history["Stock Splits"] if "Stock Splits" in history else pd.Series(dtype=float)
    splits = splits[splits.fillna(0) > 0]
    if splits.empty:
        return np.ones(len(dates))
    s_dates = splits.index.to_numpy()
    ratios = splits.to_numpy(dtype=float)
    suffix = np.append(np.cumprod(ratios[::-1])[::-1], 1.0)
    pos = s_dates.searchsorted(pd.to_datetime(dates).to_numpy(), side="right")
    return suffix[pos]


def ratio_table(history: pd.DataFrame, trades: pd.DataFrame) -> pd.DataFrame:
    """Per ogni riga del registro con bar Yahoo lo stesso giorno: prezzo, Low/High/Close split-adjusted raw, rapporto."""
    t = trades.dropna(subset=["trade_date", "price"])
    t = t[(t["price"] > 0) & t["trade_date"].isin(history.index)].sort_values("trade_date")
    if t.empty:
        return pd.DataFrame(columns=["trade_date", "price", "low", "high", "close", "ratio"])
    hist = history.loc[t["trade_date"]]
    f = split_factor_after(history, t["trade_date"])
    out = pd.DataFrame(
        {
            "trade_date": t["trade_date"].to_numpy(),
            "price": t["price"].to_numpy(dtype=float),
            "low": hist["Low"].to_numpy(dtype=float) * f,
            "high": hist["High"].to_numpy(dtype=float) * f,
            "close": hist["Close"].to_numpy(dtype=float) * f,
        }
    )
    out["ratio"] = out["price"] / out["close"].where(out["close"] > 0)
    return out


@dataclass(frozen=True)
class ScaleSegment:
    start: pd.Timestamp
    end: pd.Timestamp
    factor: float
    n: int


def estimate_scale_segments(history: pd.DataFrame, trades: pd.DataFrame, tol: float = SCALE_TOL, min_rows: int = 3) -> list[ScaleSegment]:
    """Tratti (per anno, poi fusi se compatibili) con fattore = mediana(prezzo registro / Close Yahoo)."""
    rt = ratio_table(history, trades).dropna(subset=["ratio"])
    if len(rt) < min_rows:
        return []
    rt["year"] = pd.to_datetime(rt["trade_date"]).dt.year
    groups = []
    for _, g in rt.groupby("year"):
        if len(g) >= 2:
            groups.append([pd.Timestamp(g["trade_date"].min()), pd.Timestamp(g["trade_date"].max()), float(g["ratio"].median()), int(len(g)), list(g["ratio"])])
    if not groups:
        return []
    merged = [groups[0]]
    for start, end, med, n, ratios in groups[1:]:
        last = merged[-1]
        if abs(med / last[2] - 1) <= tol:
            all_r = last[4] + ratios
            merged[-1] = [last[0], end, float(np.median(all_r)), last[3] + n, all_r]
        else:
            merged.append([start, end, med, n, ratios])
    return [ScaleSegment(s, e, f, n) for s, e, f, n, _ in merged if n >= 2]


def scale_at(segments: list[ScaleSegment], dates: pd.Series) -> np.ndarray:
    """Fattore del tratto che contiene la data; fuori dai tratti, quello del tratto più vicino; 1,0 senza tratti."""
    d = pd.to_datetime(pd.Series(dates)).to_numpy()
    out = np.ones(len(d))
    if not segments:
        return out
    starts = np.array([np.datetime64(s.start) for s in segments])
    ends = np.array([np.datetime64(s.end) for s in segments])
    factors = np.array([s.factor for s in segments])
    for i, day in enumerate(d):
        inside = np.where((starts <= day) & (day <= ends))[0]
        if len(inside):
            out[i] = factors[inside[0]]
            continue
        dist = np.minimum(np.abs((starts - day).astype("timedelta64[D]").astype(int)), np.abs((ends - day).astype("timedelta64[D]").astype(int)))
        out[i] = factors[int(dist.argmin())]
    return out


def raw_close(history: pd.DataFrame, dates: pd.Series, segments: list[ScaleSegment] | None = None) -> np.ndarray:
    idx = history.index.to_numpy()
    d = pd.to_datetime(dates).to_numpy()
    pos = idx.searchsorted(d, side="right") - 1
    out = np.full(len(d), np.nan)
    ok = pos >= 0
    out[ok] = history["Close"].to_numpy(dtype=float)[pos[ok]]
    return out * split_factor_after(history, dates) * scale_at(segments or [], dates)


@dataclass(frozen=True)
class Verification:
    verified: bool | None
    n_checked: int
    share_in_range: float | None
    share_in_range_recent: float | None
    median_ratio: float | None
    reason: str
    adjusted_history: bool = False
    segments: tuple = field(default_factory=tuple)


def verify_against_register(history: pd.DataFrame | None, trades: pd.DataFrame, tolerance: float, min_rows: int, min_share: float, recent_rows: int = RECENT_ROWS) -> Verification:
    """`trades`: colonne trade_date, price (SEK). Verificato se il prezzo cade in [Low, High] raw ±tol
    per >= min_share delle ultime `recent_rows` righe (la coda della storia non è riscalata da Yahoo),
    oppure di tutte le righe. Il riscalamento dei tratti precedenti è registrato, non penalizzato."""
    if history is None or history.empty:
        return Verification(False, 0, None, None, None, "NO_HISTORY")
    rt = ratio_table(history, trades)
    n = len(rt)
    if n < min_rows:
        return Verification(None, n, None, None, None, "TOO_FEW_ROWS")
    inside = (rt["price"] >= rt["low"] * (1 - tolerance)) & (rt["price"] <= rt["high"] * (1 + tolerance))
    share_all = float(inside.mean())
    share_recent = float(inside.iloc[-recent_rows:].mean())
    ratio = float(np.nanmedian(rt["ratio"]))
    segments = tuple(estimate_scale_segments(history, trades))
    adjusted = any(abs(s.factor - 1) > SCALE_TOL for s in segments)
    if share_recent >= min_share or share_all >= min_share:
        return Verification(True, n, share_all, share_recent, ratio, "OK", adjusted, segments)
    recent_ratio = float(np.nanmedian(rt["ratio"].iloc[-recent_rows:]))
    if recent_ratio > 0 and (50 <= recent_ratio <= 200 or 1 / 200 <= recent_ratio <= 1 / 50):
        return Verification(False, n, share_all, share_recent, ratio, "SCALE_SUSPECT", adjusted, segments)
    return Verification(False, n, share_all, share_recent, ratio, "PRICE_MISMATCH", adjusted, segments)
