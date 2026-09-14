# fi-insider-scanner

Registro insider svedese (FI Insynsregistret, MAR art. 19): ingest canonico, gate Layer 1, backtest
event-time su Stoccolma 2016-2025, dossier WHO / WHERE / WHEN per un caso reale.

Repo autonomo: nessun import né path condiviso con altri progetti (test AST in `tests/test_guards.py`).
Nessun ordine, nessuna raccomandazione: il verdetto del backtest è pre-registrato e riguarda solo la
replica di un numero; il dossier non contiene giudizi.

## Domanda

Lo scanner USA su Form 4 aveva un solo numero sopravvissuto allo scrutinio: **+3,50% a 126 giorni di
borsa nella banda di market cap $50-300M (t = 4,30)**. Quel numero non era un test "cluster": era
"ogni acquisto open market ≥ $25.000, non bloccato dal dilution veto, uno per emittente ogni 126
giorni, eccesso iid contro IWM". Il suo matched control lo aveva già ridotto a +2,41% (t = 2,02).
Qui si replica la stessa definizione sulla Svezia (**colonna A**, primaria), si misura la versione
cluster del metodo (**colonna B**) e si affianca a entrambe un peer della stessa dimensione
(**colonna C**). Se non regge, è un risultato.

## Dove leggere i risultati

| file | contenuto |
|---|---|
| `backtest/preregistration.md` | cella primaria, criteri di verdetto, sha256 della configurazione, **scritti prima dei rendimenti** |
| `backtest/20_verdict.md` | verdetto (REGGE / NON REGGE / INCONCLUSIVO) applicando solo i criteri pre-registrati |
| `backtest/10_backtest_A.md` | colonna A: imbuto, cella primaria, per anno, sensibilità, closed period, tutte le celle |
| `backtest/11_backtest_B.md` | colonna B (cluster Layer 1): stesse tabelle |
| `backtest/12_matched_control.md` | colonna C, scomposizione per anno, placebo |
| `backtest/13_survivorship.md` | copertura per anno, scenari per gli eventi non risolti, break-even |
| `backtest/00_…05_*.md` | checkpoint intermedi: profilo dello snapshot, tabella canonica, dry-run eventi, risoluzione ticker, gate e bande |
| `dossier/` | caso zero: candidati e dossier |
| `DECISIONS.md` | 42 ADR: ogni scelta non ovvia, con alternative, conseguenze e test |

## Fonte dati e header reale

Bulk: `civictechsweden/oppna-insynsregistret`, `data/insynsregistret.csv` (dati CC0), **pinnato al commit
`27d8523376`** (sha256 `462fbf2c…`, 42,6 MB, 166.210 righe, pubblicazioni 2016-07-04 → 2026-09-13).
UTF-8, `;`, virgola decimale, `YYYY-MM-DD HH:MM:SS`. Nessun ID notifica. 9 record rotti in quarantena.

| # | header FI | canonico | note |
|---|---|---|---|
| 0 | Publiceringsdatum | `published_at` | della versione, non della notifica |
| 1 | Emittent | `issuer_name_raw` → `issuer_key` | chiave = LEI; backfill via ISIN/nome; altrimenti nome |
| 2 | LEI-kod | `issuer_lei` | vuoto nel 63% del 2016, 0% dal 2019 |
| 3 | Anmälningsskyldig | `notifier_name` → `associate_kind` | self / vehicle / family |
| 4 | Person i ledande ställning | `pdmr_name` → `name_key` / `person_key` | persona fisica; 3,4% degli acquisti ha nome societario |
| 5 | Befattning | `role_raw` → `roles` | testo libero fino a ~2020, lista fissa di 9 valori dal 2023 |
| 6 | Närstående | `is_closely_associated` | 44.199 Ja |
| 7 | Korrigering | `is_amendment` | ⟺ `Är förstagångsrapportering` vuoto (0 violazioni) |
| 8 | Beskrivning av korrigering | `amendment_note` | |
| 9 | Är förstagångsrapportering | `is_initial` | |
| 10 | Är kopplad till aktieprogram | `is_share_program` | 20.642 Ja |
| 11 | Karaktär | `nature_raw` → `txn_kind` | 41 valori; solo `Förvärv` può essere segnale |
| 12 | Instrumenttyp | `instrument_type_raw` → `instrument_type` + `type_source` | vuoto per tutto il 2016-17: inferito via ISIN / nome |
| 13 | Instrumentnamn | `instrument_name` → `share_class` | `ser. B`, `serie B`, `… B`, pref, SDB |
| 14 | ISIN | `isin` (+ check digit) | vuoto 14.036 |
| 15 | Transaktionsdatum | `trade_date` | |
| 16 | Volym | `volume` | |
| 17 | Volymsenhet | `volume_unit` | Antal / Belopp |
| 18 | Pris | `price` | valuta nativa conservata |
| 19 | Valuta | `currency` | SEK 95%, poi CAD, EUR, USD |
| 20 | Handelsplats | `venue_raw` → `venue_class` | nome, non MIC; `Utanför handelsplats` 37% |
| 21 | Status | `status_raw` → `chain_status` | Aktuell / Reviderad / Makulerad; catene inferite (nessun ID) |

Dettagli e distribuzioni: `backtest/00_ingest_profile.md`, `backtest/01_canonical.md`.

## Idee riprese dallo scanner USA (reimplementate, mai importate)

| idea USA (file di riferimento nel repo `form4-scanner`) | qui |
|---|---|
| `open_market_buys`: P, non derivato, non piano, ≥ $25k (`form4_scanner/parse.py`) | Förvärv + azione + non programma + prezzo > 0 + Antal + ≥ $25k per riga al cambio della data |
| dedup `(accession, txn_index)` (`cluster.py`) | `record_id` = sha256 dei 22 campi + occorrenza; catene di revisione inferite |
| buyer groups via union-find, token entità (`cluster.py`, `flags.py`) | la persona fisica è già nel registro; veicoli attribuiti; nomi societari esclusi |
| finestra 30 giorni, buyer distinti (`cluster.py`) | ≥ 3 persone fisiche, trigger alla pubblicazione, staleness, cooldown episodi |
| prezzo di esecuzione uniforme = allocazione (`cluster.py`) | regole strutturali S1-S3 (sottoscrizione, strumenti di emissione, stesso prezzo + evidenza) |
| dilution veto point-in-time (`dilution.py`, `tools/backfill_dilution.py`) | Teckning/BTA/BTU visibili nel registro + crescita azioni con lag di pubblicazione |
| classificatore CMP routine (`classify.py`, con il bug "solo primo owner") | etichetta per ogni persona; il gate usa mesi con acquisti + dispersione degli importi |
| backtest event-time: ingresso dopo la pubblicazione, ±500%, variante (b), t iid (`tools/backtest_event_time.py`) | stesso schema + t con cluster per emittente e mese, calendar-time, bootstrap, MDE |
| matched control stessa banda, stessa data, quiet 60 gg (`tools/matched_control.py`) | colonna C su popolazione identica |
| UNKNOWN scritto, sezione NON VERIFICATO (`reports/dossier_spec.md`) | dossier con MISSINGNESS obbligatoria e test di vocabolario |
| lezioni: prezzo aggiustato × azioni as-filed è sbagliato; −100% non è conservativo; la copertura prezzi cambia per anno (`docs/HANDOFF.md`, `reports/survivorship_bound.md`) | mcap con prezzo del registro e azioni as-reported; scenari e break-even; copertura per anno |

## Come si esegue

```
uv sync
uv run pytest                      # 178 test offline
uv run fi-scan ingest              # snapshot bulk pinnato -> data/raw/bulk
uv run fi-scan profile             # 00_ingest_profile.md
uv run fi-scan canon               # tabella canonica in data/fi.sqlite, 01_canonical.md
uv run fi-scan events-dryrun       # 02_events_dryrun.md (solo registro + FX)
uv run fi-scan resolve             # ISIN -> ticker .ST verificato sui prezzi del registro (lungo)
uv run fi-scan enrich              # azioni e date report da Yahoo (lungo)
uv run fi-scan gates-mcap          # 05_gates_mcap.md (nessun rendimento)
uv run fi-scan freeze              # preregistration.md: committare PRIMA del backtest
uv run fi-scan backtest            # 10, 11, 12, 13, 20
uv run fi-scan refresh             # export FI incrementale (un thread, pausa 5 s, <= 20 richieste) -> data/fi_refreshed.sqlite
uv run fi-scan caso-zero           # dossier/<data>_<emittente>.md
```

Nessuna chiamata a modelli linguistici in nessun passo: token e costo per run = 0.

## Cosa non è stato possibile fare

Elenco aggiornato in fondo a `backtest/20_verdict.md` e nella sezione "Limiti" di `DECISIONS.md` (ADR-032, ADR-034, ADR-042).
