"""Identità delle persone: normalizzazione, riconoscimento entità, merge conservativo.

Regole (ADR-009):
- chiave = NFKC, spazi speciali, spazi compressi, casefold; "Cognome, Nome" -> "nome cognome";
- un nome con token societari (AB, Ltd, Holding, Stiftelse…) non è una persona fisica;
- merge solo nello stesso emittente: stesso primo e ultimo token, un solo nome breve
  (2 token) e una sola variante lunga; più varianti lunghe -> ambiguo, nessun merge;
- il merge vale dal momento in cui entrambe le forme sono visibili e smette di valere
  quando compare una seconda variante lunga (point-in-time);
- nomi uguali a meno dei diacritici: solo flag, mai merge.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

import pandas as pd

_ENTITY_TOKENS = {
    "ab", "aktiebolag", "(publ)", "publ", "as", "asa", "a/s", "aps", "oy", "oyj", "ltd", "ltd.", "limited",
    "llc", "lp", "llp", "inc", "inc.", "corp", "corp.", "corporation", "gmbh", "ag", "bv", "b.v.", "nv", "n.v.",
    "sa", "s.a.", "sas", "sarl", "s.à", "s.a.r.l.", "plc", "holding", "holdings", "invest", "investment",
    "investments", "investering", "capital", "förvaltning", "fastighet", "fastigheter", "fastighets",
    "stiftelse", "stiftelsen", "foundation", "trust", "fund", "fond", "fonder", "partners", "kb", "hb",
    "group", "kommanditbolag", "handelsbolag", "consulting", "management", "ventures", "equity",
    "pensionskassa", "försäkring", "försäkringsaktiebolag", "bank", "vinstandelsstiftelse", "förening",
    "ekonomisk", "trading", "konsult", "estate", "company", "co", "co.", "family", "kapital", "invest.",
    "aktiebolaget", "bolag", "holdco", "sicav", "gp", "lda", "srl", "spa", "s.p.a.", "pty", "bhd",
}
_ENTITY_SUBSTRINGS = ("stiftelse", "förvaltning", "fastighet", "aktiebolag", "vinstandels", "holding", "invest ab")


def _nfkc(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "")
    s = s.replace(" ", " ").replace(" ", " ")
    return re.sub(r"\s+", " ", s).strip()


def normalize_name(name: str | None) -> str:
    s = _nfkc(name or "")
    if s.count(",") == 1 and not is_entity(s):
        last, first = (p.strip() for p in s.split(","))
        if last and first and " " not in last:
            s = f"{first} {last}"
    return s.casefold()


def ascii_fold(key: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", key) if not unicodedata.combining(c))


def is_entity(name: str | None) -> bool:
    s = _nfkc(name or "").casefold()
    if not s:
        return False
    tokens = re.split(r"[\s,]+", s)
    if any(t in _ENTITY_TOKENS for t in tokens):
        return True
    return any(sub in s for sub in _ENTITY_SUBSTRINGS)


def is_natural_person(name: str | None) -> bool | None:
    s = _nfkc(name or "")
    if not s or is_entity(s):
        return False
    if len(s.split(" ")) < 2:
        return None
    return True


def associate_kind(notifier: str | None, pdmr: str | None) -> str:
    if normalize_name(notifier) == normalize_name(pdmr):
        return "self"
    return "vehicle" if is_entity(notifier) else "family"


@dataclass(frozen=True)
class MergeRule:
    issuer_key: str
    long_key: str
    short_key: str
    valid_from: pd.Timestamp
    valid_until: pd.Timestamp | None  # esclusivo; None = sempre valido dopo valid_from


def build_merge_rules(names: pd.DataFrame) -> tuple[list[MergeRule], pd.DataFrame]:
    """`names`: colonne issuer_key, name_key, first_seen (prima pubblicazione visibile).

    Restituisce le regole di merge e un DataFrame di flag (NAME_AMBIGUOUS, NEAR_DUP_NAME).
    """
    rules: list[MergeRule] = []
    flags: list[dict] = []
    df = names.dropna(subset=["name_key"]).copy()
    df["tokens"] = df["name_key"].str.split(" ")
    df = df[df["tokens"].str.len() >= 2]
    df["first_tok"] = df["tokens"].str[0]
    df["last_tok"] = df["tokens"].str[-1]
    for (issuer, first, last), grp in df.groupby(["issuer_key", "first_tok", "last_tok"], sort=False):
        if len(grp) < 2:
            continue
        shorts = grp[grp["tokens"].str.len() == 2]
        longs = grp[grp["tokens"].str.len() > 2].sort_values("first_seen")
        if len(shorts) != 1 or longs.empty:
            continue
        short = shorts.iloc[0]
        first_long = longs.iloc[0]
        valid_from = max(short["first_seen"], first_long["first_seen"])
        valid_until = longs.iloc[1]["first_seen"] if len(longs) > 1 else None
        rules.append(MergeRule(issuer, first_long["name_key"], short["name_key"], valid_from, valid_until))
        if len(longs) > 1:
            flags.append({"issuer_key": issuer, "name_key": short["name_key"], "flag": "NAME_AMBIGUOUS",
                          "detail": "; ".join(longs["name_key"]), "from": valid_until})
    df["folded"] = df["name_key"].map(ascii_fold)
    for (issuer, folded), grp in df.groupby(["issuer_key", "folded"], sort=False):
        if grp["name_key"].nunique() > 1:
            flags.append({"issuer_key": issuer, "name_key": folded, "flag": "NEAR_DUP_NAME",
                          "detail": "; ".join(sorted(grp["name_key"].unique())), "from": grp["first_seen"].max()})
    return rules, pd.DataFrame(flags, columns=["issuer_key", "name_key", "flag", "detail", "from"])


def apply_merges(issuer_key: pd.Series, name_key: pd.Series, as_of: pd.Timestamp, rules: list[MergeRule]) -> pd.Series:
    """person_key al tempo `as_of`: applica solo le regole valide in quell'istante."""
    active = {
        (r.issuer_key, r.long_key): r.short_key
        for r in rules
        if r.valid_from <= as_of and (r.valid_until is None or as_of < r.valid_until)
    }
    if not active:
        return name_key.copy()
    return pd.Series(
        [active.get((i, n), n) for i, n in zip(issuer_key, name_key)], index=name_key.index, dtype="object"
    )
