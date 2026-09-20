"""The single read path into the register for gates, events and controls (ADR-034).

`Register.visible(as_of, issuer_key)` returns exactly what an observer could see at `as_of`:

- ``snapshot`` (primary): rows that are current in the snapshot and published no later than `as_of`;
- ``as_seen`` (robustness): every version from its publication until the version that replaces it is
  published. Cancelled rows stay visible, because the register carries no cancellation timestamp.

``timing="pub"`` orders visibility by `published_at`; ``timing="first_pub"`` by the first publication of
the correction chain (sensitivity). The `person_key` column applies the name merges valid at `as_of`;
issuers without merge rules — the vast majority — reuse the precomputed column and cost no copy.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .names import MergeRule, apply_merges

MODES = ("snapshot", "as_seen")
TIMINGS = ("pub", "first_pub")


@dataclass
class Register:
    df: pd.DataFrame
    rules: list[MergeRule] = field(default_factory=list)
    mode: str = "snapshot"
    timing: str = "pub"

    def __post_init__(self) -> None:
        if self.mode not in MODES:
            raise ValueError(f"mode must be one of {MODES}, got {self.mode!r}")
        if self.timing not in TIMINGS:
            raise ValueError(f"timing must be one of {TIMINGS}, got {self.timing!r}")
        base = self.df
        if self.mode == "snapshot":
            base = base[base["chain_status"] == "current"]
        time_col = "published_at" if self.timing == "pub" else "first_published_at"
        base = base.assign(visible_from=base[time_col], person_key=base["name_key"])
        self._all = base.sort_values("visible_from", kind="stable").reset_index(drop=True)
        self._all_times = self._all["visible_from"].to_numpy()
        self._by_issuer = {k: g.reset_index(drop=True) for k, g in self._all.groupby("issuer_key", sort=False)}
        self._issuer_times = {k: g["visible_from"].to_numpy() for k, g in self._by_issuer.items()}
        self._rules_by_issuer: dict[str, list[MergeRule]] = {}
        for rule in self.rules:
            self._rules_by_issuer.setdefault(rule.issuer_key, []).append(rule)

    @property
    def issuers(self) -> list[str]:
        return list(self._by_issuer)

    def timeline(self, issuer_key: str | None = None) -> pd.DataFrame:
        """Every row that was visible at some point, ordered by `visible_from`.

        Only for enumerating candidate instants; decisions must go through `visible()`.
        """
        if issuer_key is None:
            return self._all
        frame = self._by_issuer.get(issuer_key)
        return self._all.iloc[:0] if frame is None else frame

    def visible(self, as_of: pd.Timestamp, issuer_key: str | None = None, since: pd.Timestamp | None = None) -> pd.DataFrame:
        """Rows visible at `as_of`; `since` additionally keeps only trades on or after that date."""
        as_of = pd.Timestamp(as_of)
        if issuer_key is None:
            frame, times, rules = self._all, self._all_times, self.rules
        else:
            frame = self._by_issuer.get(issuer_key)
            if frame is None:
                return self._all.iloc[:0]
            times, rules = self._issuer_times[issuer_key], self._rules_by_issuer.get(issuer_key, [])
        sub = frame.iloc[: int(times.searchsorted(np.datetime64(as_of), side="right"))]
        if self.mode == "as_seen":
            end = sub["superseded_at"]
            sub = sub[end.isna() | (end > as_of)]
        if since is not None:
            sub = sub[sub["trade_date"] >= since]
        active = [r for r in rules if r.valid_from <= as_of and (r.valid_until is None or as_of < r.valid_until)]
        return sub.assign(person_key=apply_merges(sub["issuer_key"], sub["name_key"], as_of, active)) if active else sub
