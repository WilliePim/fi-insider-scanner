"""Riga grezza -> `Transaction`, poi passi a livello di dataset.

Passi di dataset (ognuno con la sua fonte registrata):
1. `issuer_key`: LEI; altrimenti LEI univoco delle altre righe con lo stesso ISIN; altrimenti
   LEI univoco delle righe con lo stesso nome normalizzato; altrimenti `name:<nome>`.
2. `instrument_type`: dichiarato; altrimenti tipo univoco dello stesso ISIN; altrimenti regola
   sul nome; altrimenti nome dello strumento che richiama l'emittente (-> azione); altrimenti None.
3. catene di revisione (`canon/chains.py`).
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from functools import lru_cache

import pandas as pd
from pydantic import ValidationError

from ..schema import Transaction
from . import names as nm
from .parse import currency_code, isin_valid, ja_flag, lei_valid, parse_date, parse_datetime, parse_decimal
from .shareclass import parse_share_class
from .taxonomy import InstrumentType, direction, instrument_type, instrument_type_from_name, roles, txn_kind, venue_class

_LEI_FORMAT = re.compile(r"^[A-Z0-9]{18}[0-9]{2}$")
_UNITS = {"Antal": "antal", "Belopp": "belopp", "Quantity": "antal", "Amount": "belopp"}

_kind = lru_cache(maxsize=None)(txn_kind)
_venue = lru_cache(maxsize=None)(venue_class)
_roles = lru_cache(maxsize=None)(roles)
_itype = lru_cache(maxsize=None)(instrument_type)
_sclass = lru_cache(maxsize=None)(parse_share_class)
_name_key = lru_cache(maxsize=None)(nm.normalize_name)
_natural = lru_cache(maxsize=None)(nm.is_natural_person)
_assoc = lru_cache(maxsize=None)(nm.associate_kind)


def map_row(raw: Mapping[str, str], source: str, snapshot_id: str) -> Transaction:
    errors: list[str] = []

    def text(col: str) -> str:
        v = raw.get(col)
        return "" if v is None or (isinstance(v, float) and pd.isna(v)) else str(v)

    def flag(col: str) -> bool | None:
        value = ja_flag(text(col))
        if value is None:
            errors.append(f"FLAG:{col}={text(col)!r}")
        return value

    def number(col: str) -> float | None:
        value = parse_decimal(text(col))
        if value is None and text(col):
            errors.append(f"NUMBER:{col}={text(col)!r}")
        return value

    published_at = parse_datetime(text("Publiceringsdatum"))
    if published_at is None:
        raise ValueError(f"Publiceringsdatum non interpretabile: {text('Publiceringsdatum')!r}")

    lei = text("LEI-kod") or None
    if lei and not _LEI_FORMAT.match(lei):
        errors.append(f"LEI_FORMAT:{lei!r}")
    isin = text("ISIN") or None
    status_text = text("Status")
    status = status_text if status_text in ("Aktuell", "Reviderad", "Makulerad") else {"Current": "Aktuell", "Revised": "Reviderad"}.get(status_text)
    if status is None:
        errors.append(f"STATUS:{status_text!r}")
    currency = currency_code(text("Valuta"))
    if currency is None and text("Valuta"):
        errors.append(f"CURRENCY_JUNK:{text('Valuta')!r}")
    trade_date = parse_date(text("Transaktionsdatum"))
    if trade_date is None and text("Transaktionsdatum"):
        errors.append(f"DATE:Transaktionsdatum={text('Transaktionsdatum')!r}")
    unit = _UNITS.get(text("Volymsenhet"))
    if unit is None and text("Volymsenhet"):
        errors.append(f"UNIT:{text('Volymsenhet')!r}")

    is_amendment = flag("Korrigering")
    is_initial = flag("Är förstagångsrapportering")
    if is_amendment is not None and is_initial is not None and is_amendment == is_initial:
        errors.append("KORRIGERING_INVARIANT_VIOLATION")

    kind = _kind(text("Karaktär"))
    itype_raw = text("Instrumenttyp") or None
    itype = _itype(itype_raw) if itype_raw else None
    if itype_raw and itype is None:
        errors.append(f"INSTRUMENT_TYPE_UNMAPPED:{itype_raw!r}")
    sclass = _sclass(text("Instrumentnamn"))
    pdmr = text("Person i ledande ställning")
    notifier = text("Anmälningsskyldig")

    return Transaction(
        record_id=text("record_id"),
        source=source,
        snapshot_id=snapshot_id,
        published_at=published_at,
        issuer_name_raw=text("Emittent"),
        issuer_lei=lei,
        lei_checksum_ok=lei_valid(lei),
        notifier_name=notifier,
        pdmr_name=pdmr,
        name_key=_name_key(pdmr),
        associate_kind=_assoc(notifier, pdmr) if notifier else "self",
        pdmr_is_natural_person=_natural(pdmr),
        role_raw=text("Befattning"),
        roles=tuple(sorted(_roles(text("Befattning")))),
        is_closely_associated=flag("Närstående"),
        is_amendment=is_amendment,
        amendment_note=text("Beskrivning av korrigering") or None,
        is_initial=is_initial,
        is_share_program=flag("Är kopplad till aktieprogram"),
        nature_raw=text("Karaktär"),
        txn_kind=kind,
        direction=direction(kind),
        instrument_type_raw=itype_raw,
        instrument_type_reported=itype,
        instrument_name=text("Instrumentnamn"),
        isin=isin,
        isin_valid=isin_valid(isin),
        share_class=sclass.share_class,
        is_pref=sclass.is_pref,
        is_sdr=sclass.is_sdr,
        trade_date=trade_date,
        volume=number("Volym"),
        volume_unit=unit,
        price=number("Pris"),
        currency=currency,
        venue_raw=text("Handelsplats"),
        venue_class=_venue(text("Handelsplats")),
        status_raw=status,
        parse_errors=tuple(errors),
    )


def map_rows(raw_rows: pd.DataFrame, source: str, snapshot_id: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    mapped, rejects = [], []
    for rec in raw_rows.to_dict("records"):
        try:
            mapped.append(map_row(rec, source, snapshot_id).model_dump())
        except (ValueError, ValidationError) as exc:
            rejects.append({"record_id": rec.get("record_id"), "error": str(exc)[:300]})
    df = pd.DataFrame(mapped)
    df["published_at"] = pd.to_datetime(df["published_at"])
    df["trade_date"] = pd.to_datetime(df["trade_date"])
    # pandas 3 memorizza i None delle colonne stringa come NaN: mai convertirli in "nan".
    for col in ("txn_kind", "venue_class", "instrument_type_reported"):
        df[col] = pd.Series([None if v is None or (isinstance(v, float) and pd.isna(v)) else str(v) for v in df[col]], index=df.index, dtype="object")
    return df, pd.DataFrame(rejects, columns=["record_id", "error"])


# --- issuer_key ----------------------------------------------------------------------------

_ISSUER_NOISE = re.compile(r"\(publ\)|\bpubl\b|\baktiebolag(et)?\b|\bab\b|[^\w\s]", re.IGNORECASE)


def normalize_issuer_name(name: str | None) -> str:
    s = _ISSUER_NOISE.sub(" ", (name or "").casefold())
    return re.sub(r"\s+", " ", s).strip()


def _unique_or_none(s: pd.Series):
    u = s.dropna().unique()
    return u[0] if len(u) == 1 else None


def assign_issuer_keys(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    lei_ok = df["issuer_lei"].fillna("").str.match(_LEI_FORMAT)
    df["_iname"] = df["issuer_name_raw"].map(normalize_issuer_name)
    with_lei = df[lei_ok]
    by_isin = with_lei[with_lei["isin"].notna()].groupby("isin")["issuer_lei"].agg(_unique_or_none)
    by_name = with_lei.groupby("_iname")["issuer_lei"].agg(_unique_or_none)
    key = df["issuer_lei"].where(lei_ok)
    source = pd.Series(["lei" if ok else None for ok in lei_ok], index=df.index, dtype="object")
    from_isin = df["isin"].map(by_isin).where(key.isna())
    source = source.where(~(key.isna() & from_isin.notna()), "isin_backfill")
    key = key.fillna(from_isin)
    from_name = df["_iname"].map(by_name).where(key.isna())
    source = source.where(~(key.isna() & from_name.notna()), "name_backfill")
    key = key.fillna(from_name)
    source = source.where(key.notna(), "name")
    key = key.fillna("name:" + df["_iname"])
    df["issuer_key"] = key
    df["issuer_key_source"] = source
    return df.drop(columns="_iname")


# --- instrument_type ----------------------------------------------------------------------

_DERIVATIVE_WORDS = re.compile(
    r"option|teckning|\bto\b|\bto\d|\btr\b|\bbta\b|\bbtu\b|konvert|obligation|warrant|lån|bond|\bkv\b|swap|termin|cfd|"
    r"certifikat|inlösen|\bir\b|\bia\b|\bur\b|rätt",
    re.IGNORECASE,
)


def _significant_tokens(text: str) -> list[str]:
    return [t for t in normalize_issuer_name(text).split() if len(t) >= 3 and t not in {"the", "group", "holding"}]


def looks_like_issuer_share(instrument_name: str, issuer_name: str) -> bool:
    if not instrument_name or _DERIVATIVE_WORDS.search(instrument_name):
        return False
    if parse_share_class(instrument_name).share_class is not None:
        return True
    inst, iss = _significant_tokens(instrument_name), _significant_tokens(issuer_name)
    return bool(inst and iss and inst[0][:5] == iss[0][:5])


def _present(value) -> bool:
    return value is not None and not (isinstance(value, float) and pd.isna(value)) and value != ""


ISIN_MAJORITY_SHARE = 0.90


def infer_instrument_types(df: pd.DataFrame) -> pd.DataFrame:
    """Livelli: reported -> isin_rows (unanime) -> isin_majority (>= 90%) -> name_rule -> issuer_name_match -> none.

    Un ISIN tipizzato in modo discordante dai dichiaranti (es. 95% Aktie, 5% Option) prende il
    tipo dominante solo se copre almeno il 90% delle righe tipizzate; altrimenti null + conflitto.
    """
    from collections import Counter

    df = df.copy()
    reported = list(df["instrument_type_reported"])
    isins = list(df["isin"])
    typed: dict[str, Counter] = {}
    for isin, t in zip(isins, reported):
        if _present(isin) and _present(t):
            typed.setdefault(isin, Counter())[t] += 1

    name_cache: dict[str, str | None] = {}
    types, sources, conflicts = [], [], []
    for t, isin, name, issuer, valid in zip(reported, isins, df["instrument_name"], df["issuer_name_raw"], df["isin_valid"]):
        if _present(t):
            types.append(t), sources.append("reported"), conflicts.append(False)
            continue
        known = typed.get(isin) if _present(isin) else None
        if known is not None:
            top, count = known.most_common(1)[0]
            share = count / sum(known.values())
            if len(known) == 1:
                types.append(top), sources.append("isin_rows"), conflicts.append(False)
            elif share >= ISIN_MAJORITY_SHARE:
                types.append(top), sources.append("isin_majority"), conflicts.append(False)
            else:
                types.append(None), sources.append("none"), conflicts.append(True)
            continue
        if name not in name_cache:
            rule = instrument_type_from_name(name)
            name_cache[name] = None if rule is None else str(rule)
        if name_cache[name] is not None:
            types.append(name_cache[name]), sources.append("name_rule"), conflicts.append(False)
        elif bool(valid) and looks_like_issuer_share(name or "", issuer or ""):
            types.append(str(InstrumentType.SHARE)), sources.append("issuer_name_match"), conflicts.append(False)
        else:
            types.append(None), sources.append("none"), conflicts.append(False)

    df["instrument_type"] = pd.Series(types, index=df.index, dtype="object")
    df["type_source"] = pd.Series(sources, index=df.index, dtype="object")
    df["type_conflict"] = pd.Series(conflicts, index=df.index, dtype=bool)
    return df
