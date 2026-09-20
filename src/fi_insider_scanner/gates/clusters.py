"""Cluster gate B (ADR-018): at least three distinct natural persons buying within 30 days.

The trigger time T is the first publication instant at which the condition holds on the rows visible
then. Rows belonging to a structural subscription (S3) do not count. Staleness is T minus the trade
date of the row that completes the cluster. A new episode for the same issuer needs an anchor beyond
the previous episode end plus the cooldown.

The window search is a sliding window over trade dates (linear in the rows of the last year), and the
S3 groups are computed only once a window is found: structural subscriptions are rare, so paying for
the grouping at every publication instant would dominate the run.
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
    """Earliest-anchored window [d, d + window_days] holding at least `min_persons` distinct persons."""
    r = rows if min_anchor is None else rows[rows["trade_date"] >= min_anchor]
    if len(r) < min_persons:
        return None
    r = r.sort_values(["trade_date", "record_id"], kind="stable")
    dates = r["trade_date"].to_numpy()
    persons = r["person_key"].to_numpy()
    span = np.timedelta64(window_days, "D")
    counts: dict[str, int] = {}
    distinct = 0
    end = 0
    for start in range(len(r)):
        while end < len(r) and dates[end] <= dates[start] + span:
            counts[persons[end]] = counts.get(persons[end], 0) + 1
            distinct += counts[persons[end]] == 1
            end += 1
        if distinct >= min_persons:
            return r.iloc[start:end]
        counts[persons[start]] -= 1
        if counts[persons[start]] == 0:
            del counts[persons[start]]
            distinct -= 1
    return None


def _structural_ids(groups: pd.DataFrame) -> set[str]:
    if groups.empty:
        return set()
    return {rid for ids in groups.loc[groups["s3"], "record_ids"] for rid in ids}


def detect_clusters(register: Register, issuer_key: str, cfg: dict) -> list[ClusterTrigger]:
    cc, sc = cfg["cluster"], cfg["structural"]
    min_persons, window_days = cc["min_persons"], cc["window_days"]
    lookback = pd.Timedelta(days=LOOKBACK_DAYS)
    cooldown = pd.Timedelta(days=cc["episode_cooldown_days"] + 1)

    timeline = register.timeline(issuer_key)
    if timeline.empty:
        return []
    candidates = timeline[b_row(timeline) & timeline["pdmr_is_natural_person"].eq(True)]
    if candidates["name_key"].nunique() < min_persons:
        return []

    triggers: list[ClusterTrigger] = []
    episode_end: pd.Timestamp | None = None
    for raw_time in pd.unique(candidates["visible_from"]):
        as_of = pd.Timestamp(raw_time)
        visible = register.visible(as_of, issuer_key, since=as_of - lookback)
        rows = visible[b_row(visible) & visible["pdmr_is_natural_person"].eq(True)]
        if rows["person_key"].nunique() < min_persons:
            continue
        min_anchor = None if episode_end is None else episode_end + cooldown
        window = find_window(rows, min_persons, window_days, min_anchor)
        if window is None:
            continue

        groups = uniform_price_groups(visible, sc["min_persons_same_price"], sc["subscription_price_window_days"])
        structural = _structural_ids(groups)
        if structural & set(window["record_id"]):
            window = find_window(rows[~rows["record_id"].isin(structural)], min_persons, window_days, min_anchor)
            if window is None:
                continue

        anchor, end = window["trade_date"].min(), window["trade_date"].max()
        new_rows = window[window["visible_from"] == as_of]
        reference = new_rows["trade_date"].max() if not new_rows.empty else end
        staleness = int((as_of.normalize() - reference).days)
        in_window = groups[groups["trade_date"].between(anchor, anchor + pd.Timedelta(days=window_days))] if not groups.empty else groups
        triggers.append(
            ClusterTrigger(
                issuer_key=issuer_key,
                as_of=as_of,
                anchor=anchor,
                window_end=end,
                persons=tuple(sorted(window["person_key"].unique())),
                record_ids=tuple(window["record_id"]),
                trigger_record_ids=tuple(new_rows["record_id"]),
                staleness_days=staleness,
                is_stale=staleness > cc["max_staleness_days"],
                s3_in_window=bool(not in_window.empty and in_window["s3"].any()),
                uniform_onvenue_in_window=bool(not in_window.empty and in_window["uniform_onvenue"].any()),
            )
        )
        episode_end = end
    return triggers
