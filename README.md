# fi-insider-scanner

**Does an American insider-trading anomaly survive on the Swedish register? Pre-registered answer: no.**

A US Form 4 scanner had produced one result that survived scrutiny: **+3.50% over 126 trading days for
insider purchases in the $50-300M market-cap band (t = 4.30)**. This repository rebuilds that test on
Finansinspektionen's PDMR register (MAR art. 19), Stockholm 2016-2025, with the criteria written down and
committed *before* any forward return was computed.

The answer, on 817 events: **−2.39%** against the index (t = −1.96 clustered by issuer) and **−0.58%**
against a size-matched peer (t = −0.33). The pre-registered rule reads that as **NON REGGE** — it does not
replicate. A placebo run shows the peer comparison is not even neutral, which is part of the finding.

**Status: work in progress.** The pre-registered test is finished and its numbers are frozen — they will
not be re-fitted. The repository around it is still being built: coverage of delisted issuers, a wider
event window and a few checks listed under [Status and open work](#status-and-open-work) are open.

```
uv sync && uv run pytest     # 226 offline tests
uv run fi-scan profile       # pinned snapshot -> report backtest/00_ingest_profile.md
```

---

## Why this repository might interest you

It is a complete research pipeline for a question with a negative answer, built so that the answer can be
trusted and audited:

- **Pre-registration.** The primary cell, the verdict rule and the sha256 of the configuration are written
  to [`backtest/preregistration.md`](backtest/preregistration.md) and committed before the first forward
  return exists. `fi-scan backtest` refuses to run if the configuration changed since.
  ([`prereg.py`](src/fi_insider_scanner/backtest/prereg.py), [`verdict.py`](src/fi_insider_scanner/backtest/verdict.py))
- **One read path, enforced.** Gates, events and controls may only see the register through
  `Register.visible(as_of)`. An AST test fails the build if a decision module mentions a column computed
  with future information (`expost_*`) or reads the row statuses directly.
  ([`visibility.py`](src/fi_insider_scanner/canon/visibility.py), [`test_guards.py`](tests/test_guards.py))
- **Data forensics over trust.** The register has no notification id, so revision chains are inferred and
  scored. Yahoo silently rescales Swedish price history around rights issues, so every ticker is verified
  against the register's own execution prices before it is used.
  ([ADR-014](DECISIONS.md), [ADR-042](DECISIONS.md))
- **Every judgement call is an ADR.** 45 of them in [`DECISIONS.md`](DECISIONS.md), each with context,
  decision, alternatives rejected, consequences, and the test that enforces it.
- **The reports are the product.** Every cell prints n, mean, median, four t statistics, a bootstrap CI and
  the minimum detectable effect, and is flagged when `n < 30`, `|t| < 2` or the mean sits under its MDE.

Language note: code, tests and this README are in English. The analysis output — the reports under
`backtest/`, the ADRs, the case dossier — is in Italian, the language it was written and reasoned in.
Table headers and verdict labels are Italian for the same reason.

### Where to look first

| if you have | read |
|---|---|
| 5 minutes | [`backtest/20_verdict.md`](backtest/20_verdict.md) — the pre-registered criteria, the numbers they were applied to, and nothing else |
| 15 minutes | this page, then [`backtest/preregistration.md`](backtest/preregistration.md) (written before the first return) and [`DECISIONS.md`](DECISIONS.md) ADR-035 |
| 30 minutes | [`visibility.py`](src/fi_insider_scanner/canon/visibility.py) for the point-in-time contract, [`clusters.py`](src/fi_insider_scanner/gates/clusters.py) for a gate, [`run.py`](src/fi_insider_scanner/backtest/run.py) for the measurement, [`test_guards.py`](tests/test_guards.py) for what the build refuses |
| an afternoon | the reports in order, 00 to 20: they are the laboratory notebook, including the parts that did not work |

Everything is reproducible from the pinned snapshot: one upstream commit, one configuration hash, one
bootstrap seed. Network steps cache to disk, so a second run of the whole pipeline is offline and gives
the same numbers to the byte.

---

## The result

Snapshot `27d8523376`, configuration `b67e29d7…`, primary horizon 126 trading sessions, one event per
issuer per 126 calendar days, gross excess return.

| cell | n | mean | median | t iid | t CR1 issuer | 95% CI | MDE |
|---|---:|---:|---:|---:|---:|---:|---:|
| **P — column A, $50-300M, vs OMXSPI** | 817 | **−2.39%** | −4.75% | −1.83 | −1.96 | [−5.00%, +0.12%] | 3.66% |
| C — same events vs size-matched peer | 817 | −0.58% | 0.00% | −0.33 | −0.34 | [−3.80%, +2.54%] | 4.90% |
| A, <$50M vs index / vs peer | 509 | +1.66% / +4.17% | | 0.85 / 1.38 | | | |
| A, >$300M vs index / vs peer | 1,892 | −0.05% / +0.23% | | −0.09 / 0.29 | | | |
| B — cluster gate 4/4, $50-300M | 238 | −1.22% | −3.93% | −0.48 | −0.46 | [−5.70%, +3.80%] | 7.06% |
| Placebo — same issuers, dates −252 sessions, vs peer | 636 | **+4.54%** | +4.88% | **2.31** | 2.23 | [+0.29%, +8.43%] | 5.49% |

Three things the table says, in order of importance:

1. **The US number does not reproduce.** Not in the band, not out of it, not at 21 or 63 sessions, not in
   any of the 16 sensitivity variants (all between −1.75% and −3.39%, none changing sign).
2. **Most of what looks like an insider effect against an index is a size effect.** Year by year, the
   excess against OMXSPI tracks the peers' own excess against OMXSPI: +21% in 2020, −12% in 2025
   ([report 12](backtest/12_matched_control.md)). The US result, also measured against an index, was
   exposed to the same confound — its own matched control had already cut it to +2.41%.
3. **The peer comparison is not neutral either.** Shifting the same events back one year gives +4.54%
   against the peer (t = 2.31). Issuers that will see insider buying a year later were already beating
   their size peers, so C = −0.58% should be read against a positive baseline, not against zero. A
   pipeline that only reported the primary cell would have hidden this.

Honest limits, in the same breath: coverage is 68.3% of events (Yahoo has no series for most delisted
issuers), the column-B cluster test needs ~1,350 events to detect +3.5% and has 238, and the survivorship
scenarios are bounds, not measurements. All of it is in [report 20](backtest/20_verdict.md).

---

## Method in one screen

Three columns come out of one pipeline:

| column | event | gate | role |
|---|---|---|---|
| **A** | (issuer, publication day) with at least one open-market purchase ≥ $25,000 | dilution veto ≠ BLOCKED | exact analogue of the US test — decides the verdict |
| **B** | first publication instant at which ≥ 3 distinct natural persons have bought within 30 days | Layer-1 score 4/4, not stale | the cluster method the brief asked for |
| **C** | same events as A or B | — | peer of the same size band, quiet for 60 days: separates the insider effect from the size effect |

Entry is the first session strictly after the publication day — never a price from before the market could
read the filing. Exit is 126 sessions later. Excess is price return minus `^OMXSPI` price return, both in
SEK; `Adj Close` is reported as an upper bound because no total-return Swedish index has history on Yahoo.

**Layer-1 gates** (column B): cluster of ≥ 3 natural persons in 30 days · not routine (≥ 6 months with
purchases and stable monthly amounts means a plan, not an opinion) · dilution veto (subscriptions visible
in the register, or share count up ≥ 25%) · no large holder. A structural subscription — three or more
people buying at an identical price on the same day with issue evidence — forces the score to zero.

Two gates deserve their asymmetry: MAR does not cover holders above 10%, so `large_holder` is `true` or
`unknown` and never `false`; and the MAR closed period makes post-report buying structural in Europe, so
that flag is an attribute, never a score component.

---

## The data, and what it took to make it usable

Source: [`civictechsweden/oppna-insynsregistret`](https://github.com/civictechsweden/oppna-insynsregistret),
the FI register as open data (CC0), pinned to commit `27d8523376`: 166,210 rows, 22 columns, publications
from 2016-07-04 to 2026-09-13. Never `main` — a pinned commit, with its sha256 checked on load.

| FI column | canonical | what it took |
|---|---|---|
| `Publiceringsdatum` | `published_at` | timestamp of the *version*, not of the notification |
| `Emittent`, `LEI-kod` | `issuer_key` | LEI missing for 63% of 2016 rows; backfilled through ISIN, then through the normalised name |
| `Anmälningsskyldig` | `notifier_name`, `associate_kind` | 34,387 rows filed by vehicles, 7,183 by family members — attributed to the PDMR, never counted as extra people |
| `Person i ledande ställning` | `person_key` | conservative middle-name merges, point-in-time; 6,501 rows carry a company name and are excluded from person counts |
| `Befattning` | `roles` | free text until ~2020 (3,863 distinct values), a fixed list of 9 from 2023 |
| `Karaktär` | `txn_kind` | 41 values mapped; only `Förvärv` can ever be a signal; an unmapped value is never one |
| `Instrumenttyp` | `instrument_type` + `type_source` | empty for all of 2016-17: inferred from the ISIN's other rows (unanimous, then ≥ 90% majority), then from the instrument name |
| `Instrumentnamn` | `share_class` | `ser. B`, `serie B`, trailing `B`, pref, SDB; 53 ISINs carry conflicting classes |
| `Pris`, `Valuta` | `price`, `currency` | native currency kept; SEK for 95% of rows, then CAD, EUR, USD |
| `Handelsplats` | `venue_class` | a venue *name*, not a MIC; `Utanför handelsplats` on 37% of rows |
| `Status` | `chain_status` | Aktuell / Reviderad / Makulerad, with the correction chains inferred |

Four problems that shaped the code:

1. **No notification id.** Corrections are linked one-to-one to the version they correct by scoring the
   fields (ISIN 3, instrument name 2, kind 2, volume/price/venue 1); ties are left unlinked rather than
   guessed. 9,036 links, 60 ambiguous. ([`chains.py`](src/fi_insider_scanner/canon/chains.py))
2. **Upstream statuses go stale.** The public mirror refetches only three days, so a row corrected later
   keeps `Aktuell`. After a documented horizon the pipeline infers supersession itself.
3. **Nine broken records** (a newline inside a field, 2018 and 2020). They are quarantined with their line
   numbers, not repaired: the matching halves are not adjacent and pairing them would be a guess.
4. **Yahoo rescales history.** Securitas 1.20×, Dustin 2.0×, Scandic 1.4× before their rights issues — not
   in `Stock Splits`. Found by verifying tickers against the register's own execution prices; the scale
   segments are estimated from that same comparison, and market caps use the register price.
   ([ADR-042](DECISIONS.md), [`prices.py`](src/fi_insider_scanner/market/prices.py))

The only direct access to FI's own service is an incremental export used for the current-quarter case: one
thread, 5-second pauses, at most 20 requests, windows halved to stay under the silent 1,000-row cap, and a
hard error instead of a truncated page. ([`fi_export.py`](src/fi_insider_scanner/ingest/fi_export.py))

---

## Layout

```
src/fi_insider_scanner/
  ingest/    bulk snapshot · raw CSV parser (record identity, quarantine) · FI export client · refresh · profile
  canon/     value parsers · taxonomies · names · share class · row mapping (Pydantic) · revision chains · visibility
  market/    yfinance cache · FX · Nasdaq listings · ticker resolution · price rescaling · market cap · enrichment
  gates/     open-market predicates · structural subscription · clusters · dilution · routine · large holder · closed period · score
  backtest/  events · returns · matched control · statistics · survivorship · placebo · pre-registration · verdict · reports
  dossier/   case selection and the WHO / WHERE / WHEN write-up
backtest/    00 ingest profile · 01 canonical · 02 dry run · 03 resolution · 05 gates+mcap · preregistration · 10 A · 11 B · 12 control · 13 survivorship · 20 verdict
dossier/     candidates and the case dossier
tests/       226 offline tests, including AST guards and snapshot invariants
config/      pipeline.toml — every threshold, frozen by the pre-registration
```

Storage is SQLite plus gzipped snapshots plus per-ticker CSV caches, all under `data/` and git-ignored:
the repository holds code, configuration, reports and decisions, and every artefact can be rebuilt from the
pinned snapshot.

## Running it

```bash
uv sync
uv run pytest                 # 226 offline tests, no network
uv run fi-scan ingest         # pinned snapshot -> data/raw/bulk (42 MB)
uv run fi-scan profile        # report 00: counts, invariants, per-year regimes
uv run fi-scan canon          # canonical table -> data/fi.sqlite, report 01
uv run fi-scan events-dryrun  # report 02: events and clusters, register + FX only
uv run fi-scan resolve        # ISIN -> verified .ST ticker (network, resumable, ~1 h cold)
uv run fi-scan enrich         # share counts and report dates (network, resumable)
uv run fi-scan gates-mcap     # report 05: gates with market data, no returns yet
uv run fi-scan freeze         # write the pre-registration, then commit it
uv run fi-scan backtest       # reports 10-13 and the verdict
uv run fi-scan refresh        # polite FI incremental export (case zero only)
uv run fi-scan case-zero      # candidate list and dossier
```

The network steps are resumable and write through to the cache, so an interrupted `resolve` or `enrich`
picks up where it stopped.

## Performance

The hot paths were profiled and rewritten; the reports come out byte-identical apart from their timestamps.

| path | before | after | what changed |
|---|---:|---:|---|
| `attach_mcap` | 15.6 ms/event | 5.0 ms/event | the execution price was found by scanning all 166k register rows per event; now a dict lookup, and split ratios are cached per symbol |
| `detect_clusters`, large issuer | 3.33 s | 0.69 s | sliding window instead of a quadratic scan; the structural-subscription grouping runs only once a window is found |
| `detect_clusters`, mid issuer | 265 ms | 97 ms | the visible slice is cut to the last year before the masks, and `person_key` is precomputed when an issuer has no merge rules |
| `Pool.at` (peer pool) | 2.7 ms/event | ~0 ms | band labels computed once for the whole panel; peer selection on numpy arrays |
| `event_return` | 2.1 ms/event | 1.6 ms/event | numpy views instead of a per-call column cast |

`find_window` is checked against a brute-force reference on 40 random inputs, so the fast path cannot
silently disagree with the obvious one. ([`test_fastpaths.py`](tests/test_fastpaths.py))

## Tests

```
pytest -q            # 226 tests, offline
pytest -m snapshot   # snapshot checks against the pinned data
ruff check . && ruff format --check .
```

GitHub Actions runs the linter, the formatter check and the offline suite on every push
([`.github/workflows/ci.yml`](.github/workflows/ci.yml)).

Beyond the unit tests of parsing, dedup, share class, gates, returns and statistics, three families are
worth naming: **guards** (no import or path from another repository; no `expost_` column in a decision
module; no recommendation vocabulary in a generated dossier), **equivalence** (the optimised window search
against the naive one), and **point-in-time** (a gate fed the full history with an `as_of` must agree with
the same gate fed only the data up to `as_of`).

## Status and open work

Done, and frozen: ingest and canonical schema, Layer-1 gates, the pre-registered backtest with its matched
control, survivorship bounds and placebo, the verdict, and one case dossier. The primary cell will not be
re-estimated — a new question means a new pre-registration, not a new fit of this one.

Open, in the order I intend to take them:

1. **Delisted coverage.** 41% of column-A events have no usable price series, because Yahoo drops issuers
   that disappear. Today this is handled with bounds (scenarios and a break-even share); a delisting list
   with last prices would turn the bounds into measurements. This is the single change that could most
   affect the reading of the result.
2. **The truncation-invariance test** planned at design time and not yet written: replay 200 random events
   against a register physically cut at `as_of` and assert the gates agree with the point-in-time path.
   The guarantee is currently carried by unit tests and the AST guard, which is weaker.
3. **Statistical power for column B.** 238 events in band against roughly 1,350 needed for +3.5%. Either a
   longer window as the register grows, or the same pipeline pointed at Oslo and Helsinki, which publish
   comparable MAR art. 19 registers.
4. **A total-return benchmark.** `^OMXSPI` is a price index; the `Adj Close` variant is reported as an
   upper bound rather than a correction.
5. **The 2024 notification threshold** (EUR 5,000 to 20,000, ADR-040) is visible in the per-year tables but
   not corrected for.
6. **Operational use of the polite FI client** — a weekly refresh that lists new clusters — is written and
   run by hand; it is not scheduled.

No language model is used anywhere in the pipeline: token cost per run is zero, and every number comes
from deterministic code over public data.

## License and data

Code: [MIT](LICENSE). Register data: CC0, from the upstream mirror; no upstream code is copied or executed.
Market data comes from Yahoo Finance through `yfinance` and is cached locally for reproducibility, not
redistributed. This repository produces measurements and a dossier: no orders, no recommendations, and the
verdict is about one number replicating, nothing else.

Author: Simone Datola. Corrections, and arguments against the reading of the result, are welcome as issues —
a negative result is only useful if it can be attacked.
