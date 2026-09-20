"""Parsing of the register CSV (civictech bulk or FI export) into raw 22-field rows.

No value is interpreted here: only structure, cleanup of the special spaces, record identity and
quarantine of the broken records that cannot be recomposed unambiguously.

Known breakages (ADR-004):
- short record (< 22 fields): an unquoted newline split the line;
- "shifted" 22-field record (civictech bulk, Biovica 2018 and 2020): one half has the fields
  Transaktionsdatum..Status empty, the other has Publiceringsdatum empty and the seven trailing values
  written into fields 1..7.
Only a truncated record followed *immediately* by its continuation is recomposed.
"""

from __future__ import annotations

import csv
import hashlib
import io
import re
from collections import Counter
from dataclasses import dataclass, field

import pandas as pd

EXPECTED_HEADER: tuple[str, ...] = (
    "Publiceringsdatum",
    "Emittent",
    "LEI-kod",
    "Anmälningsskyldig",
    "Person i ledande ställning",
    "Befattning",
    "Närstående",
    "Korrigering",
    "Beskrivning av korrigering",
    "Är förstagångsrapportering",
    "Är kopplad till aktieprogram",
    "Karaktär",
    "Instrumenttyp",
    "Instrumentnamn",
    "ISIN",
    "Transaktionsdatum",
    "Volym",
    "Volymsenhet",
    "Pris",
    "Valuta",
    "Handelsplats",
    "Status",
)
N_FIELDS = len(EXPECTED_HEADER)
TAIL_START = EXPECTED_HEADER.index("Transaktionsdatum")
TAIL_LEN = N_FIELDS - TAIL_START

_SPACE_CHARS = {" ": " ", " ": " ", " ": " ", "\r": " ", "\n": " ", "\t": " "}
_DT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}( \d{2}:\d{2}:\d{2})?$")


class SchemaDriftError(ValueError):
    """The header does not match the 22 expected columns."""


@dataclass
class RawParseResult:
    rows: pd.DataFrame
    quarantine: pd.DataFrame
    header: list[str]
    encoding: str
    had_bom: bool
    physical_records: int
    repairs: Counter = field(default_factory=Counter)


def clean_field(value: str) -> str:
    for bad, good in _SPACE_CHARS.items():
        if bad in value:
            value = value.replace(bad, good)
    return value.strip()


def decode(data: bytes) -> tuple[str, str, bool]:
    """UTF-16 (FI export, normally LE without BOM) or UTF-8 with or without BOM (bulk)."""
    if data[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return data.decode("utf-16"), "utf-16", True
    if len(data) >= 4 and data[1:2] == b"\x00" and data[3:4] == b"\x00":
        return data.decode("utf-16-le"), "utf-16-le", False
    if data.startswith(b"\xef\xbb\xbf"):
        return data[3:].decode("utf-8"), "utf-8-sig", True
    return data.decode("utf-8"), "utf-8", False


def _strip_trailing_empty(fields: list[str]) -> list[str]:
    # the FI export ends every line with ';' -> 23 fields, the last one empty
    if len(fields) == N_FIELDS + 1 and fields[-1].strip() == "":
        return fields[:-1]
    return fields


def record_ids(tuples: list[tuple[str, ...]]) -> list[str]:
    """sha256 of the 22 cleaned fields plus the occurrence index among identical tuples."""
    seen: Counter = Counter()
    out = []
    for t in tuples:
        digest = hashlib.sha256("\x1f".join(t).encode("utf-8")).hexdigest()[:20]
        out.append(f"{digest}:{seen[digest]}")
        seen[digest] += 1
    return out


def _is_dt(value: str) -> bool:
    return bool(_DT_RE.match(value.strip()))


def _classify(fields: list[str]) -> tuple[str, list[str] | None]:
    """Returns (kind, usable part): ok / truncated(head) / continuation(tail) / malformed."""
    blank = [f.strip() == "" for f in fields]
    if len(fields) == N_FIELDS:
        tail_blank = all(blank[TAIL_START:])
        if not blank[0] and not tail_blank:
            return "ok", fields
        if not blank[0] and tail_blank:
            return "truncated", fields[:TAIL_START]
        if blank[0] and _is_dt(fields[1]) and all(blank[1 + TAIL_LEN :]):
            return "continuation", fields[1 : 1 + TAIL_LEN]
        return "malformed", None
    if len(fields) < N_FIELDS:
        if _is_dt(fields[0]) and len(fields) <= TAIL_LEN:
            return "continuation", fields
        return "truncated", fields
    return "malformed", None


def _join(head: list[str], tail: list[str]) -> list[str] | None:
    if len(head) + len(tail) == N_FIELDS:
        return head + tail
    if len(head) + len(tail) - 1 == N_FIELDS:  # the break fell inside a field
        return [*head[:-1], head[-1] + " " + tail[0], *tail[1:]]
    return None


def parse_register_csv(data: bytes) -> RawParseResult:
    text, encoding, had_bom = decode(data)
    reader = csv.reader(io.StringIO(text, newline=""), delimiter=";", quotechar='"')
    try:
        header = [clean_field(h) for h in _strip_trailing_empty(next(reader))]
    except StopIteration as exc:
        raise SchemaDriftError("file vuoto") from exc
    if tuple(header) != EXPECTED_HEADER:
        raise SchemaDriftError(f"header inatteso: {header}")

    records: list[tuple[int, list[str]]] = []
    for fields in reader:
        fields = _strip_trailing_empty(fields)
        if not fields or all(f.strip() == "" for f in fields):
            continue
        records.append((reader.line_num, fields))

    classified = [(ln, fields, *_classify(fields)) for ln, fields in records]
    good: list[tuple[int, list[str], str]] = []
    quarantine_rows = []
    repairs: Counter = Counter()
    consumed: set[int] = set()
    for i, (ln, fields, kind, part) in enumerate(classified):
        if i in consumed:
            continue
        if kind == "ok":
            repair = "cell_break" if any("\n" in f or "\r" in f for f in fields) else ""
            if repair:
                repairs[repair] += 1
            good.append((ln, fields, repair))
            continue
        if kind == "truncated" and i + 1 < len(classified) and classified[i + 1][2] == "continuation":
            merged = _join(part, classified[i + 1][3])
            if merged is not None:
                good.append((ln, merged, "join"))
                consumed.add(i + 1)
                repairs["join"] += 1
                continue
        quarantine_rows.append({"line_no": ln, "n_fields": len(fields), "kind": kind, "raw": ";".join(f for f in fields if f.strip())})

    cleaned = [tuple(clean_field(f) for f in fields) for _, fields, _ in good]
    df = pd.DataFrame(cleaned, columns=list(EXPECTED_HEADER), dtype="string")
    df.insert(0, "record_id", record_ids(cleaned))
    df["line_no"] = [ln for ln, _, _ in good]
    df["repair"] = [rep for _, _, rep in good]
    quarantine = pd.DataFrame(quarantine_rows, columns=["line_no", "n_fields", "kind", "raw"])
    return RawParseResult(
        rows=df,
        quarantine=quarantine,
        header=header,
        encoding=encoding,
        had_bom=had_bom,
        physical_records=len(records),
        repairs=repairs,
    )
