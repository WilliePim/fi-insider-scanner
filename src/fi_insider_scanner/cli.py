"""`fi-scan`: one command per checkpoint of the study.

Handlers import lazily so that `fi-scan --help` stays instant, and each one prints the artefact it wrote.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

from . import config


def _pinned_snapshot():
    """Parse the pinned bulk snapshot, refusing to continue if its sha256 moved."""
    from .ingest import bulk
    from .ingest.rawcsv import parse_register_csv

    source = config.load()["source"]
    data, snapshot = bulk.load(source["pinned_commit"])
    if snapshot.sha256 != source["pinned_sha256"]:
        raise SystemExit(f"snapshot sha256 {snapshot.sha256} differs from the pinned one in config/pipeline.toml")
    return parse_register_csv(data), snapshot


def cmd_ingest(args: argparse.Namespace) -> None:
    from .ingest import bulk

    snapshot = bulk.download(args.commit or config.load()["source"]["pinned_commit"])
    print(f"snapshot {snapshot.commit_sha[:10]} sha256={snapshot.sha256} bytes={snapshot.n_bytes:,} -> {snapshot.path}")


def cmd_profile(args: argparse.Namespace) -> None:
    from .ingest.profile import build_profile

    raw, snapshot = _pinned_snapshot()
    out = config.BACKTEST_DIR / "00_ingest_profile.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build_profile(raw, snapshot), encoding="utf-8")
    print(f"rows {len(raw.rows):,}, quarantined {len(raw.quarantine)} -> {out}")


def cmd_canon(args: argparse.Namespace) -> None:
    from . import store
    from .canon.build import build_canonical
    from .canon.report import build_report

    raw, snapshot = _pinned_snapshot()
    cfg = config.load()
    canonical = build_canonical(raw.rows, "bulk", snapshot.commit_sha[:10], cfg["source"]["stale_status_horizon"])
    store.save_frame("transactions", canonical.df)
    store.save_frame("quarantine", raw.quarantine)
    store.save_frame("mapping_rejects", canonical.rejects)
    store.save_frame("chain_links", canonical.chain_stats.links)
    store.save_frame("name_flags", canonical.name_flags)
    store.save_rules(canonical.rules)
    store.save_meta("canonical", {"snapshot": snapshot.commit_sha, "sha256": snapshot.sha256, "rows": len(canonical.df)})
    out = config.BACKTEST_DIR / "01_canonical.md"
    out.write_text(build_report(canonical, snapshot.commit_sha[:10]), encoding="utf-8")
    print(f"rows {len(canonical.df):,}, correction links {canonical.chain_stats.linked:,}, name merges {len(canonical.rules):,} -> {out}")


def cmd_events_dryrun(args: argparse.Namespace) -> None:
    from . import pipeline, store
    from .backtest import dryrun

    a, b, markdown = dryrun.run(config.load(), pipeline.register)
    store.save_frame("events_a_dry", a)
    store.save_frame("events_b_dry", b)
    a.to_csv(config.BACKTEST_DIR / "02_events_a_dry.csv", index=False)
    b.to_csv(config.BACKTEST_DIR / "02_events_b_dry.csv", index=False)
    out = config.BACKTEST_DIR / "02_events_dryrun.md"
    out.write_text(markdown, encoding="utf-8")
    print(f"A {len(a):,} events, B {len(b):,} triggers -> {out}")


def cmd_resolve(args: argparse.Namespace) -> None:
    """ISIN -> verified .ST ticker. Network-bound, resumable: partial results are stored per shard."""
    import contextlib
    from dataclasses import asdict

    import pandas as pd

    from . import store
    from .market import nasdaq, resolve

    cfg = config.load()
    transactions = store.load_frame("transactions")
    done_frames = []
    for table in ["resolution_partial", *[f"resolution_partial_{k}" for k in range(8)]]:
        with contextlib.suppress(Exception):  # the table is absent on a first run
            done_frames.append(store.load_frame(table))
    done = pd.concat(done_frames, ignore_index=True).drop_duplicates("isin") if done_frames else None
    table = "resolution_partial" if args.shard is None else f"resolution_partial_{args.shard}"
    collected: list[dict] = []

    def progress(i: int, n: int, resolution) -> None:
        collected.append(asdict(resolution))
        if len(collected) % 50 == 0:
            store.save_frame(table, pd.DataFrame(collected))
            verified = sum(1 for r in collected if r["verified"] is True)
            print(f"{i}/{n} ISIN, verified {verified}/{len(collected)} (shard {args.shard})", flush=True)

    result = resolve.resolve_all(
        transactions, nasdaq.listings(), cfg["resolver"], done=done, progress=progress, shard=args.shard, nshards=args.nshards
    )
    if collected:
        store.save_frame(table, pd.DataFrame(collected))
    if args.shard is not None:
        print(f"shard {args.shard} done: {len(collected)} new ISIN")
        return
    store.save_frame("resolution", result)
    result.to_csv(config.CACHE_DIR / "resolution.csv", index=False)
    verified = int(result["verified"].eq(True).sum())
    print(f"ISIN {len(result):,}: verified {verified:,}, unverifiable {int(result['verified'].isna().sum()):,}")


def cmd_enrich(args: argparse.Namespace) -> None:
    from . import store
    from .market import enrich

    symbols = enrich.usable_symbols(store.load_frame("resolution"))
    print(enrich.enrich(symbols, progress=lambda i, stats: print(f"{i}/{len(symbols)} {stats}", flush=True)))


def cmd_gates_mcap(args: argparse.Namespace) -> None:
    from .backtest import main as backtest_main

    backtest_main.gates_mcap(config.load())
    print("-> backtest/05_gates_mcap.md")


def cmd_freeze(args: argparse.Namespace) -> None:
    from .backtest import main as backtest_main

    backtest_main.freeze(config.load())
    print(f"config sha256 {config.config_sha256()} -> backtest/preregistration.md (commit it before the backtest)")


def cmd_backtest(args: argparse.Namespace) -> None:
    """Refuses to run unless the pre-registration exists and still matches the configuration."""
    from .backtest import main as backtest_main

    prereg = config.BACKTEST_DIR / "preregistration.md"
    if not prereg.exists():
        raise SystemExit("backtest/preregistration.md missing: run `fi-scan freeze` and commit it first")
    if config.config_sha256() not in prereg.read_text(encoding="utf-8"):
        raise SystemExit("config/pipeline.toml changed after pre-registration: that needs a new ADR and a new freeze")
    print(backtest_main.backtest(config.load()))


def cmd_refresh(args: argparse.Namespace) -> None:
    from .ingest.refresh import refresh

    print(refresh(args.lookback))


def cmd_case_zero(args: argparse.Namespace) -> None:
    from .dossier.case import run_case_zero

    result = run_case_zero(config.load(), use_pinned=args.pinned)
    if result.case is None:
        print(f"no candidate passes the gates in the window -> {result.candidates_path}")
        return
    case = result.case
    print(f"case zero: {case['issuer_name']} T={case['as_of']} band={case['band']} -> {result.dossier_path}")


@dataclass(frozen=True)
class Command:
    name: str
    help: str
    run: Callable[[argparse.Namespace], None]
    arguments: Sequence[tuple[tuple[str, ...], dict]] = field(default_factory=tuple)


def commands() -> list[Command]:
    cfg = config.load()
    return [
        Command(
            "ingest",
            "download the bulk snapshot (default: the pinned commit)",
            cmd_ingest,
            [(("--commit",), {"default": None, "help": "upstream commit to pin instead"})],
        ),
        Command("profile", "checkpoint 1: profile of the pinned snapshot", cmd_profile),
        Command("canon", "checkpoint 2: canonical table in data/fi.sqlite", cmd_canon),
        Command("events-dryrun", "checkpoint 3: events and cluster triggers without prices", cmd_events_dryrun),
        Command(
            "resolve",
            "checkpoint 4: ISIN -> verified .ST ticker (long, resumable)",
            cmd_resolve,
            [
                (("--shard",), {"type": int, "default": None, "help": "shard index; without it, merge and finish"}),
                (("--nshards",), {"type": int, "default": 1}),
            ],
        ),
        Command("enrich", "checkpoint 5: share counts and report dates for resolved tickers (long)", cmd_enrich),
        Command("gates-mcap", "checkpoint 6: gates with market data and bands, no returns", cmd_gates_mcap),
        Command("freeze", "checkpoint 6b: pre-registration (config sha256 and verdict criteria)", cmd_freeze),
        Command("backtest", "checkpoints 7-10: returns, control, survivorship, placebo, verdict", cmd_backtest),
        Command(
            "refresh",
            "case zero: polite FI incremental export (one thread, 5 s pauses, 20 requests)",
            cmd_refresh,
            [(("--lookback",), {"type": int, "default": cfg["caso_zero"]["refresh_lookback_days"]})],
        ),
        Command(
            "case-zero",
            "case zero: declared selection and dossier",
            cmd_case_zero,
            [(("--pinned",), {"action": "store_true", "help": "use the pinned snapshot instead of the refreshed database"})],
        ),
    ]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="fi-scan", description="Swedish PDMR register: ingest, gates, backtest, dossier")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in commands():
        sub = subparsers.add_parser(command.name, help=command.help)
        for flags, options in command.arguments:
            sub.add_argument(*flags, **options)
        sub.set_defaults(func=command.run)
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main(sys.argv[1:])
