from datetime import date, datetime

import pytest

from fi_insider_scanner.canon.parse import (
    currency_code,
    isin_valid,
    ja_flag,
    lei_valid,
    parse_date,
    parse_datetime,
    parse_decimal,
)


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("25,40", 25.4),
        ("27624,0", 27624.0),
        ("10 000,0", 10000.0),
        ("1 000,5", 1000.5),
        ("8 030", 8030.0),
        ("2,116020", 2.11602),
        ("0", 0.0),
        ("", None),
        ("1,2,3", None),
        ("abc", None),
    ],
)
def test_parse_decimal(raw, expected):
    assert parse_decimal(raw) == expected


def test_parse_datetime_strict():
    assert parse_datetime("2026-09-13 22:54:41") == datetime(2026, 9, 13, 22, 54, 41)
    assert parse_date("2026-08-28 00:00:00") == date(2026, 8, 28)
    assert parse_datetime("13/09/2026 22:54:41") is None
    assert parse_datetime("2026-02-30 00:00:00") is None
    assert parse_datetime("") is None


def test_ja_flag():
    assert ja_flag("Ja") is True
    assert ja_flag("") is False
    assert ja_flag(None) is False
    assert ja_flag("Nej") is None
    assert ja_flag("NASDAQ STOCKHOLM AB") is None


def test_isin_check_digit():
    assert isin_valid("SE0000108656")  # Ericsson B
    assert isin_valid("US0378331005")  # Apple
    assert isin_valid("SE0008613731")  # Biovica B
    assert not isin_valid("SE0000108657")
    assert not isin_valid("SE000010865")
    assert not isin_valid("")


def test_lei_checksum():
    assert lei_valid("549300OQ8R5TCAP0BS18")  # Vimian Group AB
    assert not lei_valid("549300OQ8R5TCAP0BS19")
    assert not lei_valid("TESTLEI")


def test_currency_code():
    assert currency_code("SEK") == "SEK"
    assert currency_code("S EK") is None
    assert currency_code("") is None
