import pandas as pd
import pytest

from fi_insider_scanner.canon.names import (
    apply_merges,
    associate_kind,
    build_merge_rules,
    is_entity,
    is_natural_person,
    normalize_name,
)

T = pd.Timestamp


def test_normalize_whitespace_case_and_comma_order():
    assert normalize_name("  Anna  Svensson ") == normalize_name("ANNA SVENSSON") == "anna svensson"
    assert normalize_name("Svensson, Anna") == "anna svensson"
    assert normalize_name("Anna Svensson") == "anna svensson"


@pytest.mark.parametrize(
    "name,entity",
    [
        ("Svensson Invest AB", True),
        ("Stiftelsen X", True),
        ("X Förvaltning AB", True),
        ("Nordic Holding Oy", True),
        ("Akelius Apartments Ltd", True),
        ("Fabeges Vinstandelsstiftelse", True),
        ("Abdul Aziz", False),
        ("Lars Absalon", False),
        ("Klas  Holmgren", False),
    ],
)
def test_is_entity(name, entity):
    assert is_entity(name) is entity


def test_is_natural_person():
    assert is_natural_person("Testbolaget AB (publ)") is False
    assert is_natural_person("Madonna") is None
    assert is_natural_person("Anna Svensson") is True


def test_associate_kind():
    assert associate_kind("Arlon Capital AB", "Magnus Lindquist") == "vehicle"
    assert associate_kind("Karin Svensson", "Anna Svensson") == "family"
    assert associate_kind("Mikael Thorén", "Mikael  Thorén") == "self"


def _names(rows):
    return pd.DataFrame(rows, columns=["issuer_key", "name_key", "first_seen"])


def test_middle_name_merge_same_issuer_only():
    rules, _ = build_merge_rules(
        _names(
            [
                ("I1", "anna svensson", T("2020-01-01")),
                ("I1", "anna maria svensson", T("2020-02-01")),
                ("I2", "anna maria svensson", T("2020-01-15")),
            ]
        )
    )
    assert len(rules) == 1
    issuer = pd.Series(["I1", "I2"])
    names = pd.Series(["anna maria svensson", "anna maria svensson"])
    merged = apply_merges(issuer, names, T("2020-03-01"), rules)
    assert list(merged) == ["anna svensson", "anna maria svensson"]


def test_different_first_names_never_merge():
    rules, _ = build_merge_rules(
        _names([("I1", "anna svensson", T("2020-01-01")), ("I1", "maria svensson", T("2020-01-01"))])
    )
    assert rules == []


def test_ambiguous_long_variants_stop_merging_point_in_time():
    rules, flags = build_merge_rules(
        _names(
            [
                ("I1", "anna svensson", T("2020-01-01")),
                ("I1", "anna maria svensson", T("2020-02-01")),
                ("I1", "anna karin svensson", T("2020-06-01")),
            ]
        )
    )
    issuer = pd.Series(["I1"])
    long_name = pd.Series(["anna maria svensson"])
    assert list(apply_merges(issuer, long_name, T("2020-01-15"), rules)) == ["anna maria svensson"]
    assert list(apply_merges(issuer, long_name, T("2020-03-01"), rules)) == ["anna svensson"]
    assert list(apply_merges(issuer, long_name, T("2020-07-01"), rules)) == ["anna maria svensson"]
    assert "NAME_AMBIGUOUS" in set(flags["flag"])


def test_diacritic_near_duplicates_flagged_not_merged():
    rules, flags = build_merge_rules(
        _names([("I1", "per östlund", T("2020-01-01")), ("I1", "per ostlund", T("2020-01-05"))])
    )
    assert rules == []
    assert "NEAR_DUP_NAME" in set(flags["flag"])
