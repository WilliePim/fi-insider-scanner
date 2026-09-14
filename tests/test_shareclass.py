import pytest

from fi_insider_scanner.canon.shareclass import parse_share_class


@pytest.mark.parametrize(
    "name,cls",
    [
        ("Skanska AB ser. B", "B"),
        ("Saab AB serie B", "B"),
        ("Serneke Group AB B", "B"),
        ("Akelius Residential Property AB ser. D", "D"),
        ("Industrivärden, AB ser. C", "C"),
        ("AB Volvo ser. A", "A"),
        ("Investment AB Latour B", "B"),
        ("Mertiva A", "A"),
        ("BIOVIC B", "B"),
        ("Hoi Publishing B", "B"),
        ("Fastpartner AB ser. A", "A"),
        ("Bolaget B-aktie", "B"),
        ("Testbolaget AB", None),
        ("ABB Ltd", None),
        ("Vimian E1 2026", None),
        ("", None),
    ],
)
def test_share_class(name, cls):
    assert parse_share_class(name).share_class == cls


def test_pref_sdr_and_type_hint():
    pref = parse_share_class("Testbolaget AB pref")
    assert pref.is_pref and pref.share_class is None
    bta = parse_share_class("Exempel Group AB BTA")
    assert bta.share_class is None and bta.type_hint == "BTA"
    sdb = parse_share_class("Hexagon AB ser. B SDB")
    assert sdb.share_class == "B" and sdb.is_sdr
