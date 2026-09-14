"""Contesto di mercato per emittente: ticker verificato, storia prezzi, azioni, split, date report."""

from __future__ import annotations

from functools import lru_cache

import pandas as pd

from ..backtest.events import MarketContext
from . import yf_cache


class YahooMarket:
    """Callable `(issuer_key, isin) -> MarketContext` usato da eventi e gate.

    Ticker: quello dell'ISIN dell'evento se non rifiutato (verified True o None); altrimenti il
    ticker verificato di un altro ISIN azionario dello stesso emittente (per azioni e date report).
    """

    def __init__(self, resolution: pd.DataFrame, with_reports: bool = True, primary_only_verified: bool = False):
        res = resolution[resolution["symbol"].notna()].copy()
        res["ok"] = res["verified"].map(lambda v: v is True or v == 1)
        res["none"] = res["verified"].isna()
        usable = res[res["ok"] | (res["none"] & (not primary_only_verified))]
        self._by_isin = dict(zip(usable["isin"], usable["symbol"]))
        self._verified_by_isin = dict(zip(res["isin"], res["ok"]))
        ranked = usable.sort_values(["ok", "n_rows"], ascending=[False, False])
        self._by_issuer = ranked.groupby("issuer_key")["symbol"].first().to_dict()
        self.with_reports = with_reports

    def symbol(self, issuer_key: str, isin: str | None) -> str | None:
        if isin is not None and isin in self._by_isin:
            return self._by_isin[isin]
        return self._by_issuer.get(issuer_key)

    def is_verified(self, isin: str | None) -> bool | None:
        return self._verified_by_isin.get(isin)

    def symbol_for_isin(self, isin: str | None) -> str | None:
        """Solo il ticker dell'ISIN stesso (verificato o non verificabile): nessun ripiego su altre classi."""
        return self._by_isin.get(isin) if isin is not None else None

    def issuer_symbols(self) -> dict[str, str]:
        return dict(self._by_issuer)

    @staticmethod
    @lru_cache(maxsize=None)
    def history(symbol: str) -> pd.DataFrame | None:
        return yf_cache.history(symbol)

    @staticmethod
    @lru_cache(maxsize=None)
    def shares(symbol: str) -> pd.Series | None:
        return yf_cache.shares_full(symbol)

    @staticmethod
    @lru_cache(maxsize=None)
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
