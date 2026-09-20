"""Building the full canonical table from the raw rows."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .chains import ChainStats, build_chains
from .mapping import assign_issuer_keys, infer_instrument_types, map_rows
from .names import MergeRule, build_merge_rules


@dataclass
class Canonical:
    df: pd.DataFrame
    rejects: pd.DataFrame
    chain_stats: ChainStats
    rules: list[MergeRule]
    name_flags: pd.DataFrame


def build_canonical(raw_rows: pd.DataFrame, source: str, snapshot_id: str, stale_horizon: str) -> Canonical:
    df, rejects = map_rows(raw_rows, source, snapshot_id)
    df = assign_issuer_keys(df)
    df = infer_instrument_types(df)
    df, stats = build_chains(df, pd.Timestamp(stale_horizon))
    persons = df[df["pdmr_is_natural_person"].eq(True)]
    names = persons.groupby(["issuer_key", "name_key"], as_index=False)["published_at"].min()
    names = names.rename(columns={"published_at": "first_seen"})
    rules, flags = build_merge_rules(names)
    return Canonical(df=df, rejects=rejects, chain_stats=stats, rules=rules, name_flags=flags)
