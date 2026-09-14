"""Cluster B (ADR-018): >= 3 persone fisiche distinte con righe B_row entro 30 giorni.

Il trigger T è il primo istante di visibilità in cui la condizione è vera sulle sole righe
visibili. Le righe dei gruppi S3 non contano. Staleness = T - data di transazione della riga
che completa il cluster (la più recente tra quelle diventate visibili in T). Un nuovo episodio
per lo stesso emittente richiede un'ancora oltre fine episodio precedente + cooldown.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from ..canon.visibility import Register
from .openmarket import b_row
from .structural import uniform_price_groups

LOOKBACK_DAYS = 365


@dataclass(frozen=True)
class ClusterTrigger:
    issuer_key: str
    as_of: pd.Timestamp
    anchor: pd.Timestamp
    window_end: pd.Timestamp
    persons: tuple[str, ...]
    record_ids: tuple[str, ...]
    trigger_record_ids: tuple[str, ...]
    staleness_days: int
    is_stale: bool
    s3_in_window: bool
    uniform_onvenue_in_window: bool


def find_window(rows: pd.DataFrame, min_persons: int, window_days: int, min_anchor: pd.Timestamp | None):
    """Prima finestra [d, d+window] (ancora più vecchia) con >= min_persons persone distinte."""
    r = rows if min_anchor is None else rows[rows["trade_date"] >= min_anchor]
    r = r.sort_values(["trade_date", "record_id"], kind="stable")
    dates = r["trade_date"].to_numpy()
    persons = r["person_key"].to_numpy()
    span = np.timedelta64(window_days, "D")
    for i in range(len(r)):
        j = int(dates.searchsorted(dates[i] + span, side="right"))
        if len(set(persons[i:j])) >= min_persons:
            return r.iloc[i:j]
    return None


def detect_clusters(register: Register, issuer_key: str, cfg: dict) -> list[ClusterTrigger]:
    cc, sc = cfg["cluster"], cfg["structural"]
    timeline = register.timeline(issuer_key)
    cand = timeline[b_row(timeline) & timeline["pdmr_is_natural_person"].eq(True)]
    if cand["name_key"].nunique() < cc["min_persons"]:
        return []
    triggers: list[ClusterTrigger] = []
    episode_end: pd.Timestamp | None = None
    cooldown = pd.Timedelta(days=cc["episode_cooldown_days"])
    for t in pd.unique(cand["visible_from"]):
        t = pd.Timestamp(t)
        v = register.visible(t, issuer_key)
        rows = v[b_row(v) & v["pdmr_is_natural_person"].eq(True) & (v["trade_date"] >= t - pd.Timedelta(days=LOOKBACK_DAYS))]
        if rows["person_key"].nunique() < cc["min_persons"]:
            continue
        groups = uniform_price_groups(v[v["trade_date"] >= t - pd.Timedelta(days=LOOKBACK_DAYS)], sc["min_persons_same_price"], sc["subscription_price_window_days"])
        s3_ids = {rid for ids in groups.loc[groups["s3"], "record_ids"] for rid in ids} if not groups.empty else set()
        counted = rows[~rows["record_id"].isin(s3_ids)]
        min_anchor = None if episode_end is None else episode_end + cooldown + pd.Timedelta(days=1)
        window = find_window(counted, cc["min_persons"], cc["window_days"], min_anchor)
        if window is None:
            continue
        anchor, end = window["trade_date"].min(), window["trade_date"].max()
        new = window[window["visible_from"] == t]
        reference = new["trade_date"].max() if not new.empty else end
        staleness = int((t.normalize() - reference).days)
        in_window = groups[(groups["trade_date"] >= anchor) & (groups["trade_date"] <= anchor + pd.Timedelta(days=cc["window_days"]))] if not groups.empty else groups
        triggers.append(
            ClusterTrigger(
                issuer_key=issuer_key,
                as_of=t,
                anchor=anchor,
                window_end=end,
                persons=tuple(sorted(window["person_key"].unique())),
                record_ids=tuple(window["record_id"]),
                trigger_record_ids=tuple(new["record_id"]),
                staleness_days=staleness,
                is_stale=staleness > cc["max_staleness_days"],
                s3_in_window=bool(not in_window.empty and in_window["s3"].any()),
                uniform_onvenue_in_window=bool(not in_window.empty and in_window["uniform_onvenue"].any()),
            )
        )
        episode_end = end
    return triggers
