import pytest

from fi_insider_scanner.canon.taxonomy import (
    InstrumentType,
    TxnKind,
    VenueClass,
    direction,
    instrument_type,
    instrument_type_from_name,
    roles,
    txn_kind,
    venue_class,
)

OBSERVED_KARAKTAR = [
    "Förvärv",
    "Avyttring",
    "Teckning",
    "Tilldelning",
    "Lösen minskning",
    "Lösen ökning",
    "Gåva mottagen",
    "Lån utlåning",
    "Gåva lämnad",
    "Lån återgång ökning",
    "Utbyte ökning",
    "Utbyte minskning",
    "Konvertering ökning",
    "Utdelning mottagen",
    "Konvertering minskning",
    "Lån mottaget",
    "Inlösen egenutfärdat instrument",
    "Utfärdande av instrument",
    "Pantsättning",
    "Lån återgång minskning",
    "Fusion ökning",
    "Interntransaktion – Avyttring",
    "Interntransaktion – Förvärv",
    "Utdelning lämnad",
    "Pantsättning åter",
    "Koncernintern överföring ökning",
    "Koncernintern överföring minskning",
    "Fusion minskning",
    "Arv mottagen",
    "Arv ökning",
    "Koncernintern överföring förvärv",
    "Koncernintern överföring avyttring",
    "Bodelning minskning",
    "Fission ökning",
    "Fission minskning",
    "Bodelning ökning",
    "Arv minskning",
    "Arv lämnad",
    "Bodelning avyttring",
    "Blankning",
    "Bodelning förvärv",
]


def test_all_observed_karaktar_values_map():
    assert len(OBSERVED_KARAKTAR) == 41
    for value in OBSERVED_KARAKTAR:
        assert txn_kind(value) is not TxnKind.UNMAPPED, value


def test_only_forvarv_is_purchase_and_unknown_is_unmapped():
    purchases = [v for v in OBSERVED_KARAKTAR if txn_kind(v) is TxnKind.ACQ_PURCHASE]
    assert purchases == ["Förvärv"]
    assert txn_kind("Köp på börsen") is TxnKind.UNMAPPED
    assert txn_kind("") is TxnKind.UNMAPPED


def test_direction():
    assert direction(TxnKind.ACQ_PURCHASE) == 1
    assert direction(TxnKind.DISP_SALE) == -1
    assert direction(TxnKind.PLEDGE) == 0


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("Utanför handelsplats", VenueClass.OFF_VENUE),
        ("NASDAQ STOCKHOLM AB", VenueClass.XSTO),
        ("OMX NORDIC EXCHANGE STOCKHOLM AB", VenueClass.XSTO),
        ("NASDAQ STOCKHOLM AB - NORDIC@MID", VenueClass.XSTO),
        ("FIRST NORTH SWEDEN - SME GROWTH MARKET", VenueClass.FNSE),
        ("AKTIETORGET", VenueClass.SPOTLIGHT),
        ("SPOTLIGHT STOCK MARKET", VenueClass.SPOTLIGHT),
        ("NORDIC SME", VenueClass.NGM),
        ("CBOE EUROPE - DXE DARK ORDER BOOK (NL)", VenueClass.MTF_SI),
        ("SVENSKA HANDELSBANKEN AB - SYSTEMATIC INTERNALISER", VenueClass.MTF_SI),
        ("TORONTO STOCK EXCHANGE", VenueClass.FOREIGN_EXCHANGE),
        ("", VenueClass.UNKNOWN),
    ],
)
def test_venue_class(raw, expected):
    assert venue_class(raw) is expected


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("Verkställande direktör (VD)", {"ceo"}),
        ("VD", {"ceo"}),
        ("Vice VD", {"deputy_ceo"}),
        ("Styrelseledamot/suppleant", {"board", "deputy_board"}),
        ("Ekonomichef/finanschef/finansdirektör", {"cfo"}),
        ("Styrelseordförande", {"chair"}),
        ("Styrelseordförande, Styrelseledamot", {"chair", "board"}),
        ("Verkställande direktör (VD), Styrelseledamot", {"ceo", "board"}),
        ("Annan medlem i bolagets administrations-, lednings- eller kontrollorgan", {"other_admin_body"}),
        ("Annan ledande befattningshavare", {"other_exec"}),
        ("Arbetstagarrepresentant i styrelsen eller arbetstagarsuppleant", {"employee_rep"}),
        ("Större ägare", {"owner_keyword"}),
        ("Ägare 10+%", {"owner_keyword"}),
    ],
)
def test_roles(raw, expected):
    assert set(roles(raw)) == expected


def test_instrument_type_and_name_rules():
    assert instrument_type("Aktie") is InstrumentType.SHARE
    assert instrument_type("BTA (betald tecknad aktie)") is InstrumentType.BTA
    assert instrument_type("") is None
    assert instrument_type_from_name("Gammal AB BTA") is InstrumentType.BTA
    assert instrument_type_from_name("Gammal AB TO 2018") is InstrumentType.WARRANT_SUB
    assert instrument_type_from_name("Gammal AB TO3") is InstrumentType.WARRANT_SUB
    assert instrument_type_from_name("Gammal AB B") is None
    assert instrument_type_from_name("XYZ 123") is None
