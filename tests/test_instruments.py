import pandas as pd

from fi_insider_scanner.canon.mapping import infer_instrument_types


def frame(rows):
    return pd.DataFrame(rows, columns=["instrument_type_reported", "isin", "instrument_name", "issuer_name_raw", "isin_valid"])


def test_tier1_same_isin_typed_elsewhere():
    df = infer_instrument_types(
        frame(
            [
                (None, "SE0008613731", "Biovica B", "Biovica International AB", True),
                ("share", "SE0008613731", "Biovica B", "Biovica International AB", True),
            ]
        )
    )
    assert df.loc[0, "instrument_type"] == "share" and df.loc[0, "type_source"] == "isin_rows"
    assert df.loc[1, "type_source"] == "reported"


def test_isin_type_conflict_yields_none():
    df = infer_instrument_types(
        frame(
            [
                (None, "SE0000108656", "Testbolaget", "Testbolaget AB", True),
                ("share", "SE0000108656", "Testbolaget", "Testbolaget AB", True),
                ("bta", "SE0000108656", "Testbolaget BTA", "Testbolaget AB", True),
            ]
        )
    )
    assert df.loc[0, "instrument_type"] is None
    assert bool(df.loc[0, "type_conflict"]) is True
    assert df.loc[0, "type_source"] == "none"


def test_isin_majority_type_at_90_percent():
    rows = [(None, "SE0000108656", "Testbolaget", "Testbolaget AB", True)]
    rows += [("share", "SE0000108656", "Testbolaget", "Testbolaget AB", True)] * 9
    rows += [("option", "SE0000108656", "Testbolaget", "Testbolaget AB", True)]
    df = infer_instrument_types(frame(rows))
    assert df.loc[0, "instrument_type"] == "share" and df.loc[0, "type_source"] == "isin_majority"
    assert df.loc[10, "instrument_type"] == "option" and df.loc[10, "type_source"] == "reported"


def test_tier2_name_rule_and_tier3_issuer_name_match():
    df = infer_instrument_types(
        frame(
            [
                (None, "SE0000000001", "Gammal AB BTA", "Gammal AB", True),
                (None, "SE0000000002", "Gammal AB TO 2018", "Gammal AB", True),
                (None, "SE0008613731", "Gammal", "Gammal AB (publ)", True),
                (None, "SE0000108656", "XYZ 123", "Gammal AB", True),
                (None, None, "Gammal", "Gammal AB", False),
            ]
        )
    )
    assert list(df["instrument_type"]) == ["bta", "subscription_warrant", "share", None, None]
    assert list(df["type_source"]) == ["name_rule", "name_rule", "issuer_name_match", "none", "none"]
