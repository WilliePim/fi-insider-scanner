"""Parsers for the FI values: comma decimals, dates, checkboxes, ISIN, LEI.

Every parser returns None when the value cannot be read; the caller records an error if the raw field was
not empty. No value is ever estimated.
"""

from __future__ import annotations

import re
from datetime import date, datetime

_DECIMAL_RE = re.compile(r"^-?\d+(?:,\d+)?$")
_DOT_DECIMAL_RE = re.compile(r"^-?\d+\.\d+$")
_SPACES = (" ", " ", " ", " ")
_DT_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})(?: (\d{2}):(\d{2}):(\d{2}))?$")
_LEI_RE = re.compile(r"^[A-Z0-9]{18}[0-9]{2}$")
_ISIN_RE = re.compile(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$")


def parse_decimal(raw: str | None) -> float | None:
    if raw is None:
        return None
    s = raw.strip()
    for sp in _SPACES:
        s = s.replace(sp, "")
    if not s:
        return None
    if _DECIMAL_RE.match(s):
        return float(s.replace(",", "."))
    if _DOT_DECIMAL_RE.match(s):
        return float(s)
    return None


def parse_datetime(raw: str | None) -> datetime | None:
    if not raw:
        return None
    m = _DT_RE.match(raw.strip())
    if not m:
        return None
    y, mo, d, hh, mm, ss = m.groups()
    try:
        return datetime(int(y), int(mo), int(d), int(hh or 0), int(mm or 0), int(ss or 0))
    except ValueError:
        return None


def parse_date(raw: str | None) -> date | None:
    dt = parse_datetime(raw)
    return dt.date() if dt else None


def ja_flag(raw: str | None) -> bool | None:
    """`Ja` -> True, empty -> False, anything else -> None (an error)."""
    s = (raw or "").strip()
    if s == "":
        return False
    if s.casefold() in ("ja", "yes"):
        return True
    return None


def _luhn_digits_ok(digits: str) -> bool:
    total = 0
    for i, ch in enumerate(reversed(digits)):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def isin_valid(isin: str | None) -> bool:
    if not isin or not _ISIN_RE.match(isin):
        return False
    digits = "".join(str(int(c, 36)) for c in isin)
    return _luhn_digits_ok(digits)


def lei_valid(lei: str | None) -> bool:
    if not lei or not _LEI_RE.match(lei):
        return False
    return int("".join(str(int(c, 36)) for c in lei)) % 97 == 1


_CURRENCY_RE = re.compile(r"^[A-Z]{3}$")


def currency_code(raw: str | None) -> str | None:
    s = (raw or "").strip()
    return s if _CURRENCY_RE.match(s) else None
