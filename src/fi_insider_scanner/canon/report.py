"""Report del checkpoint 2: tabella canonica."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone

import pandas as pd

from ..mdtable import md_table
from .build import Canonical


def _counts(series: pd.Series, name: str) -> str:
    return md_table(series.fillna("(null)").astype(str).value_counts().rename_axis(name).reset_index(name="n"))


def build_report(c: Canonical, snapshot_id: str) -> str:
    df = c.df
    year = df["published_at"].dt.year
    out: list[str] = []
    w = out.append
    w("# 01 — Tabella canonica\n")
    w(f"Generato {datetime.now(timezone.utc).isoformat(timespec='seconds')} dallo snapshot `{snapshot_id}`.\n")

    w("## Mapping\n")
    w(md_table(pd.DataFrame([
        ("righe mappate", len(df)),
        ("righe rifiutate (Publiceringsdatum non interpretabile o schema)", len(c.rejects)),
        ("righe con almeno un errore di parse", int((df["parse_errors"].map(len) > 0).sum())),
    ], columns=["voce", "n"])))
    errs = Counter(e.split(":")[0] for errs in df["parse_errors"] for e in errs)
    if errs:
        w("\nErrori di parse per tipo:\n")
        w(md_table(pd.DataFrame(sorted(errs.items(), key=lambda kv: -kv[1]), columns=["tipo", "n"])))

    w("\n## Tassonomie\n")
    w(f"Karaktär non mappati: **{int((df['txn_kind'] == 'unmapped').sum())}**. "
      f"Instrumenttyp dichiarati non mappati: **{int(df['parse_errors'].map(lambda e: any(x.startswith('INSTRUMENT_TYPE_UNMAPPED') for x in e)).sum())}**.\n")
    w("\n" + _counts(df["txn_kind"], "txn_kind"))
    w("\n" + _counts(df["venue_class"], "venue_class"))
    w("\nVenue classificate come `other_venue` (trattate come on-venue):\n")
    w(md_table(df.loc[df["venue_class"] == "other_venue", "venue_raw"].value_counts().head(20).rename_axis("Handelsplats").reset_index(name="n")))
    w("\n" + _counts(df["associate_kind"], "associate_kind"))
    w("\n" + _counts(df["pdmr_is_natural_person"], "PDMR persona fisica"))

    w("\n## Identità emittente\n")
    w(_counts(df["issuer_key_source"], "fonte issuer_key"))
    w(f"\nEmittenti distinti: **{df['issuer_key'].nunique():,}** (di cui chiave da nome: {df.loc[df['issuer_key_source']=='name','issuer_key'].nunique():,}).\n")

    w("\n## Tipo strumento\n")
    ts = pd.crosstab(df["type_source"], year)
    w(md_table(ts, index=True, digits=0))
    w(f"\nConflitti di tipo sullo stesso ISIN (righe senza tipo dichiarato lasciate a null): **{int(df['type_conflict'].sum())}**.\n")
    w("\n" + _counts(df["instrument_type"], "instrument_type"))
    shares = df[df["instrument_type"] == "share"]
    w("\nClasse azioni sulle righe azionarie:\n")
    w(_counts(shares["share_class"], "share_class"))
    cls_conflict = shares.dropna(subset=["isin"]).groupby("isin")["share_class"].nunique()
    w(f"\nISIN azionari con classi diverse dal nome: **{int((cls_conflict > 1).sum())}** su {len(cls_conflict):,}.\n")

    w("\n## Catene di revisione\n")
    s = c.chain_stats
    w(md_table(pd.DataFrame([
        ("correzioni (Korrigering=Ja, Aktuell o Reviderad)", s.corrections),
        ("collegate", s.linked),
        ("  di cui a una riga Aktuell stantia (post-orizzonte)", s.linked_stale),
        ("ambigue (nessun link)", s.ambiguous),
        ("correzioni orfane", s.orphan_corrections),
        ("Reviderad orfane", s.orphan_revised),
    ], columns=["voce", "n"])))
    w("\n" + _counts(df["chain_status"], "chain_status"))
    if not s.links.empty:
        lag = s.links["lag_days"]
        w("\nRitardo correzione − versione precedente (giorni):\n")
        qs = lag.quantile([0.5, 0.75, 0.9, 0.95, 0.99])
        w(md_table(pd.DataFrame({"quantile": [f"p{int(q * 100)}" for q in qs.index], "giorni": qs.to_numpy()}), digits=1))
        changed = s.links[[c_ for c_ in s.links.columns if c_.startswith("changed_")]].mean() * 100
        w("\nCampi modificati dalla correzione (% dei link):\n")
        w(md_table(changed.rename_axis("campo").reset_index(name="%"), digits=1))
        stale = df[df["chain_status"] == "superseded_inferred"]
        if not stale.empty:
            w("\nRighe `superseded_inferred` per mese di pubblicazione:\n")
            w(md_table(stale["published_at"].dt.to_period("M").astype(str).value_counts().sort_index().rename_axis("mese").reset_index(name="n")))
        w("\n30 catene casuali (audit manuale):\n")
        sample = s.links.sample(min(30, len(s.links)), random_state=7)
        idx = df.set_index("record_id")
        rows = []
        for r in sample.itertuples():
            cor, pre = idx.loc[r.correction], idx.loc[r.predecessor]
            rows.append((cor["issuer_name_raw"][:28], cor["pdmr_name"][:22], str(cor["trade_date"].date()),
                         str(pre["published_at"]), str(cor["published_at"]), pre["status_raw"], r.score,
                         (r.note or "")[:50]))
        w(md_table(pd.DataFrame(rows, columns=["emittente", "persona", "trade", "pub prec.", "pub corr.", "status prec.", "score", "nota"])))

    w("\n## Persone\n")
    w(md_table(pd.DataFrame([
        ("regole di merge (middle name, stesso emittente)", len(c.rules)),
        ("flag NAME_AMBIGUOUS", int((c.name_flags["flag"] == "NAME_AMBIGUOUS").sum()) if not c.name_flags.empty else 0),
        ("flag NEAR_DUP_NAME (solo flag)", int((c.name_flags["flag"] == "NEAR_DUP_NAME").sum()) if not c.name_flags.empty else 0),
    ], columns=["voce", "n"])))
    if c.rules:
        import random

        rng = random.Random(7)
        sample = rng.sample(c.rules, min(30, len(c.rules)))
        w("\n30 merge casuali (audit manuale):\n")
        w(md_table(pd.DataFrame([(r.issuer_key, r.long_key, r.short_key, str(r.valid_from.date()), "" if r.valid_until is None else str(r.valid_until.date())) for r in sample],
                                columns=["issuer_key", "nome lungo", "nome breve", "valido da", "valido fino"])))
    if not c.name_flags.empty:
        near = c.name_flags[c.name_flags["flag"] == "NEAR_DUP_NAME"].head(20)
        if not near.empty:
            w("\nEsempi NEAR_DUP_NAME:\n")
            w(md_table(near[["issuer_key", "detail"]]))
    return "\n".join(out) + "\n"
