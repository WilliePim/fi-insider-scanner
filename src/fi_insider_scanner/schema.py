"""Schema canonico di una riga del registro (contratto Pydantic).

Campi derivati da più righe (issuer_key, tipo inferito, catene) sono aggiunti dopo,
a livello di dataset, e documentati in `canon/mapping.py`.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from .canon.taxonomy import InstrumentType, TxnKind, VenueClass


class Transaction(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    record_id: str
    source: Literal["bulk", "fi_export"]
    snapshot_id: str

    published_at: datetime
    issuer_name_raw: str
    issuer_lei: str | None
    lei_checksum_ok: bool

    notifier_name: str
    pdmr_name: str
    name_key: str
    associate_kind: Literal["self", "vehicle", "family"]
    pdmr_is_natural_person: bool | None
    role_raw: str
    roles: tuple[str, ...]

    is_closely_associated: bool | None
    is_amendment: bool | None
    amendment_note: str | None
    is_initial: bool | None
    is_share_program: bool | None

    nature_raw: str
    txn_kind: TxnKind
    direction: int

    instrument_type_raw: str | None
    instrument_type_reported: InstrumentType | None
    instrument_name: str
    isin: str | None
    isin_valid: bool
    share_class: str | None
    is_pref: bool
    is_sdr: bool

    trade_date: date | None
    volume: float | None
    volume_unit: Literal["antal", "belopp"] | None
    price: float | None
    currency: str | None
    venue_raw: str
    venue_class: VenueClass

    status_raw: Literal["Aktuell", "Reviderad", "Makulerad"] | None
    parse_errors: tuple[str, ...]


# Colonne aggiunte a livello di dataset (vedi canon/mapping.py e canon/chains.py).
DERIVED_COLUMNS = (
    "issuer_key",
    "issuer_key_source",
    "instrument_type",
    "type_source",
    "type_conflict",
    "chain_status",
    "linked_to",
    "superseded_at",
    "first_published_at",
    "chain_flags",
)
