"""Checkpoint 3: event dry-run on register data and FX only (no share prices)."""

from __future__ import annotations

import unicodedata
from datetime import UTC, datetime

import pandas as pd

from ..mdtable import md_table
from .events import apply_cooldown, build_a_events, build_b_events
from .stats import mde

US_SD = 0.46


def _fold(name: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", name) if not unicodedata.combining(c))


def near_dup_persons(b: pd.DataFrame) -> pd.Series:
    """True when two persons of the cluster coincide up to their diacritics (a possible double count)."""
    return b["persons"].map(lambda s: len({_fold(p) for p in s.split("|")}) < len(s.split("|")))


def by_year(df: pd.DataFrame, col: str = "event_day") -> pd.Series:
    return df[col].dt.year.value_counts().sort_index()


def build_report(cfg: dict, a: pd.DataFrame, b: pd.DataFrame, b_seen: pd.DataFrame, b_first: pd.DataFrame) -> str:
    cooldown = cfg["backtest"]["cooldown_calendar_days"]
    out: list[str] = []
    w = out.append
    w("# 02 — Dry-run eventi (solo registro + FX)\n")
    w(
        f"Generato {datetime.now(UTC).isoformat(timespec='seconds')}. Nessun prezzo azionario usato. "
        "Senza dati di mercato la crescita azioni del dilution veto e la soglia 10% del grande azionista restano "
        "sconosciute: qui BLOCKED viene solo da partecipazione/trappola nel registro e `large_holder` solo dalle parole chiave.\n"
    )

    w("## Colonna A — eventi (emittente, giorno di pubblicazione) con ≥ 1 riga A_exact\n")
    a_b = apply_cooldown(a, cooldown)
    t = (
        pd.DataFrame(
            {
                "eventi (a)": by_year(a),
                "variante (b)": by_year(a_b),
                "con riga on-venue": by_year(a[a["has_onvenue_row"]]),
                "BLOCKED (registro)": by_year(a[a["dilution"] == "BLOCKED"]),
            }
        )
        .fillna(0)
        .astype(int)
    )
    t.loc["totale"] = t.sum()
    w(md_table(t.rename_axis("anno").reset_index().astype({"anno": str}), digits=0))
    w(
        f"\nRighe per evento: mediana {a['n_rows'].median():.0f}, p90 {a['n_rows'].quantile(0.9):.0f}. "
        f"Valore USD per evento: mediana {a['value_usd'].median():,.0f}.\n"
    )

    w("\n## Colonna B — trigger cluster (snapshot, timing pub)\n")
    b_primary = b[(~b["is_stale"]) & (b["score"] == 4)]
    t = (
        pd.DataFrame(
            {
                "trigger": by_year(b),
                "stale (>30 gg)": by_year(b[b["is_stale"]]),
                "S3 nella finestra": by_year(b[b["s3_in_window"]]),
                "prezzo uniforme on-venue": by_year(b[b["uniform_onvenue"]]),
                "BLOCKED (registro)": by_year(b[b["dilution"] == "BLOCKED"]),
                "routine < 3 non-routine": by_year(b[~b["not_routine"]]),
                "grande azionista (parole chiave)": by_year(b[~b["no_large_holder"]]),
                "4/4 non stale": by_year(b_primary),
                "4/4 non stale, variante (b)": by_year(apply_cooldown(b_primary, cooldown)),
            }
        )
        .fillna(0)
        .astype(int)
    )
    t.loc["totale"] = t.sum()
    w(md_table(t.rename_axis("anno").reset_index().astype({"anno": str}), digits=0))
    w("\nDistribuzione dello score Layer 1 (tutti i trigger):\n")
    w(md_table(b["score"].value_counts().sort_index().rename_axis("score").reset_index(name="n")))
    w("\nPersone per cluster:\n")
    w(md_table(b["n_persons"].clip(upper=8).value_counts().sort_index().rename_axis("persone (8 = 8+)").reset_index(name="n")))
    nd = near_dup_persons(b)
    w(
        f"\nTrigger con due persone uguali a meno dei diacritici (possibile doppio conteggio): **{int(nd.sum())}**; "
        f"di questi con esattamente 3 persone (sparirebbero unendo i nomi): **{int((nd & (b['n_persons'] == 3)).sum())}**.\n"
    )
    w(
        "\nConfronto con la stima grezza dello Step 0 (~3.300 cluster: ≥3 PDMR, Förvärv Aktie Aktuell non-programma, "
        "qualunque venue, nessuna esclusione di entità né di S3, cooldown 30 gg): "
        f"qui {len(b):,} trigger con persone fisiche, righe on-venue, azioni inferite anche nel 2016-18 e S3 escluso.\n"
    )

    w("\n## Colonna B — robustezza di visibilità e timing\n")
    t = (
        pd.DataFrame(
            {
                "snapshot + pub": by_year(b),
                "as_seen + pub": by_year(b_seen),
                "snapshot + first_pub": by_year(b_first),
                "snapshot + pub, 4/4 non stale": by_year(b_primary),
                "as_seen + pub, 4/4 non stale": by_year(b_seen[(~b_seen["is_stale"]) & (b_seen["score"] == 4)]),
                "first_pub, 4/4 non stale": by_year(b_first[(~b_first["is_stale"]) & (b_first["score"] == 4)]),
            }
        )
        .fillna(0)
        .astype(int)
    )
    t.loc["totale"] = t.sum()
    w(md_table(t.rename_axis("anno").reset_index().astype({"anno": str}), digits=0))

    w("\n## Potenza: effetto minimo rilevabile (MDE)\n")
    w(f"MDE = (1,96 + 0,84) · sd / √n con la sd USA a 126 giorni ({US_SD:.0%}). Il finding USA è +3,50%.\n")
    rows = [(n, mde(US_SD, n)) for n in (30, 100, 300, 600, 1000, 1350, 2000, 3213)]
    w(md_table(pd.DataFrame([(n, f"{m:.2%}") for n, m in rows], columns=["n eventi", "MDE"])))
    w("\nIl numero di eventi in banda $50-300M si conosce solo dopo market cap (checkpoint 6).\n")
    return "\n".join(out) + "\n"


def run(cfg: dict, register_fn) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    reg = register_fn("snapshot", "pub")
    a = build_a_events(reg, cfg)
    b = build_b_events(reg, cfg)
    b_seen = build_b_events(register_fn("as_seen", "pub"), cfg)
    b_first = build_b_events(register_fn("snapshot", "first_pub"), cfg)
    return a, b, build_report(cfg, a, b, b_seen, b_first)
