"""Profile of the raw snapshot (checkpoint 1): counts, invariants, per-year regimes."""

from __future__ import annotations

from datetime import UTC, datetime

import pandas as pd

from ..mdtable import md_table
from .bulk import Snapshot
from .rawcsv import EXPECTED_HEADER, RawParseResult

UPSTREAM_KEY = [
    "Publiceringsdatum",
    "Emittent",
    "Anmälningsskyldig",
    "Person i ledande ställning",
    "Karaktär",
    "ISIN",
    "Transaktionsdatum",
    "Volym",
    "Pris",
]

CANONICAL = {
    "Publiceringsdatum": "published_at",
    "Emittent": "issuer_name_raw → issuer_key",
    "LEI-kod": "issuer_lei",
    "Anmälningsskyldig": "notifier_name → associate_kind",
    "Person i ledande ställning": "pdmr_name → person_key",
    "Befattning": "role_raw → roles",
    "Närstående": "is_closely_associated",
    "Korrigering": "is_amendment",
    "Beskrivning av korrigering": "amendment_note",
    "Är förstagångsrapportering": "is_initial",
    "Är kopplad till aktieprogram": "is_share_program",
    "Karaktär": "nature_raw → txn_kind",
    "Instrumenttyp": "instrument_type_raw → instrument_type (+ type_source)",
    "Instrumentnamn": "instrument_name → share_class",
    "ISIN": "isin",
    "Transaktionsdatum": "trade_date",
    "Volym": "volume",
    "Volymsenhet": "volume_unit",
    "Pris": "price",
    "Valuta": "currency",
    "Handelsplats": "venue_raw → venue_class",
    "Status": "status_raw → is_current / chain_status",
}


def _by_year(df: pd.DataFrame, col: str, top: int | None = None) -> pd.DataFrame:
    counts = pd.crosstab(df[col].replace("", "(vuoto)"), df["_year"])
    counts["totale"] = counts.sum(axis=1)
    counts = counts.sort_values("totale", ascending=False)
    if top:
        rest = counts.iloc[top:].sum()
        counts = counts.iloc[:top]
        if rest["totale"] > 0:
            counts.loc["(altri)"] = rest
    counts.index.name = col
    return counts.astype(int)


def build_profile(raw: RawParseResult, snap: Snapshot) -> str:
    df = raw.rows.copy()
    pub = pd.to_datetime(df["Publiceringsdatum"], format="%Y-%m-%d %H:%M:%S", errors="coerce")
    trade = pd.to_datetime(df["Transaktionsdatum"], format="%Y-%m-%d %H:%M:%S", errors="coerce")
    df["_year"] = pub.dt.year.astype("Int64").astype("string").fillna("?")
    out: list[str] = []
    w = out.append

    w("# 00 — Profilo dello snapshot grezzo\n")
    w(f"Generato {datetime.now(UTC).isoformat(timespec='seconds')}.\n")
    w("## Fonte\n")
    w(
        md_table(
            pd.DataFrame(
                [
                    ("repo", "civictechsweden/oppna-insynsregistret"),
                    ("commit dati", snap.commit_sha),
                    ("data commit", snap.commit_date),
                    ("sha256", snap.sha256),
                    ("byte", f"{snap.n_bytes:,}"),
                    ("encoding", f"{raw.encoding} (BOM: {'sì' if raw.had_bom else 'no'})"),
                ],
                columns=["campo", "valore"],
            )
        )
    )

    w("\n## Conteggi\n")
    w(
        md_table(
            pd.DataFrame(
                [
                    ("record fisici letti", raw.physical_records),
                    ("righe accettate", len(raw.rows)),
                    ("ricomposte (join)", raw.repairs.get("join", 0)),
                    ("celle con a capo normalizzate", raw.repairs.get("cell_break", 0)),
                    ("in quarantena", len(raw.quarantine)),
                ],
                columns=["voce", "n"],
            )
        )
    )
    if not raw.quarantine.empty:
        w("\nRecord in quarantena (non ricomposti: la metà corrispondente non è adiacente, l'accoppiamento sarebbe una congettura):\n")
        q = raw.quarantine.copy()
        q["raw"] = q["raw"].str.slice(0, 140)
        w(md_table(q))

    w("\n## Header e mappatura canonica\n")
    w("Header identico alle 22 colonne attese.\n")
    w(md_table(pd.DataFrame([(i, h, CANONICAL[h]) for i, h in enumerate(EXPECTED_HEADER)], columns=["#", "FI", "canonico"])))

    w("\n## Status e invarianti\n")
    w(md_table(df["Status"].value_counts().rename_axis("Status").reset_index(name="n")))
    ct = pd.crosstab(df["Korrigering"].replace("", "(vuoto)"), df["Är förstagångsrapportering"].replace("", "(vuoto)"))
    w("\nKorrigering × Är förstagångsrapportering:\n")
    w(md_table(ct, index=True))
    violations = ((df["Korrigering"] == "Ja") == (df["Är förstagångsrapportering"] == "Ja")).sum()
    w(f"\nViolazioni dell'invariante (Korrigering=Ja ⟺ förstagång vuoto): **{violations}**.\n")
    exact = df.duplicated(subset=list(EXPECTED_HEADER)).sum()
    upstream = df.duplicated(subset=UPSTREAM_KEY).sum()
    w(
        f"\nDuplicati esatti (22 campi): **{exact}**. Duplicati sulla chiave upstream a 9 campi: **{upstream}** "
        "(la dedup civictech li ha già fusi: righe identiche reali perse a monte, non recuperabili dal bulk).\n"
    )

    w("\n## Valori vuoti per colonna e anno di pubblicazione (%)\n")
    empty = df[list(EXPECTED_HEADER)].eq("").groupby(df["_year"]).mean().T * 100
    w(md_table(empty.round(1), digits=1, index=True))

    w("\n## Righe per giorno di pubblicazione\n")
    per_day = pub.dt.normalize().value_counts().sort_index()
    all_weekdays = pd.bdate_range(per_day.index.min(), per_day.index.max())
    zero_days = all_weekdays.difference(per_day.index)
    w(
        md_table(
            pd.DataFrame(
                [
                    ("massimo righe in un giorno", int(per_day.max())),
                    ("giorno con il massimo", str(per_day.idxmax().date())),
                    ("giorni con ≥ 1.000 righe (sospetto troncamento export)", int((per_day >= 1000).sum())),
                    ("giorni lun-ven senza righe (include festivi svedesi)", len(zero_days)),
                ],
                columns=["voce", "valore"],
            )
        )
    )
    zero_by_year = pd.Series(zero_days.year.astype(str)).value_counts().sort_index()
    w("\nGiorni lun-ven senza righe per anno (festivi inclusi; ~10-12/anno attesi):\n")
    w(md_table(zero_by_year.rename_axis("anno").reset_index(name="giorni")))

    w("\n## Ora di pubblicazione (fuso non dichiarato dalla fonte)\n")
    hours = pub.dt.hour.value_counts().sort_index()
    w(md_table(hours.rename_axis("ora").reset_index(name="righe")))

    w("\n## Ritardo pubblicazione − transazione (giorni)\n")
    lag = (pub.dt.normalize() - trade.dt.normalize()).dt.days
    q = lag.groupby(df["_year"]).quantile([0.5, 0.9, 0.95, 0.99]).unstack()
    q.columns = ["p50", "p90", "p95", "p99"]
    q["> 30 gg (%)"] = (lag > 30).groupby(df["_year"]).mean() * 100
    w(md_table(q.round(1), digits=1, index=True))

    for col, top in (
        ("Karaktär", None),
        ("Instrumenttyp", None),
        ("Valuta", None),
        ("Volymsenhet", None),
        ("Handelsplats", 20),
        ("Status", None),
    ):
        w(f"\n## {col} per anno di pubblicazione\n")
        w(md_table(_by_year(df, col, top), digits=0, index=True))

    w("\n## Befattning: valori distinti per anno\n")
    w(md_table(df.groupby("_year")["Befattning"].nunique().rename_axis("anno").reset_index(name="valori distinti")))
    return "\n".join(out) + "\n"
