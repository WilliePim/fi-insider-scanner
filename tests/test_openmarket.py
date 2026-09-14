from factory import T, txn, visible_all

from fi_insider_scanner.gates.openmarket import (
    a_exact,
    a_onvenue,
    b_row,
    base_purchase,
    exclusion_reason,
    sell_to_cover_candidates,
)


def _one(**kw):
    return visible_all([txn(**kw)])


def test_program_row_is_excluded():
    v = _one(program=True)
    assert not base_purchase(v).iloc[0]
    assert exclusion_reason(v).iloc[0] == "share_program"


def test_off_venue_passes_a_exact_but_not_onvenue_or_b():
    v = _one(venue="off_venue", value_usd=30000)
    assert a_exact(v, 25000).iloc[0]
    assert not a_onvenue(v, 25000).iloc[0]
    assert not b_row(v).iloc[0]


def test_amount_unit_and_zero_price_and_non_share():
    assert exclusion_reason(_one(unit="belopp")).iloc[0] == "amount_unit"
    assert exclusion_reason(_one(price=0.0)).iloc[0] == "zero_or_missing_price"
    assert exclusion_reason(_one(itype="bta")).iloc[0] == "non_share"
    assert exclusion_reason(_one(itype=None)).iloc[0] == "instrument_type_unknown"
    assert exclusion_reason(_one(kind="grant")).iloc[0] == "grant"
    assert exclusion_reason(_one()).iloc[0] == ""


def test_usd_threshold():
    # 10.000 x 25,40 SEK = 254.000 SEK: a SEK=X 10,0 -> 25.400 USD passa; a 10,2 -> 24.902 no.
    assert a_exact(_one(price=25.4, value_usd=254000 / 10.0), 25000).iloc[0]
    assert not a_exact(_one(price=25.4, value_usd=254000 / 10.2), 25000).iloc[0]


def test_sell_to_cover_candidates():
    rows = [
        txn("anna svensson", "2020-03-02", kind="grant"),
        txn("anna svensson", "2020-03-05", kind="disp_sale"),
        txn("anna svensson", "2020-05-05", kind="disp_sale"),
        txn("erik berg", "2020-03-05", kind="disp_sale"),
    ]
    v = visible_all(rows).sort_values("trade_date")
    flags = sell_to_cover_candidates(v, 30)
    got = {(p, str(d.date())): bool(f) for p, d, f in zip(v["name_key"], v["trade_date"], flags) if True}
    assert got[("anna svensson", "2020-03-05")] is True
    assert got[("anna svensson", "2020-05-05")] is False
    assert got[("erik berg", "2020-03-05")] is False
