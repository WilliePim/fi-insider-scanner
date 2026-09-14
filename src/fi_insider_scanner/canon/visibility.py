"""Unico punto di accesso al registro per gate, eventi e control (ADR-034).

`Register.visible(as_of, issuer_key)` restituisce solo ciò che un osservatore poteva
vedere all'istante `as_of`:
- mode="snapshot": righe allo stato finale dello snapshot (chain_status == current)
  pubblicate entro `as_of`;
- mode="as_seen": ogni versione dalla sua pubblicazione fino alla pubblicazione della
  versione che la sostituisce; le Makulerad restano visibili (data di annullamento ignota).
timing="pub" usa `published_at`; timing="first_pub" usa `first_published_at` (sensibilità).
La colonna `person_key` applica i merge di nome validi in `as_of`.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .names import MergeRule, apply_merges


@dataclass
class Register:
    df: pd.DataFrame
    rules: list[MergeRule] = field(default_factory=list)
    mode: str = "snapshot"
    timing: str = "pub"

    def __post_init__(self) -> None:
        if self.mode not in ("snapshot", "as_seen"):
            raise ValueError(self.mode)
        if self.timing not in ("pub", "first_pub"):
            raise ValueError(self.timing)
        base = self.df
        if self.mode == "snapshot":
            base = base[base["chain_status"] == "current"]
        time_col = "published_at" if self.timing == "pub" else "first_published_at"
        base = base.assign(visible_from=base[time_col]).sort_values("visible_from", kind="stable")
        self._all = base.reset_index(drop=True)
        self._all_times = self._all["visible_from"].to_numpy()
        self._by_issuer = {k: g.reset_index(drop=True) for k, g in self._all.groupby("issuer_key", sort=False)}
        self._issuer_times = {k: g["visible_from"].to_numpy() for k, g in self._by_issuer.items()}
        self._rules_by_issuer: dict[str, list[MergeRule]] = {}
        for r in self.rules:
            self._rules_by_issuer.setdefault(r.issuer_key, []).append(r)

    @property
    def issuers(self) -> list[str]:
        return list(self._by_issuer)

    def timeline(self, issuer_key: str | None = None) -> pd.DataFrame:
        """Tutte le righe che sono state visibili in qualche istante, ordinate per `visible_from`.

        Serve solo a enumerare gli istanti candidati; le decisioni vanno prese con `visible()`.
        """
        if issuer_key is None:
            return self._all
        frame = self._by_issuer.get(issuer_key)
        return self._all.iloc[:0] if frame is None else frame

    def _cut(self, frame: pd.DataFrame, times: np.ndarray, as_of: pd.Timestamp) -> pd.DataFrame:
        n = int(times.searchsorted(np.datetime64(as_of), side="right"))
        sub = frame.iloc[:n]
        if self.mode == "as_seen":
            end = sub["superseded_at"]
            sub = sub[end.isna() | (end > as_of) | (sub["chain_status"].isin(["current", "cancelled"]))]
        return sub

    def visible(self, as_of: pd.Timestamp, issuer_key: str | None = None) -> pd.DataFrame:
        as_of = pd.Timestamp(as_of)
        if issuer_key is not None:
            frame = self._by_issuer.get(issuer_key)
            if frame is None:
                return self._all.iloc[:0].assign(person_key=pd.Series(dtype="object"))
            sub = self._cut(frame, self._issuer_times[issuer_key], as_of)
            rules = self._rules_by_issuer.get(issuer_key, [])
        else:
            sub = self._cut(self._all, self._all_times, as_of)
            rules = self.rules
        return sub.assign(person_key=apply_merges(sub["issuer_key"], sub["name_key"], as_of, rules))
