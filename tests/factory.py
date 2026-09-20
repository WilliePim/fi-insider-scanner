"""Costruttori di righe canoniche sintetiche per i test dei gate."""

from __future__ import annotations

import itertools

import pandas as pd

from fi_insider_scanner.canon.visibility import Register

_ids = itertools.count()
T = pd.Timestamp


def txn(
    person: str = "anna svensson",
    trade: str = "2020-03-02",
    pub: str | None = None,
    *,
    issuer: str = "LEI1",
    kind: str = "acq_purchase",
    itype: str | None = "share",
    price: float = 10.0,
    volume: float = 10000.0,
    unit: str = "antal",
    venue: str = "xsto",
    program: bool | None = False,
    natural: bool | None = True,
    roles: tuple[str, ...] = ("board",),
    currency: str = "SEK",
    isin: str = "SE0000108656",
    value_usd: float | None = None,
    direction: int | None = None,
    status: str = "current",
    superseded_at: str | None = None,
) -> dict:
    trade_ts = T(trade)
    pub_ts = T(pub) if pub else trade_ts + pd.Timedelta(days=1, hours=9)
    value_sek = price * volume
    return {
        "record_id": f"r{next(_ids)}",
        "published_at": pub_ts,
        "first_published_at": pub_ts,
        "issuer_key": issuer,
        "name_key": person,
        "pdmr_name": person.title(),
        "pdmr_is_natural_person": natural,
        "trade_date": trade_ts,
        "txn_kind": kind,
        "direction": direction
        if direction is not None
        else (1 if kind in ("acq_purchase", "subscription", "grant", "exercise_in") else -1),
        "instrument_type": itype,
        "is_share_program": program,
        "price": price,
        "volume": volume,
        "volume_unit": unit,
        "venue_class": venue,
        "currency": currency,
        "roles": roles,
        "isin": isin,
        "value_sek": value_sek,
        "value_usd": value_usd if value_usd is not None else value_sek / 10.0,
        "chain_status": status,
        "superseded_at": T(superseded_at) if superseded_at else pd.NaT,
    }


def frame(rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    df["superseded_at"] = pd.to_datetime(df["superseded_at"])
    return df


def register(rows: list[dict], **kwargs) -> Register:
    return Register(frame(rows), **kwargs)


def visible_all(rows: list[dict], as_of: str = "2099-01-01", issuer: str = "LEI1") -> pd.DataFrame:
    return register(rows).visible(T(as_of), issuer)
