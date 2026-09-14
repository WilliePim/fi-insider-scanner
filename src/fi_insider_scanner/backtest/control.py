"""Matched control (ADR-031).

Per ogni evento: peer = emittente diverso, stessa banda di market cap alla stessa data, nessuna
riga B_row visibile a T con data di transazione in [D-60, D], log-cap più vicino; a parità
issuer_key minore. Il pool è l'insieme degli emittenti del registro con ticker (passato dal chiamante,
già con mcap alla data). Tutte le classi dell'emittente dell'evento sono escluse perché il pool è per
emittente.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..canon.visibility import Register
from ..gates.openmarket import b_row


class QuietIndex:
    """Righe B_row (emittente, data transazione, visibile da) per il controllo di "quiet"."""

    def __init__(self, register: Register):
        tl = register.timeline()
        rows = tl[b_row(tl)]
        self.issuer = rows["issuer_key"].to_numpy()
        self.trade = rows["trade_date"].to_numpy()
        self.visible = rows["visible_from"].to_numpy()

    def active_issuers(self, as_of: pd.Timestamp, day: pd.Timestamp, quiet_days: int) -> set[str]:
        start = np.datetime64(pd.Timestamp(day).normalize() - pd.Timedelta(days=quiet_days))
        end = np.datetime64(pd.Timestamp(day).normalize())
        m = (self.trade >= start) & (self.trade <= end) & (self.visible <= np.datetime64(pd.Timestamp(as_of)))
        return set(self.issuer[m])


def pick_peer(event_issuer: str, event_mcap_usd: float, band: str, pool: pd.DataFrame, active: set[str]) -> pd.Series | None:
    """`pool`: colonne issuer_key, symbol, mcap_usd, band (alla data dell'evento)."""
    cand = pool[(pool["band"] == band) & (pool["issuer_key"] != event_issuer) & ~pool["issuer_key"].isin(active)]
    cand = cand[np.isfinite(cand["mcap_usd"]) & (cand["mcap_usd"] > 0)]
    if cand.empty or not event_mcap_usd > 0:
        return None
    dist = np.abs(np.log(cand["mcap_usd"].to_numpy()) - np.log(event_mcap_usd))
    cand = cand.assign(_dist=dist).sort_values(["_dist", "issuer_key"], kind="stable")
    return cand.iloc[0]
