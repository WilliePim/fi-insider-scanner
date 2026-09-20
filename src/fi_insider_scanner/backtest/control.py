"""Matched control (ADR-031).

For each event the peer is a different issuer of the register with a usable ticker, in the same
market-cap band on the same date, with no visible open-market PDMR purchase in the previous 60 days,
and the closest log market cap; ties go to the lower issuer key. Candidates are held as parallel
numpy arrays because the peer pool is scanned once per event.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from ..canon.visibility import Register
from ..gates.openmarket import b_row


class QuietIndex:
    """Open-market purchase rows, indexed by trade date, for the "quiet issuer" condition."""

    def __init__(self, register: Register):
        rows = register.timeline()
        rows = rows[b_row(rows)].sort_values("trade_date", kind="stable")
        self.issuer = rows["issuer_key"].to_numpy()
        self.trade = rows["trade_date"].to_numpy()
        self.visible = rows["visible_from"].to_numpy()

    def active_issuers(self, as_of: pd.Timestamp, day: pd.Timestamp, quiet_days: int) -> set[str]:
        """Issuers with a purchase traded in [day − quiet_days, day] and already published at `as_of`."""
        day = pd.Timestamp(day).normalize()
        lo = self.trade.searchsorted(np.datetime64(day - pd.Timedelta(days=quiet_days)), side="left")
        hi = self.trade.searchsorted(np.datetime64(day), side="right")
        if hi <= lo:
            return set()
        window = slice(lo, hi)
        return set(self.issuer[window][self.visible[window] <= np.datetime64(pd.Timestamp(as_of))])


@dataclass(frozen=True)
class PeerCandidates:
    """Peer pool at one date: parallel arrays, `band` holding the label or None."""

    issuer_key: np.ndarray
    symbol: np.ndarray
    mcap_usd: np.ndarray
    band: np.ndarray

    @classmethod
    def from_frame(cls, df: pd.DataFrame) -> PeerCandidates:
        return cls(df["issuer_key"].to_numpy(), df["symbol"].to_numpy(), df["mcap_usd"].to_numpy(dtype=float), df["band"].to_numpy())


@dataclass(frozen=True)
class Peer:
    issuer_key: str
    symbol: str
    mcap_usd: float


def pick_peer(event_issuer: str, event_mcap_usd: float, band: str, candidates: PeerCandidates, active: set[str]) -> Peer | None:
    eligible = (
        (candidates.band == band) & (candidates.issuer_key != event_issuer) & np.isfinite(candidates.mcap_usd) & (candidates.mcap_usd > 0)
    )
    if active:
        eligible &= ~np.isin(candidates.issuer_key, list(active))
    if not eligible.any() or not event_mcap_usd > 0:
        return None
    index = np.flatnonzero(eligible)
    distance = np.abs(np.log(candidates.mcap_usd[index]) - np.log(event_mcap_usd))
    best = index[np.lexsort((candidates.issuer_key[index], distance))[0]]
    return Peer(str(candidates.issuer_key[best]), str(candidates.symbol[best]), float(candidates.mcap_usd[best]))
