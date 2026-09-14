"""CLI `fi-scan`."""

from __future__ import annotations

import argparse
import sys

from . import config


def _pinned_raw():
    from .ingest import bulk
    from .ingest.rawcsv import parse_register_csv

    src = config.load()["source"]
    data, snap = bulk.load(src["pinned_commit"])
    if snap.sha256 != src["pinned_sha256"]:
        raise SystemExit(f"sha256 dello snapshot ({snap.sha256}) diverso da quello pinnato in config")
    return parse_register_csv(data), snap


def cmd_ingest(args: argparse.Namespace) -> None:
    from .ingest import bulk

    snap = bulk.download(args.commit or config.load()["source"]["pinned_commit"])
    print(f"snapshot {snap.commit_sha[:10]} sha256={snap.sha256} byte={snap.n_bytes:,} -> {snap.path}")


def cmd_profile(args: argparse.Namespace) -> None:
    from .ingest.profile import build_profile

    raw, snap = _pinned_raw()
    out = config.BACKTEST_DIR / "00_ingest_profile.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build_profile(raw, snap), encoding="utf-8")
    print(f"righe {len(raw.rows):,}, quarantena {len(raw.quarantine)} -> {out}")


def cmd_canon(args: argparse.Namespace) -> None:
    from . import store
    from .canon.build import build_canonical
    from .canon.report import build_report

    raw, snap = _pinned_raw()
    cfg = config.load()
    c = build_canonical(raw.rows, "bulk", snap.commit_sha[:10], cfg["source"]["stale_status_horizon"])
    store.save_frame("transactions", c.df)
    store.save_frame("quarantine", raw.quarantine)
    store.save_frame("mapping_rejects", c.rejects)
    store.save_frame("chain_links", c.chain_stats.links)
    store.save_frame("name_flags", c.name_flags)
    store.save_rules(c.rules)
    store.save_meta("canonical", {"snapshot": snap.commit_sha, "sha256": snap.sha256, "rows": len(c.df)})
    out = config.BACKTEST_DIR / "01_canonical.md"
    out.write_text(build_report(c, snap.commit_sha[:10]), encoding="utf-8")
    print(f"righe {len(c.df):,}, link {c.chain_stats.linked:,}, merge {len(c.rules):,} -> {out}")


def cmd_events_dryrun(args: argparse.Namespace) -> None:
    from . import pipeline, store
    from .backtest import dryrun

    cfg = config.load()
    a, b, md = dryrun.run(cfg, pipeline.register)
    store.save_frame("events_a_dry", a)
    store.save_frame("events_b_dry", b)
    a.to_csv(config.BACKTEST_DIR / "02_events_a_dry.csv", index=False)
    b.to_csv(config.BACKTEST_DIR / "02_events_b_dry.csv", index=False)
    out = config.BACKTEST_DIR / "02_events_dryrun.md"
    out.write_text(md, encoding="utf-8")
    print(f"A {len(a):,} eventi, B {len(b):,} trigger -> {out}")


def cmd_resolve(args: argparse.Namespace) -> None:
    from dataclasses import asdict

    import pandas as pd

    from . import store
    from .market import nasdaq, resolve

    cfg = config.load()
    df = store.load_frame("transactions")
    partial_tables = ["resolution_partial"] + [f"resolution_partial_{k}" for k in range(8)]
    frames = []
    for name in partial_tables:
        try:
            frames.append(store.load_frame(name))
        except Exception:  # noqa: BLE001 - tabella assente
            pass
    done = pd.concat(frames, ignore_index=True).drop_duplicates("isin") if frames else None
    table = "resolution_partial" if args.shard is None else f"resolution_partial_{args.shard}"
    collected: list[dict] = []

    def progress(i, n, res):
        collected.append(asdict(res))
        if len(collected) % 50 == 0:
            store.save_frame(table, pd.DataFrame(collected))
            ok = sum(1 for r in collected if r["verified"] is True)
            print(f"{i}/{n} ISIN, verificati {ok}/{len(collected)} (shard {args.shard})", flush=True)

    result = resolve.resolve_all(df, nasdaq.listings(), cfg["resolver"], done=done, progress=progress,
                                 shard=args.shard, nshards=args.nshards)
    if collected:
        store.save_frame(table, pd.DataFrame(collected))
    if args.shard is not None:
        print(f"shard {args.shard} completato: {len(collected)} ISIN nuovi")
        return
    store.save_frame("resolution", result)
    result.to_csv(config.CACHE_DIR / "resolution.csv", index=False)
    print(f"ISIN {len(result):,}: verified True {int((result['verified'] == True).sum()):,}, None {int(result['verified'].isna().sum()):,}")  # noqa: E712


def cmd_enrich(args: argparse.Namespace) -> None:
    from . import store
    from .market import enrich

    symbols = enrich.usable_symbols(store.load_frame("resolution"))
    stats = enrich.enrich(symbols, progress=lambda i, s: print(f"{i}/{len(symbols)} {s}", flush=True))
    print(stats)


def cmd_gates_mcap(args: argparse.Namespace) -> None:
    from .backtest import main as bt

    bt.gates_mcap(config.load())
    print("-> backtest/05_gates_mcap.md")


def cmd_freeze(args: argparse.Namespace) -> None:
    from .backtest import main as bt

    bt.freeze(config.load())
    print(f"config sha256 {config.config_sha256()} -> backtest/preregistration.md (da committare prima del backtest)")


def cmd_backtest(args: argparse.Namespace) -> None:
    from .backtest import main as bt

    prereg = config.BACKTEST_DIR / "preregistration.md"
    if not prereg.exists():
        raise SystemExit("manca backtest/preregistration.md: eseguire `fi-scan freeze` e committare prima")
    if config.config_sha256() not in prereg.read_text(encoding="utf-8"):
        raise SystemExit("config/pipeline.toml è cambiato dopo la pre-registrazione: serve un nuovo ADR e un nuovo freeze")
    print(bt.backtest(config.load()))


def cmd_refresh(args: argparse.Namespace) -> None:
    from .ingest.refresh import refresh

    print(refresh(args.lookback))


def cmd_caso_zero(args: argparse.Namespace) -> None:
    import re

    import pandas as pd

    from . import pipeline, store
    from .backtest import main as bt
    from .backtest import run
    from .backtest.events import build_b_events
    from .canon.visibility import Register
    from .dossier import build as dz
    from .gates.openmarket import b_row
    from .ingest.refresh import REFRESHED_DB

    cfg = config.load()
    cz = cfg["caso_zero"]
    db = None if args.pinned or not REFRESHED_DB.exists() else REFRESHED_DB
    note = "snapshot pinnato" if db is None else f"snapshot pinnato + refresh FI ({store.load_meta('refresh', db)['window']})"
    env = bt.load_env(cfg, db)
    df = pipeline.canonical_with_values() if db is None else pipeline.canonical_from(db)
    rules = store.load_rules(db)
    start = pd.Timestamp(cz["window_start"]) - pd.Timedelta(days=cfg["cluster"]["window_days"] + 5)
    cand = df[b_row(df) & (df["trade_date"] >= start)]
    keys = set(cand["issuer_key"])
    reg = Register(df[df["issuer_key"].isin(keys)], rules)
    print(f"{note}; emittenti con acquisti on-venue dal {start.date()}: {len(keys)}", flush=True)
    b = build_b_events(reg, cfg, env.market)
    b = run.attach_mcap(b, env, "anchor")
    b["gate_ok"] = b["score"].eq(4) & ~b["is_stale"]
    sel = dz.select_case(b, cfg)
    config.DOSSIER_DIR.mkdir(exist_ok=True)
    cols = ["issuer_name", "as_of", "anchor", "n_persons", "value_sek", "score", "is_stale", "symbol", "verified", "mcap_usd", "band", "dilution", "s3_in_window"]
    ranked = sel.candidates[cols].copy()
    ranked["mcap_usd"] = (ranked["mcap_usd"] / 1e6).round(0)
    from .mdtable import md_table

    header = "# Candidati caso zero" + chr(10) * 2 + "Regola: " + sel.rule + "." + chr(10) * 2 + "Fonte: " + note + "." + chr(10) * 2
    (config.DOSSIER_DIR / f"{cz['window_end']}_candidati.md").write_text(header + md_table(ranked.astype({"as_of": str, "anchor": str})) + chr(10), encoding="utf-8")
    if sel.case is None:
        print("nessun candidato che passa i gate nella finestra")
        return
    case = sel.case
    sym = case["symbol"]
    shares_out = env.market.shares(sym)
    shares_out = None if shares_out is None or shares_out.empty else float(shares_out[shares_out.index <= pd.Timestamp(case["as_of"]) - pd.Timedelta(days=cfg["dilution"]["shares_lag_days"])].iloc[-1]) if (shares_out[shares_out.index <= pd.Timestamp(case["as_of"]) - pd.Timedelta(days=cfg["dilution"]["shares_lag_days"])]).size else None
    slug = re.sub(r"[^a-z0-9]+", "-", str(case["issuer_name"]).lower()).strip("-")[:40]
    sources = dz.load_sources(config.DOSSIER_DIR / f"{slug}_sources.json")
    md = dz.build_dossier(case, reg, cfg, shares_out, env.market.reports(sym), sources, sel.in_band, sel.rule, note)
    out = config.DOSSIER_DIR / f"{cz['window_end']}_{slug}.md"
    out.write_text(md, encoding="utf-8")
    print(f"caso zero: {case['issuer_name']} T={case['as_of']} banda={case['band']} -> {out}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="fi-scan")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("ingest", help="scarica lo snapshot bulk (default: commit pinnato)")
    p.add_argument("--commit", default=None)
    p.set_defaults(func=cmd_ingest)
    p = sub.add_parser("profile", help="checkpoint 1: profilo dello snapshot pinnato")
    p.set_defaults(func=cmd_profile)
    p = sub.add_parser("canon", help="checkpoint 2: tabella canonica in data/fi.sqlite")
    p.set_defaults(func=cmd_canon)
    p = sub.add_parser("events-dryrun", help="checkpoint 3: eventi A e trigger B senza prezzi")
    p.set_defaults(func=cmd_events_dryrun)
    p = sub.add_parser("resolve", help="checkpoint 4: ISIN -> ticker .ST verificato (lungo, riprende da cache)")
    p.add_argument("--shard", type=int, default=None, help="indice shard (senza: unisce e completa)")
    p.add_argument("--nshards", type=int, default=1)
    p.set_defaults(func=cmd_resolve)
    p = sub.add_parser("enrich", help="checkpoint 5: azioni e date report per i ticker risolti (lungo)")
    p.set_defaults(func=cmd_enrich)
    p = sub.add_parser("gates-mcap", help="checkpoint 6: gate con dati di mercato e bande (nessun rendimento)")
    p.set_defaults(func=cmd_gates_mcap)
    p = sub.add_parser("freeze", help="checkpoint 6b: pre-registrazione (sha256 config + criteri)")
    p.set_defaults(func=cmd_freeze)
    p = sub.add_parser("backtest", help="checkpoint 7-10: rendimenti, control, survivorship, placebo, verdetto")
    p.set_defaults(func=cmd_backtest)
    p = sub.add_parser("refresh", help="caso zero: export incrementale FI (un thread, pausa 5 s, max 20 richieste)")
    p.add_argument("--lookback", type=int, default=config.load()["caso_zero"]["refresh_lookback_days"])
    p.set_defaults(func=cmd_refresh)
    p = sub.add_parser("caso-zero", help="caso zero: selezione dichiarata e dossier")
    p.add_argument("--pinned", action="store_true", help="usa lo snapshot pinnato invece del DB rinfrescato")
    p.set_defaults(func=cmd_caso_zero)
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main(sys.argv[1:])
