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
    try:
        done = store.load_frame("resolution_partial")
    except Exception:  # noqa: BLE001 - tabella assente al primo avvio
        done = None
    collected = [] if done is None else done.to_dict("records")

    def progress(i, n, res):
        collected.append(asdict(res))
        if len(collected) % 100 == 0:
            store.save_frame("resolution_partial", pd.DataFrame(collected))
            ok = sum(1 for r in collected if r["verified"] is True)
            print(f"{i}/{n} ISIN, verificati {ok}/{len(collected)}", flush=True)

    result = resolve.resolve_all(df, nasdaq.listings(), cfg["resolver"], done=done, progress=progress)
    store.save_frame("resolution_partial", pd.DataFrame(collected))
    store.save_frame("resolution", result)
    result.to_csv(config.CACHE_DIR / "resolution.csv", index=False)
    print(f"ISIN {len(result):,}: verified True {int((result['verified'] == True).sum()):,}, None {int(result['verified'].isna().sum()):,}")  # noqa: E712


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
    p.set_defaults(func=cmd_resolve)
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main(sys.argv[1:])
