"""Persistenza delle tabelle canoniche in SQLite (stdlib)."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pandas as pd

from . import config
from .canon.names import MergeRule

_TUPLE_COLS = ("roles", "parse_errors")
_DATETIME_COLS = ("published_at", "trade_date", "superseded_at", "first_published_at")


def _connect(path: Path | None = None) -> sqlite3.Connection:
    path = path or config.DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    # Più processi (resolve, dry-run) possono scrivere: attesa lunga sul lock invece di fallire.
    return sqlite3.connect(path, timeout=120)


def save_frame(name: str, df: pd.DataFrame, path: Path | None = None) -> None:
    out = df.copy()
    for col in _TUPLE_COLS:
        if col in out:
            out[col] = out[col].map(lambda t: "|".join(t) if isinstance(t, (tuple, list)) else t)
    for col in out.columns:
        if pd.api.types.is_datetime64_any_dtype(out[col]):
            out[col] = out[col].dt.strftime("%Y-%m-%d %H:%M:%S").where(out[col].notna(), None)
    with _connect(path) as con:
        out.to_sql(name, con, if_exists="replace", index=False)


def load_frame(name: str, path: Path | None = None) -> pd.DataFrame:
    with _connect(path) as con:
        df = pd.read_sql(f"SELECT * FROM {name}", con)
    for col in _TUPLE_COLS:
        if col in df:
            df[col] = df[col].map(lambda s: tuple(s.split("|")) if isinstance(s, str) and s else ())
    for col in _DATETIME_COLS:
        if col in df:
            df[col] = pd.to_datetime(df[col])
    for col in ("is_closely_associated", "is_amendment", "is_initial", "is_share_program"):
        if col in df:
            df[col] = df[col].map(lambda v: None if v is None or pd.isna(v) else bool(v))
    for col in ("isin_valid", "lei_checksum_ok", "is_pref", "is_sdr", "type_conflict"):
        if col in df:
            df[col] = df[col].astype(bool)
    return df


def save_rules(rules: list[MergeRule], path: Path | None = None) -> None:
    rows = [
        {
            "issuer_key": r.issuer_key,
            "long_key": r.long_key,
            "short_key": r.short_key,
            "valid_from": r.valid_from,
            "valid_until": r.valid_until,
        }
        for r in rules
    ]
    save_frame("merge_rules", pd.DataFrame(rows, columns=["issuer_key", "long_key", "short_key", "valid_from", "valid_until"]), path)


def load_rules(path: Path | None = None) -> list[MergeRule]:
    df = load_frame("merge_rules", path)
    return [
        MergeRule(r.issuer_key, r.long_key, r.short_key, pd.Timestamp(r.valid_from), None if r.valid_until is None or pd.isna(r.valid_until) else pd.Timestamp(r.valid_until))
        for r in df.itertuples()
    ]


def save_meta(key: str, value: dict, path: Path | None = None) -> None:
    with _connect(path) as con:
        con.execute("CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT)")
        con.execute("INSERT OR REPLACE INTO meta VALUES (?, ?)", (key, json.dumps(value, default=str)))


def load_meta(key: str, path: Path | None = None) -> dict | None:
    with _connect(path) as con:
        con.execute("CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT)")
        row = con.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
    return json.loads(row[0]) if row else None
