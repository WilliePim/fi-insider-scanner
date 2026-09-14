"""Classe azioni da `Instrumentnamn`. L'identità dello strumento resta l'ISIN."""

from __future__ import annotations

import re
from dataclasses import dataclass

_SDR = re.compile(r"\b(sdb|sdr)\b|depåbevis", re.IGNORECASE)
_PREF = re.compile(r"\bpref\b|\bpreferens(aktie)?\b|\bpreference\b", re.IGNORECASE)
_TYPE_HINTS = [
    ("BTA", re.compile(r"\bBTA\b", re.IGNORECASE)),
    ("BTU", re.compile(r"\bBTU\b", re.IGNORECASE)),
    ("TO", re.compile(r"\bTO\s?\d+\b", re.IGNORECASE)),
    ("TR", re.compile(r"\bTR\b", re.IGNORECASE)),
]
_SERIES = re.compile(r"\bser(?:ie)?\.?\s*([A-D])\b", re.IGNORECASE)
_CLASS = re.compile(r"\b(?:class|klass)\s*([A-D])\b", re.IGNORECASE)
_LETTER_AKTIE = re.compile(r"\b([A-D])[- ]aktie", re.IGNORECASE)
_TRAILING = re.compile(r"(?:^|\s)([A-D])$")


@dataclass(frozen=True)
class ShareClassInfo:
    share_class: str | None
    is_pref: bool
    is_sdr: bool
    type_hint: str | None


def parse_share_class(name: str | None) -> ShareClassInfo:
    text = re.sub(r"\s+", " ", (name or "").replace(" ", " ")).strip()
    is_sdr = bool(_SDR.search(text))
    is_pref = bool(_PREF.search(text))
    hint = next((h for h, rx in _TYPE_HINTS if rx.search(text)), None)
    share_class = None
    for rx in (_SERIES, _CLASS, _LETTER_AKTIE):
        m = rx.search(text)
        if m:
            share_class = m.group(1).upper()
            break
    if share_class is None:
        stripped = _SDR.sub("", text)
        stripped = _PREF.sub("", stripped)
        for _, rx in _TYPE_HINTS:
            stripped = rx.sub("", stripped)
        stripped = re.sub(r"\s+", " ", stripped).strip(" ,.-")
        m = _TRAILING.search(stripped)
        # Una lettera finale in maiuscolo dopo almeno una parola (evita "AB" e simili).
        if m and len(stripped) > 2 and stripped[-1].isupper():
            share_class = m.group(1)
    return ShareClassInfo(share_class=share_class, is_pref=is_pref, is_sdr=is_sdr, type_hint=hint)
