"""Refresh FI per il caso zero (ADR-001, ADR-002): export incrementale + merge window-replace + ricostruzione canonica
in un DB separato (`data/fi_refreshed.sqlite`). Il DB pinnato del backtest non viene toccato."""

from __future__ import annotations

import gzip
import json
from datetime import date, datetime, timedelta, timezone

import pandas as pd

from .. import config, store
from ..canon.build import build_canonical
from . import bulk
from .fi_export import FiExportClient, HttpFetcher, merge_window_replace, user_agent
from .rawcsv import parse_register_csv

REFRESHED_DB = config.DATA_DIR / "fi_refreshed.sqlite"


def refresh(lookback_days: int, end: date | None = None, fetcher=None) -> dict:
    cfg = config.load()
    src, fe = cfg["source"], cfg["fi_export"]
    end = end or date.today()
    start = end - timedelta(days=lookback_days)
    data, snap = bulk.load(src["pinned_commit"])
    raw = parse_register_csv(data)

    fetch = fetcher or HttpFetcher(fe["base_url"], user_agent(fe["user_agent"]))
    client = FiExportClient(fetch, fe["pause_seconds"], fe["max_requests"], fe["row_cap"])
    parts = client.fetch_range(start, end)
    fi_rows = pd.concat([p.rows for p in parts], ignore_index=True) if parts else raw.rows.iloc[:0]
    fi_quarantine = pd.concat([p.quarantine for p in parts], ignore_index=True) if parts else raw.quarantine.iloc[:0]

    out_dir = config.RAW_DIR / "fi"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    with gzip.open(out_dir / f"{stamp}_{start}_{end}.csv.gz", "wt", encoding="utf-8") as f:
        fi_rows.to_csv(f, sep=";", index=False)
    (out_dir / f"{stamp}_fetchlog.json").write_text(json.dumps(client.log.requests, indent=2), encoding="utf-8")

    merged = merge_window_replace(raw.rows, fi_rows, start, end)
    fi_ids = set(fi_rows["record_id"])
    c = build_canonical(merged, "bulk", f"{snap.commit_sha[:10]}+fi{end}", src["stale_status_horizon"])
    c.df["source"] = c.df["record_id"].map(lambda r: "fi_export" if r in fi_ids else "bulk")
    if REFRESHED_DB.exists():
        REFRESHED_DB.unlink()
    store.save_frame("transactions", c.df, REFRESHED_DB)
    store.save_frame("quarantine", pd.concat([raw.quarantine, fi_quarantine], ignore_index=True), REFRESHED_DB)
    store.save_rules(c.rules, REFRESHED_DB)
    replaced = int(((pd.to_datetime(raw.rows["Publiceringsdatum"], errors="coerce").dt.normalize() >= pd.Timestamp(start))
                    & (pd.to_datetime(raw.rows["Publiceringsdatum"], errors="coerce").dt.normalize() <= pd.Timestamp(end))).sum())
    summary = {
        "window": [str(start), str(end)],
        "requests": len(client.log.requests),
        "fi_rows": int(len(fi_rows)),
        "bulk_rows_replaced": replaced,
        "rows_total": int(len(c.df)),
        "stale_inferred": int((c.df["chain_status"] == "superseded_inferred").sum()),
        "fi_quarantine": int(len(fi_quarantine)),
        "status_fi_rows": fi_rows["Status"].value_counts().to_dict(),
        "fetched_at": stamp,
    }
    store.save_meta("refresh", summary, REFRESHED_DB)
    return summary
