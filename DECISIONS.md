# DECISIONS

Registro delle decisioni non ovvie, stile ADR. Ogni voce: contesto, decisione, alternative
scartate, conseguenze, test che la fa rispettare. Le voci non si riscrivono: una modifica
dopo il congelamento della configurazione (`backtest/preregistration.md`) è una nuova voce.
I numeri citati vengono dai report `backtest/00_…` e `backtest/01_…` sullo snapshot pinnato.

---

## ADR-001 — Fonte bulk pinnata; incrementale proprio solo per il caso zero

**Contesto.** Il repo `civictechsweden/oppna-insynsregistret` pubblica il registro FI completo (dati
CC0, codice AGPL) in un unico CSV aggiornato ogni giorno da GitHub Actions. Il suo `run.py` usa
User-Agent da browser, 4 thread e nessuna pausa verso FI; FI si riserva di bloccare chi carica il
servizio. L'export FI tronca in silenzio a 1.000 righe.

**Decisione.** Il backtest usa uno snapshot **pinnato a un commit upstream**
(`27d8523376497b0eac9759edf6ae319e828d8c55`, sha256 `462fbf2c…`, in `config/pipeline.toml`),
scaricato dal raw GitHub a quel commit. Nessun codice upstream viene eseguito o copiato.
L'unico accesso a FI è un client proprio per il caso zero: un thread, pausa ≥ 5 s, ≤ 20 richieste,
UA `fi-insider-scanner/0.1 (research)` con contatto solo da variabile d'ambiente, finestre dimezzate
sotto le 1.000 righe ed errore esplicito se un giorno singolo arriva al tetto.

**Alternative.** Eseguire `run.py` (carico e UA non accettabili); scaricare `main` a ogni run
(non riproducibile).

**Conseguenze.** Il backtest è riproducibile bit per bit; lo snapshot eredita i limiti upstream
(ADR-002). **Test:** `tests/test_rawcsv.py`, sha256 verificato da `cli._pinned_raw`.

## ADR-002 — Semantica dello snapshot e status stantii

**Contesto.** Upstream ha fatto il full fetch il 2026-08-19; poi ri-scarica 3 giorni. FI cambia lo
status delle versioni vecchie (`Aktuell` → `Reviderad`) senza cambiarne `Publiceringsdatum`, quindi
una riga pubblicata prima della finestra di 3 giorni e corretta dopo resta `Aktuell` nel CSV (caso
Vimian 2026-09-01). La dedup upstream su 9 campi ha anche fuso righe identiche reali, non
recuperabili dal bulk (0 duplicati sulla chiave upstream nello snapshot).

**Decisione.** Gli status sono fidati fino a `stale_status_horizon = 2026-08-16`. Dopo, una correzione
può collegarsi a un predecessore ancora `Aktuell` (solo con ISIN e tipo uguali) che diventa
`superseded_inferred` con flag `STATUS_STALE_UPSTREAM`. Lo storico git upstream non è trattato come
archivio point-in-time.

**Conseguenze.** Il backtest (eventi fino a 2025-12) non è toccato; il caso zero sì, e per questo usa
anche il refresh FI. Le righe annullate dopo la loro pubblicazione spariscono retroattivamente dalla
modalità `snapshot` (bias piccolo; la modalità `as_seen` lo misura). **Test:** `tests/test_chains.py`
(`test_stale_upstream_status_after_horizon_vimian`, `test_before_horizon_two_current_rows_are_separate_trades`).

## ADR-003 — Identità del record

**Contesto.** Il registro non ha ID notifica nell'export.

**Decisione.** `record_id` = sha256 (20 hex) dei 22 campi puliti (NBSP e a capo → spazio, trim) +
`:n`, indice di occorrenza tra tuple identiche in ordine di file. Bulk ed export FI producono lo stesso
id per la stessa riga.

**Alternative.** Chiave su sottoinsieme di campi (fonde righe reali, come upstream).

**Test:** `tests/test_rawcsv.py` (id stabile al rimescolamento, `:0`/`:1`, bulk = export FI).

## ADR-004 — Righe rotte: ricomposizione solo per adiacenza, altrimenti quarantena

**Contesto.** 9 record Biovica (2018, 2020) sono spezzati in due righe da 22 campi con valori spostati:
5 metà con Transaktionsdatum..Status vuoti, 4 continuazioni con Publiceringsdatum vuoto e i 7 valori
di coda nei campi 1..7. Le continuazioni stanno in fondo al file, non adiacenti; 5 teste per 4 code.

**Decisione.** Si ricompone solo una troncata seguita immediatamente dalla sua continuazione. Tutto il
resto va in quarantena con numero di riga (tabella `quarantine`, report 00). Esito sullo snapshot:
0 ricomposte, 9 in quarantena.

**Alternative.** Accoppiare per data o prezzo plausibile: sarebbe una congettura.

**Test:** `tests/test_rawcsv.py` (forma reale adiacente/non adiacente, record corti, celle quotate).

## ADR-005 — Checkbox

**Decisione.** `Ja`/`Yes` → True, vuoto → False, qualunque altro valore → None + errore di parse.
Invariante verificato: `Korrigering=Ja` ⟺ `Är förstagångsrapportering` vuoto (0 violazioni).

**Test:** `tests/test_parse.py`, `tests/test_mapping.py`.

## ADR-006 — Tassonomia Karaktär

**Decisione.** I 41 valori osservati mappano a `TxnKind` con direzione (+1/−1/0). **Solo `Förvärv`** è
`acq_purchase` e può essere segnale. Valori sconosciuti → `unmapped`, mai segnale. I trattini tipografici
(`Interntransaktion – Förvärv`) sono normalizzati. Esclusi dal segnale ma conservati con motivo: grant
(Tilldelning), esercizio (Lösen), gift, conversione/scambio, eredità/divisione, corporate action,
prestito/pegno, trasferimento interno, sottoscrizione (Teckning), short, vendita.

**Test:** `tests/test_taxonomy.py`, snapshot: 0 non mappati (report 01).

## ADR-007 — Tassonomia venue

**Contesto.** `Handelsplats` è un nome libero (225 valori), non un MIC.

**Decisione.** Classi: `xsto`, `fnse`, `spotlight` (incl. AktieTorget), `ngm` (incl. Nordic SME/MTF),
`mtf_si` (MTF, dark book, internalizzatori sistematici), `foreign_exchange`, `other_venue`,
`off_venue` (Utanför handelsplats, off-exchange, unlisted), `unknown`. On-venue = tutto tranne
`off_venue` e `unknown`: MTF/SI contano come mercato (esecuzione a prezzo di mercato), con classe
propria per la sensibilità.

**Test:** `tests/test_taxonomy.py`; valori `other_venue` elencati nel report 01.

## ADR-008 — Identità emittente

**Decisione.** `issuer_key` = LEI (formato valido); altrimenti LEI univoco delle righe con lo stesso ISIN;
altrimenti LEI univoco delle righe con lo stesso nome normalizzato; altrimenti `name:<nome normalizzato>`.
Chiave statica (identità, non informazione di mercato). Fonte registrata in `issuer_key_source`.

**Conseguenze.** Gli emittenti vecchi senza LEI e senza righe successive restano identificati per nome
(fusioni di nomi diversi dello stesso emittente possibili solo via ISIN). **Test:** `tests/test_mapping.py`.

## ADR-009 — Identità persona e merge dei nomi

**Contesto.** `Person i ledande ställning` è la persona fisica PDMR, con varianti di scrittura.

**Decisione.** Chiave = NFKC, NBSP, spazi compressi, casefold; "Cognome, Nome" → "nome cognome".
Nomi con token societari (AB, Ltd, Holding, Invest, Stiftelse…) → `pdmr_is_natural_person=False`: non
contano come persone nei cluster. Merge solo **nello stesso emittente**: stesso primo e ultimo token,
un solo nome da 2 token e una sola variante più lunga. Il merge vale da quando entrambe le forme sono
visibili e decade quando appare una seconda variante lunga (ambiguità, point-in-time). Nomi uguali a
meno dei diacritici (Östlund/Ostlund): **solo flag**, nessun merge; il dry-run conta quanti cluster ne
dipendono.

**Alternative.** Fuzzy matching (fusioni transitive non verificabili).

**Test:** `tests/test_names.py`.

## ADR-010 — Persone strettamente legate e veicoli

**Decisione.** Ogni riga è attribuita alla PDMR in `Person i ledande ställning`; `associate_kind` =
`self` / `vehicle` (notificante con nome societario) / `family`. Nei cluster un veicolo conta come la sua
persona, mai come persona aggiuntiva. Il dossier mostra sempre notificante e persona fisica.

**Test:** `tests/test_mapping.py`, `tests/test_clusters.py::test_vehicle_and_person_count_once`.

## ADR-011 — Ruoli

**Decisione.** `Befattning` (testo libero fino a ~2020, lista fissa di 9 valori dal 2023) → insieme di ruoli
{ceo, deputy_ceo, cfo, chair, board, deputy_board, employee_rep, other_admin_body, other_exec,
owner_keyword} con regole regex sull'intero testo. Nessuna etichetta "indipendente": il registro non la
contiene. I ruoli sono descrittivi; entrano nei gate solo `owner_keyword` (grande azionista) e il flag
"tutti consiglieri" dei gruppi a prezzo uniforme.

**Test:** `tests/test_taxonomy.py::test_roles`.

## ADR-012 — Classe azioni e acquisto simbolico

**Decisione.** Classe da `Instrumentnamn` (`ser.`/`serie`/`class`/`klass X`, `X-aktie`, lettera finale
A-D maiuscola), con flag `pref` e `SDB`; l'identità resta l'ISIN. Il registro non contiene il possesso,
quindi la "frazione irrilevante della posizione" non è osservabile: si usa un **limite superiore** della
variazione % = volume / posizione minima visibile (somma netta delle righe azionarie della persona,
veicoli inclusi, dal 2016-07, tutte le classi). Acquisto simbolico = `true` se questo limite è < 1%,
altrimenti `unknown`. Non esclude eventi nella primaria; è una sensibilità.

**Test:** `tests/test_shareclass.py`, `tests/test_gates.py::test_symbolic_purchase_upper_bound`.

## ADR-013 — Inferenza di Instrumenttyp

**Contesto.** `Instrumenttyp` è vuoto per tutto il 2016-17 e per due terzi del 2018.

**Decisione.** Livelli, registrati in `type_source`: `reported` → `isin_rows` (tutte le righe tipizzate dello
stesso ISIN concordano) → `isin_majority` (il tipo dominante copre ≥ 90% delle righe tipizzate dello
stesso ISIN) → `name_rule` (BTA, BTU, TO, TR, konvertibel…) → `issuer_name_match` (nome strumento che
richiama l'emittente o porta una classe, senza parole da derivato, ISIN valido → azione) → `none`.
Sotto il 90% → null + `type_conflict`.

**Storia.** La prima versione (conflitto = null a qualunque discordanza) lasciava null 11.418 righe del
2016-18 per errori di tipizzazione dei dichiaranti su ISIN azionari; cambiata al checkpoint 2, prima del
congelamento.

**Conseguenze.** `isin_rows`/`isin_majority` usano righe pubblicate anche dopo l'evento (identità dello
strumento, non informazione di prezzo); sopravvivenza dell'emittente oltre il 2018 aumenta la probabilità
di essere tipizzati: i risultati si riportano per livello di tipizzazione. **Test:** `tests/test_instruments.py`.

## ADR-014 — Catene di revisione

**Decisione.** Una correzione (`Korrigering=Ja`, `Aktuell` o `Reviderad`) si collega **uno a uno** al
predecessore con stesso emittente, persona e data di transazione e pubblicazione strettamente precedente.
Punteggio: ISIN 3, nome strumento 2, tipo 2, volume 1, prezzo 1, venue 1; minimo 2 (5 per un predecessore
`Aktuell` stantio). A parità di punteggio vince la pubblicazione più recente; parità piena → ambiguo,
nessun link. `chain_status`: current, superseded, superseded_inferred, orphan_revised, cancelled.
`first_published_at` = pubblicazione più vecchia della catena.

**Alternative.** Chiave esatta sui campi (le correzioni cambiano proprio quei campi: ISIN nel 21% dei link).

**Conseguenze.** Le correzioni che cambiano persona o data restano orfane (contate nel report 01).
**Test:** `tests/test_chains.py`.

## ADR-015 — Visibilità e timing

**Decisione.** Gate, eventi e control leggono il registro solo con `Register.visible(as_of)`:
- `snapshot` (primaria): righe `current` pubblicate entro `as_of`;
- `as_seen` (robustezza): ogni versione dalla sua pubblicazione fino a quella della versione successiva;
  le `Makulerad` restano visibili, perché la data di annullamento non esiste nei dati;
- timing `pub` (primaria, conservativo: la versione corrente) o `first_pub` (prima pubblicazione della catena).
Un test AST vieta ai moduli che decidono (gate, eventi, control) di leggere status, SQLite o colonne `expost_`.

**Test:** `tests/test_chains.py::test_snapshot_and_as_seen_visibility`, `tests/test_guards.py`.
