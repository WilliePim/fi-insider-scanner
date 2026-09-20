"""Structural subscription (ADR-017).

- S1: Teckning rows of the issuer inside the window -> subscription context (flag)
- S2: activity on BTA/BTU/rights/interim instruments -> issue context (flag)
- S3: at least 3 distinct persons with a base purchase on the same date at the same price, AND
      (at least one off-venue row OR a Teckning or issue instrument visible at the same price within
      20 days) -> a structural subscription: score 0, and those rows stay out of B.
  The same on-venue price with no evidence of an issue -> only the UNIFORM_PRICE_ONVENUE flag.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..canon.taxonomy import ISSUE_INSTRUMENTS, TxnKind
from .openmarket import OFF_VENUE_CLASSES, base_purchase

BOARD_ROLES = {"board", "chair", "deputy_board"}
_ISSUE = {str(i) for i in ISSUE_INSTRUMENTS}


def issue_rows(v: pd.DataFrame) -> pd.DataFrame:
    return v[v["txn_kind"].eq(str(TxnKind.SUBSCRIPTION)) | v["instrument_type"].isin(_ISSUE)]


def uniform_price_groups(v: pd.DataFrame, min_persons: int, price_window_days: int) -> pd.DataFrame:
    """Groups (date, price, currency) with at least min_persons persons; columns s3, uniform_onvenue, all_board, record_ids."""
    acq = v[base_purchase(v)]
    cols = [
        "trade_date",
        "price",
        "currency",
        "n_persons",
        "off_venue",
        "issue_evidence",
        "s3",
        "uniform_onvenue",
        "all_board",
        "record_ids",
    ]
    if acq.empty:
        return pd.DataFrame(columns=cols)
    issues = issue_rows(v)
    window = pd.Timedelta(days=price_window_days)
    rows = []
    for (day, price, ccy), grp in acq.groupby(["trade_date", "price", "currency"], dropna=False):
        persons = grp["person_key"].nunique()
        if persons < min_persons:
            continue
        off = bool(grp["venue_class"].isin(OFF_VENUE_CLASSES).any())
        near = issues[(issues["trade_date"] - day).abs() <= window]
        evidence = bool(np.isclose(near["price"].astype(float), float(price), rtol=0, atol=1e-9).any()) if not near.empty else False
        board = all(set(r) and set(r) <= BOARD_ROLES for r in grp["roles"])
        rows.append((day, price, ccy, persons, off, evidence, off or evidence, not (off or evidence), board, tuple(grp["record_id"])))
    return pd.DataFrame(rows, columns=cols)


def context_flags(v: pd.DataFrame, window_start: pd.Timestamp, window_end: pd.Timestamp) -> dict:
    issues = issue_rows(v)
    in_window = issues[(issues["trade_date"] >= window_start) & (issues["trade_date"] <= window_end)]
    return {
        "s1_subscription": bool(in_window["txn_kind"].eq(str(TxnKind.SUBSCRIPTION)).any()),
        "s2_issue_instruments": bool(in_window["instrument_type"].isin(_ISSUE).any()),
    }
