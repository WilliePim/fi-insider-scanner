"""Per-issuer market context: verified ticker, price history, share counts, splits, report dates."""

from __future__ import annotations

from functools import cache

import pandas as pd

from ..backtest.events import MarketContext
from . import yf_cache
from .prices import ScaleSegment, split_ratios


def parse_segments(text) -> list[ScaleSegment]:
    if not isinstance(text, str) or not text:
        return []
    out = []
    for part in text.split(";"):
        rng, factor, n = part.rsplit(":", 2)
        start, end = rng.split("..")
        out.append(ScaleSegment(pd.Timestamp(start), pd.Timestamp(end), float(factor), int(n)))
    return out


class YahooMarket:
    """Callable `(issuer_key, isin) -> MarketContext` used by events and gates.

    Ticker: the one of the event's ISIN unless it was rejected (verified True or None); otherwise the verified
    ticker of another share ISIN of the same issuer (for share counts and report dates).
    """

    def __init__(self, resolution: pd.DataFrame, with_reports: bool = True, primary_only_verified: bool = False):
        res = resolution[resolution["symbol"].notna()].copy()
        res["ok"] = res["verified"].map(lambda v: v is True or v == 1)
        res["none"] = res["verified"].isna()
        usable = res[res["ok"] | (res["none"] & (not primary_only_verified))]
        self._by_isin = dict(zip(usable["isin"], usable["symbol"], strict=True))
        self._verified_by_isin = dict(zip(res["isin"], res["ok"], strict=True))
        segs = res["scale_segments"] if "scale_segments" in res else pd.Series([""] * len(res), index=res.index)
        best: dict[str, tuple[int, list[ScaleSegment]]] = {}
        for sym, text, nrows in zip(res["symbol"], segs, res["n_rows"], strict=True):
            parsed = parse_segments(text)
            # per symbol keep the segments of the ISIN with the most rows (one ticker can serve several historical ISINs)
            if parsed and (sym not in best or nrows > best[sym][0]):
                best[sym] = (int(nrows), parsed)
        self._segments_by_symbol = {k: v[1] for k, v in best.items()}
        ranked = usable.sort_values(["ok", "n_rows"], ascending=[False, False])
        self._by_issuer = ranked.groupby("issuer_key")["symbol"].first().to_dict()
        self.with_reports = with_reports

    def symbol(self, issuer_key: str, isin: str | None) -> str | None:
        if isin is not None and isin in self._by_isin:
            return self._by_isin[isin]
        return self._by_issuer.get(issuer_key)

    def is_verified(self, isin: str | None) -> bool | None:
        return self._verified_by_isin.get(isin)

    def segments(self, symbol: str | None) -> list[ScaleSegment]:
        return self._segments_by_symbol.get(symbol, []) if symbol else []

    def symbol_for_isin(self, isin: str | None) -> str | None:
        """Only the ticker of that ISIN (verified or unverifiable): never a fallback to another share class."""
        return self._by_isin.get(isin) if isin is not None else None

    def issuer_symbols(self) -> dict[str, str]:
        return dict(self._by_issuer)

    @staticmethod
    @cache
    def history(symbol: str) -> pd.DataFrame | None:
        return yf_cache.history(symbol)

    @staticmethod
    @cache
    def shares(symbol: str) -> pd.Series | None:
        return yf_cache.shares_full(symbol)

    @classmethod
    @cache
    def splits(cls, symbol: str | None) -> pd.Series:
        """Split ratios of a symbol, cached: the hot paths must not rescan the price history."""
        history = cls.history(symbol) if symbol else None
        return split_ratios(history) if history is not None else pd.Series(dtype=float)

    @staticmethod
    @cache
    def reports(symbol: str) -> pd.DatetimeIndex | None:
        return yf_cache.earnings_dates(symbol)

    def __call__(self, issuer_key: str, isin: str | None) -> MarketContext:
        sym = self.symbol(issuer_key, isin)
        if sym is None:
            return MarketContext()
        hist = self.history(sym)
        splits = None
        if hist is not None and "Stock Splits" in hist:
            s = hist["Stock Splits"]
            splits = s[s.fillna(0) > 0]
        return MarketContext(
            shares=self.shares(sym),
            splits=splits,
            report_dates=self.reports(sym) if self.with_reports else None,
        )
