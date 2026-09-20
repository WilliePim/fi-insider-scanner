"""Revision chains and the status of every row (ADR-002, ADR-014).

The register carries no notification id. A correction (`Korrigering=Ja`) is linked one-to-one to the
previous version with the same issuer, person and trade date and a *strictly* earlier publication,
choosing the highest score over the fields and, on a tie, the most recent publication. A full tie ->
ambiguous, no link.

Stale upstream statuses: after `stale_status_horizon` a correction can have a predecessor still marked
`Aktuell`, because the civictech job never re-downloaded it. In that case, and only on a strong match
(same ISIN and same type), the row becomes `superseded_inferred`.

chain_status:
- current               Aktuell, not superseded
- superseded            Reviderad linked to a later version
- superseded_inferred   Aktuell superseded by a correction published after the horizon (STATUS_STALE_UPSTREAM)
- orphan_revised        Reviderad with no identifiable successor
- cancelled             Makulerad
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

SCORE_WEIGHTS = {"isin": 3, "instrument_name": 2, "txn_kind": 2, "volume": 1, "price": 1, "venue_raw": 1}
MIN_SCORE = 2
MIN_SCORE_STALE = 5  # ISIN + type


@dataclass
class ChainStats:
    corrections: int = 0
    linked: int = 0
    linked_stale: int = 0
    ambiguous: int = 0
    orphan_corrections: int = 0
    orphan_revised: int = 0
    links: pd.DataFrame = field(default_factory=pd.DataFrame)


def _score(c: pd.Series, cands: pd.DataFrame) -> pd.Series:
    total = pd.Series(0, index=cands.index)
    for col, w in SCORE_WEIGHTS.items():
        total += (cands[col] == c[col]).fillna(False).astype(int) * w
    return total


def build_chains(df: pd.DataFrame, stale_horizon: pd.Timestamp) -> tuple[pd.DataFrame, ChainStats]:
    df = df.copy()
    stats = ChainStats()
    status = df["status_raw"]
    is_corr = df["is_amendment"].eq(True) & status.isin(["Aktuell", "Reviderad"])
    stats.corrections = int(is_corr.sum())
    key = ["issuer_key", "name_key", "trade_date"]

    linked_to: dict[str, str] = {}
    successor_pub: dict[str, pd.Timestamp] = {}
    stale_linked: set[str] = set()
    link_rows = []

    corr_keys = df.loc[is_corr, key].drop_duplicates()
    pool = df.merge(corr_keys, on=key, how="inner")
    pool = pool[pool["status_raw"].isin(["Aktuell", "Reviderad"])]
    for _, grp in pool.groupby(key, sort=False, dropna=False):
        corrections = grp[grp["is_amendment"].eq(True)].sort_values("published_at", kind="stable")
        taken: set[str] = set()
        for _, c in corrections.iterrows():
            cands = grp[(grp["published_at"] < c["published_at"]) & ~grp["record_id"].isin(taken)]
            allowed_stale = c["published_at"] > stale_horizon
            cands = cands[(cands["status_raw"] == "Reviderad") | ((cands["status_raw"] == "Aktuell") & allowed_stale)]
            if cands.empty:
                stats.orphan_corrections += 1
                continue
            scores = _score(c, cands)
            is_stale = cands["status_raw"] == "Aktuell"
            ok = (scores >= MIN_SCORE) & (~is_stale | (scores >= MIN_SCORE_STALE))
            cands, scores = cands[ok], scores[ok]
            if cands.empty:
                stats.orphan_corrections += 1
                continue
            best = cands[scores == scores.max()]
            latest = best[best["published_at"] == best["published_at"].max()]
            if len(latest) > 1:
                stats.ambiguous += 1
                continue
            pred = latest.iloc[0]
            taken.add(pred["record_id"])
            linked_to[c["record_id"]] = pred["record_id"]
            successor_pub[pred["record_id"]] = c["published_at"]
            if pred["status_raw"] == "Aktuell":
                stale_linked.add(pred["record_id"])
            link_rows.append(
                {
                    "correction": c["record_id"],
                    "predecessor": pred["record_id"],
                    "predecessor_status": pred["status_raw"],
                    "lag_days": (c["published_at"] - pred["published_at"]).total_seconds() / 86400,
                    "score": int(scores.max()),
                    **{f"changed_{col}": bool(c[col] != pred[col]) for col in (*SCORE_WEIGHTS, "role_raw", "notifier_name", "currency")},
                    "note": c["amendment_note"],
                }
            )
    stats.linked = len(linked_to)
    stats.linked_stale = len(stale_linked)
    stats.links = pd.DataFrame(link_rows)

    rid = df["record_id"]
    chain_status = pd.Series("current", index=df.index, dtype="object")
    chain_status[status == "Makulerad"] = "cancelled"
    chain_status[status == "Reviderad"] = "orphan_revised"
    chain_status[rid.isin(successor_pub.keys()) & (status == "Reviderad")] = "superseded"
    chain_status[rid.isin(stale_linked)] = "superseded_inferred"
    stats.orphan_revised = int((chain_status == "orphan_revised").sum())

    superseded: dict[str, pd.Timestamp] = dict(successor_pub)
    # orphan Reviderad rows: visibility ends at the next correction by the same person
    # for the same issuer; without one, they are never visible in as_seen
    orphans = df[chain_status == "orphan_revised"]
    if not orphans.empty:
        corr_pub = df.loc[is_corr, ["issuer_key", "name_key", "published_at"]].sort_values("published_at")
        by_person = {k: g["published_at"].to_numpy() for k, g in corr_pub.groupby(["issuer_key", "name_key"])}
        for rec, issuer, person, pub in zip(
            orphans["record_id"], orphans["issuer_key"], orphans["name_key"], orphans["published_at"], strict=True
        ):
            arr = by_person.get((issuer, person))
            later = None
            if arr is not None:
                pos = int(arr.searchsorted(pub.to_datetime64(), side="right"))
                later = pd.Timestamp(arr[pos]) if pos < len(arr) else None
            superseded[rec] = later if later is not None else pub
    superseded_at = pd.to_datetime(pd.Series([superseded.get(r) for r in rid], index=df.index, dtype="object"))

    pub_by_id = dict(zip(rid, df["published_at"], strict=True))
    first_pub = {}
    for r in rid:
        seen, cur, earliest = set(), r, pub_by_id[r]
        while cur in linked_to and cur not in seen:
            seen.add(cur)
            cur = linked_to[cur]
            earliest = min(earliest, pub_by_id[cur])
        first_pub[r] = earliest

    flags = pd.Series("", index=df.index, dtype="object")
    flags[rid.isin(stale_linked)] = "STATUS_STALE_UPSTREAM"
    orphan_corr_ids = set(df.loc[is_corr, "record_id"]) - set(linked_to)
    flags[rid.isin(orphan_corr_ids)] = "ORPHAN_CORRECTION"

    df["chain_status"] = chain_status
    df["linked_to"] = pd.Series([linked_to.get(r) for r in rid], index=df.index, dtype="object")
    df["superseded_at"] = superseded_at
    df["first_published_at"] = pd.to_datetime(pd.Series([first_pub[r] for r in rid], index=df.index, dtype="object"))
    df["chain_flags"] = flags
    return df, stats
