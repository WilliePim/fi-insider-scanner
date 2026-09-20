"""Case zero (ADR-038): the declared selection and the WHO / WHERE / WHEN dossier, with no verdict.

The dossier holds only sourced facts: the FI register (rows cited by record_id), market data (stated as
Yahoo's) and primary sources read by the analyst and passed in a JSON file
(`dossier/<case>_sources.json`: facts with a URL and a date). Everything that was not read goes into the
NON VERIFICATO / MISSINGNESS section. The WHO/WHERE/WHEN score is provisional (starred) and its anchors
are written in the dossier itself.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from ..canon.visibility import Register
from ..gates.large_holder import large_holder, position_lb
from ..gates.openmarket import base_purchase
from ..gates.routine import routine_metrics
from ..mdtable import md_table

BUY_KINDS = {
    "acq_purchase",
    "subscription",
    "grant",
    "exercise_in",
    "gift_in",
    "conversion_in",
    "exchange_in",
    "inheritance_in",
    "division_in",
    "merger_in",
    "internal_in",
}
SELL_KINDS = {
    "disp_sale",
    "exercise_out",
    "gift_out",
    "conversion_out",
    "exchange_out",
    "inheritance_out",
    "division_out",
    "merger_out",
    "internal_out",
    "redemption",
}

MISSINGNESS_CHECKLIST = [
    "ultimo report infra-annuale (ricavi, EBIT, cassa, debito netto) letto dalla fonte primaria",
    "tabella dei maggiori azionisti / possesso degli insider (annual report o pagina IR) con data",
    "comunicati stampa dell'emittente nella finestra del cluster e nei 30 giorni precedenti",
    "calendario finanziario (prossimo report, AGM) dalla pagina IR",
    "eventuali prospetti, emissioni dirette, programmi di incentivazione in corso",
    "verbali/avviso di convocazione dell'ultima AGM (mandati, autorizzazioni a emettere)",
    "retribuzione in contanti dei dirigenti (per rapportare la taglia dell'acquisto)",
    "lock-up o accordi tra azionisti",
]

SCORE_ANCHORS = """### Ancore del punteggio (provvisorie, ADR-038)

- **WHO** 0: acquisti simbolici, routine o solo veicoli senza persona identificata · 1: tre persone, importi piccoli e nessuna variazione di posizione misurabile · 2: tre o più persone con importi materiali (≥ 250 kSEK a testa dal registro) oppure variazione di posizione verificata ≥ 10% · 3: CEO/CFO e presidente insieme, importi materiali e variazione di posizione verificata su fonte primaria.
- **WHERE** 0: nessuna fonte primaria letta · 1: un report letto, nessun fatto che spieghi il momento · 2: report e comunicati letti, contesto coerente con gli acquisti · 3: fatto verificabile e databile che precede gli acquisti (risultati, contratto, ristrutturazione) letto sulla fonte.
- **WHEN** 0: nessun evento databile · 1: solo il report appena pubblicato (closed period appena aperto: strutturale in Europa) · 2: un evento databile futuro entro 6 mesi (AGM, scadenza, report) · 3: più eventi databili con date confermate dal calendario dell'emittente.

Ogni punteggio porta un asterisco: dipende da ciò che è stato letto, non da ciò che esiste.
"""


@dataclass
class CaseSelection:
    case: pd.Series | None
    in_band: bool
    candidates: pd.DataFrame
    rule: str


def select_case(events_b: pd.DataFrame, cfg: dict) -> CaseSelection:
    cz = cfg["caso_zero"]
    start, end = pd.Timestamp(cz["window_start"]), pd.Timestamp(cz["window_end"]) + pd.Timedelta(days=1)
    rule = (
        f"trigger B con T in [{cz['window_start']}, {cz['window_end']}], score 4/4, non stale, banda 50-300M USD as-of l'ancora, "
        "ticker verificato sui prezzi del registro; spareggi: più persone fisiche, poi T più recente; se nessuno è in banda, il migliore fuori banda con nota"
    )
    ev = events_b[(events_b["as_of"] >= start) & (events_b["as_of"] < end) & events_b["gate_ok"]].copy()
    ev = ev[ev["verified"].eq(True)]
    ranked = ev.sort_values(["n_persons", "as_of"], ascending=[False, False])
    in_band = ranked[ranked["band"].eq("50_300")]
    if not in_band.empty:
        return CaseSelection(in_band.iloc[0], True, ranked, rule)
    if not ranked.empty:
        return CaseSelection(ranked.iloc[0], False, ranked, rule)
    return CaseSelection(None, False, ranked, rule)


def _fmt_sek(x) -> str:
    return "—" if x is None or pd.isna(x) else f"{x:,.0f}"


def _person_block(
    v_all: pd.DataFrame, v_at_t: pd.DataFrame, person: str, window: pd.DataFrame, as_of: pd.Timestamp, cfg: dict, shares_out: float | None
) -> str:
    own_all = v_all[v_all["person_key"].eq(person)].sort_values("trade_date")
    own_window = window[window["person_key"].eq(person)]
    lines = []
    names = sorted(set(own_all["pdmr_name"]))
    roles = sorted({r for rs in own_window["roles"] for r in rs}) or sorted({r for rs in own_all["roles"] for r in rs})
    raw_roles = sorted(set(own_window["role_raw"])) or sorted(set(own_all["role_raw"]))
    lines.append(f"### {' / '.join(names)}\n")
    lines.append(f"- Ruolo (Befattning): {', '.join(raw_roles)} → canonico {', '.join(roles) or '—'}")
    notifiers = own_window.groupby(["notifier_name", "associate_kind"]).size().reset_index()
    lines.append("- Chi notifica: " + "; ".join(f"{n} ({k})" for n, k, _ in notifiers.itertuples(index=False)))
    lines.append("\nAcquisti del cluster (registro FI):\n")
    tab = own_window[["trade_date", "published_at", "volume", "price", "currency", "value_sek", "venue_raw", "record_id"]].copy()
    tab["trade_date"] = tab["trade_date"].dt.date.astype(str)
    tab["published_at"] = tab["published_at"].astype(str)
    tab.columns = ["transazione", "pubblicazione", "quantità", "prezzo", "valuta", "SEK", "venue", "record"]
    lines.append(md_table(tab))
    before = v_at_t[v_at_t["trade_date"] < own_window["trade_date"].min()]
    lb = position_lb(before, person)
    vol = float(own_window["volume"].sum())
    ub = (
        f"≤ {vol / lb:.1%} (limite superiore: posizione minima visibile nel registro {lb:,.0f} azioni)"
        if lb > 0
        else "UNKNOWN (nessuna posizione visibile nel registro prima del cluster: il registro parte dal 2016-07 e non contiene il possesso)"
    )
    lines.append(f"\n- Variazione di posizione: {ub}. Possesso da fonte primaria: vedi WHERE; se assente → UNKNOWN.")
    five_y = own_all[own_all["trade_date"] >= as_of - pd.Timedelta(days=5 * 365)]
    buys = five_y[five_y["txn_kind"].isin(BUY_KINDS)]
    sells = five_y[five_y["txn_kind"].isin(SELL_KINDS)]
    lines.append(
        f"- Storia 5 anni nel registro (questo emittente): {len(buys)} righe in aumento ({', '.join(sorted(set(buys['txn_kind']))) or '—'}), "
        f"{len(sells)} in diminuzione ({', '.join(sorted(set(sells['txn_kind']))) or '—'}); prima riga {five_y['trade_date'].min().date() if len(five_y) else '—'}."
    )
    after = own_all[own_all["published_at"] > as_of]
    if after.empty:
        lines.append("- Dopo il cluster (fino allo snapshot): nessuna riga.")
    else:
        desc = "; ".join(f"{r.trade_date.date()} {r.txn_kind} {r.volume:,.0f} @ {r.price} {r.currency}" for r in after.itertuples())
        lines.append(f"- Dopo il cluster (fino allo snapshot): {desc}.")
    m = routine_metrics(v_at_t, person, as_of, cfg["routine"])
    lines.append(
        f"- Routine a T: mesi con acquisti (12m) {m.n_buy_months}, dispersione {'—' if m.dispersion is None else f'{m.dispersion:.2f}'} → {'routine' if m.is_routine else 'non routine'}; etichetta CMP: {m.cmp_label}."
    )
    lines.append(
        f"- Grande azionista: {large_holder(v_at_t, person, shares_out, cfg['large_holder']['position_share_threshold'])} (mai `false`: MAR non copre i >10%)."
    )
    return "\n".join(lines) + "\n"


def build_dossier(
    case: pd.Series,
    register: Register,
    cfg: dict,
    shares_out: float | None,
    report_dates: pd.DatetimeIndex | None,
    sources: dict | None,
    in_band: bool,
    rule: str,
    snapshot_note: str,
) -> str:
    as_of = pd.Timestamp(case["as_of"])
    issuer = case["issuer_key"]
    v_t = register.visible(as_of, issuer)
    v_all = register.visible(pd.Timestamp("2099-01-01"), issuer)
    window = v_t[v_t["record_id"].isin(str(case["record_ids"]).split("|"))]
    persons = str(case["persons"]).split("|")
    sources = sources or {}
    facts = sources.get("facts", [])
    when = sources.get("when", [])
    holdings = sources.get("holdings", [])
    out: list[str] = []
    w = out.append
    name = case.get("issuer_name") or window["issuer_name_raw"].mode().iat[0]
    w(f"# Caso zero — {name}\n")
    w(f"Dossier generato dal registro FI ({snapshot_note}). Formato rubric WHO / WHERE / WHEN. **Nessun verdetto, nessun ordine.**\n")
    w("## Selezione\n")
    w(f"Regola dichiarata prima di guardare i prezzi successivi: {rule}.\n")
    w(f"Esito: {'in banda' if in_band else 'FUORI BANDA (nessun candidato in banda nella finestra)'}.\n")
    w("## Testata\n")
    head = [
        ("Emittente", name),
        ("LEI / issuer_key", issuer),
        ("ISIN", case["isin"]),
        ("Ticker (verificato sui prezzi del registro)", case["symbol"]),
        ("T (prima pubblicazione che completa il cluster)", str(as_of)),
        ("Ancora (prima transazione)", str(pd.Timestamp(case["anchor"]).date())),
        ("Ultima transazione della finestra", str(pd.Timestamp(case["window_end"]).date())),
        (
            "Market cap as-of ancora",
            f"{_fmt_sek(case['mcap_sek'])} SEK = {case['mcap_usd'] / 1e6:,.0f} M USD (azioni {_fmt_sek(case['shares_used'])} al {str(case['shares_date'])[:10]} da Yahoo, prezzo {case['price_used']} da {case['price_source']}, USDSEK {case['usdsek']:.3f})"
            if pd.notna(case["mcap_usd"])
            else "UNKNOWN",
        ),
        ("Banda", case["band"] or "UNKNOWN"),
        ("Persone fisiche distinte", int(case["n_persons"])),
        ("Valore SEK del cluster", _fmt_sek(case["value_sek"])),
        ("Staleness (giorni)", int(case["staleness_days"])),
    ]
    w(md_table(pd.DataFrame(head, columns=["campo", "valore"])))
    w("\n## Layer 1 a T\n")
    l1 = [
        ("cluster ≥ 3 persone / 30 gg", True, f"record {case['record_ids']}"),
        ("non routine (≥ 3 persone non routine)", bool(case["not_routine"]), f"n_routine = {int(case['n_routine'])}"),
        (
            "dilution veto ≠ BLOCKED",
            bool(case["dilution_ok"]),
            f"verdetto {case['dilution']}, partecipazione {bool(case['dil_participation'])}, trappola {bool(case['dil_trap'])}, crescita azioni {'—' if pd.isna(case['dil_growth']) else f'{case["dil_growth"]:+.1%}'}",
        ),
        ("nessun grande azionista `true`", bool(case["no_large_holder"]), f"n_large_holder = {int(case['n_large_holder'])}"),
        (
            "S3 (sottoscrizione strutturale) nella finestra",
            bool(case["s3_in_window"]),
            f"prezzo uniforme on-venue: {bool(case['uniform_onvenue'])}; S1 {bool(case['s1_subscription'])}, S2 {bool(case['s2_issue_instruments'])}",
        ),
    ]
    w(md_table(pd.DataFrame([(a, "sì" if b else "no", c) for a, b, c in l1], columns=["gate", "esito", "evidenza"])))
    w(f"\nScore Layer 1 = **{int(case['score'])}/4**. Acquisti simbolici (limite superiore < 1%): {int(case['n_symbolic'])}.\n")
    w("\n## WHO\n")
    for person in persons:
        w(_person_block(v_all, v_t, person, window, as_of, cfg, shares_out))
    later = v_all[
        base_purchase(v_all)
        & (v_all["published_at"] > as_of)
        & (v_all["trade_date"] <= pd.Timestamp(case["anchor"]) + pd.Timedelta(days=cfg["cluster"]["window_days"]))
        & ~v_all["person_key"].isin(persons)
    ]
    if not later.empty:
        w("### Altre persone entrate nella stessa finestra dopo T (non contano nello score)\n")
        tab = later[["pdmr_name", "role_raw", "trade_date", "published_at", "volume", "price", "value_sek"]].copy()
        tab["trade_date"] = tab["trade_date"].dt.date.astype(str)
        tab["published_at"] = tab["published_at"].astype(str)
        w(md_table(tab))
    if holdings:
        w("\n### Possesso da fonte primaria\n")
        w(md_table(pd.DataFrame(holdings)))
    w("\n## WHERE\n")
    if facts:
        w("Fatti letti su fonti primarie (URL e data di lettura):\n")
        w(md_table(pd.DataFrame(facts)))
    else:
        w("Nessuna fonte primaria letta: tutto ciò che segue è MISSINGNESS.\n")
    w("\n### NON VERIFICATO / MISSINGNESS\n")
    read_keys = {f.get("covers") for f in facts} | {h.get("covers") for h in holdings} | {x.get("covers") for x in when}
    for item in MISSINGNESS_CHECKLIST:
        mark = "letto" if item in read_keys else "NON LETTO"
        w(f"- [{mark}] {item}")
    w("\n## WHEN\n")
    if report_dates is not None and len(report_dates):
        past = report_dates[report_dates <= as_of]
        future = report_dates[report_dates > as_of]
        dsr = None if case["days_since_report"] is None or pd.isna(case["days_since_report"]) else int(case["days_since_report"])
        stale = (
            " — lista incompleta (ultima data oltre 200 giorni prima di T): attributo della pipeline UNKNOWN, vale la fonte primaria"
            if dsr is not None and dsr > 200
            else ""
        )
        w(
            f"- Date report note a Yahoo: ultima prima di T {past.max().date() if len(past) else '—'} "
            f"({'—' if dsr is None else dsr} giorni prima di T){stale}; prossime {', '.join(str(d.date()) for d in future[:3]) or '—'}."
        )
        w(
            "- Closed period MAR: 30 giorni prima di ogni report; gli acquisti PDMR si concentrano strutturalmente nei giorni successivi (attributo, non segnale)."
        )
    else:
        w("- Date report: UNKNOWN su Yahoo. Closed period non calcolabile dalla pipeline.")
    if when:
        w("\nEventi databili da fonti primarie:\n")
        w(md_table(pd.DataFrame(when)))
    else:
        w("- Nessun evento databile letto da fonte primaria (AGM, scadenze, emissioni): MISSINGNESS.")
    w("\n## Punteggio provvisorio\n")
    sc = sources.get("score", {})
    who, where, when_s = sc.get("who"), sc.get("where"), sc.get("when")
    tot = None if None in (who, where, when_s) else who + where + when_s
    w(
        md_table(
            pd.DataFrame(
                [
                    ("WHO", f"{who}/3*" if who is not None else "n/d*"),
                    ("WHERE", f"{where}/3*" if where is not None else "n/d*"),
                    ("WHEN", f"{when_s}/3*" if when_s is not None else "n/d*"),
                    ("Totale", f"{tot}/9*" if tot is not None else "n/d*"),
                ],
                columns=["dimensione", "punteggio"],
            )
        )
    )
    if sc.get("notes"):
        w("\n" + "\n".join(f"- {n}" for n in sc["notes"]))
    w("\n\\* provvisorio: riflette ciò che è stato letto alla data del dossier, non un giudizio sul titolo. Nessun verdetto.\n")
    w("\n" + SCORE_ANCHORS)
    w("\nCosto API di modelli linguistici per questo dossier: 0 token, 0 USD.\n")
    return "\n".join(out) + "\n"


def load_sources(path: Path) -> dict | None:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
