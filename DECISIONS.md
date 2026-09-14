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

## ADR-016 — Definizioni di riga A_exact, A_onvenue, B_row

**Contesto.** Il codice P del Form 4 USA è "open market or private purchase": include acquisti privati.

**Decisione.** Base = `Förvärv` + azione (dichiarata o inferita) + non collegato a programma + prezzo > 0 +
volume in Antal + versione corrente.
- **A_exact** (primaria per la colonna A, parità con P): base + valore ≥ $25.000 per riga al cambio della data di
  transazione, qualunque venue.
- **A_onvenue**: A_exact senza righe fuori mercato (sensibilità).
- **B_row**: base on-venue, senza soglia di valore (conta per i cluster).
Le vendite di copertura fiscale dopo vesting sono marcate `SELL_TO_COVER_CANDIDATE` (vendita entro 30 giorni da
Tilldelning, Lösen ökning o riga di programma della stessa persona) e restano fuori dal segnale come ogni vendita.

**Test:** `tests/test_openmarket.py`.

## ADR-017 — Sottoscrizione strutturale S1-S3

**Contesto.** In Svezia i consiglieri sottoscrivono emissioni dirette e diritti; a volte le registrano come `Förvärv`
allo stesso prezzo e nella stessa data.

**Decisione.** S1 = righe Teckning dell'emittente nella finestra; S2 = righe su BTA/BTU/diritti/interim (flag di contesto).
**S3** = ≥ 3 persone distinte con acquisto base alla stessa data, stesso prezzo e valuta, **e** almeno una riga fuori
mercato **oppure** una sottoscrizione/strumento di emissione visibile allo stesso prezzo entro 20 giorni. S3 azzera lo
score e le sue righe non contano per il cluster. Stesso prezzo on-venue senza evidenza di emissione = solo flag
`UNIFORM_PRICE_ONVENUE` (può essere un ordine limite comune). Flag aggiuntivo se sono tutti consiglieri. Tutto
point-in-time: un'emissione pubblicata dopo T non riscrive un trigger già emesso.

**Test:** `tests/test_structural.py`.

## ADR-018 — Cluster B

**Decisione.** ≥ 3 persone fisiche distinte (merge point-in-time, veicoli attribuiti) con righe B_row e date di
transazione in una finestra di 30 giorni inclusi. T = prima pubblicazione in cui la condizione è vera sulle righe
visibili; righe S3 escluse; finestra con l'ancora più vecchia. Staleness = T − data della riga che completa il cluster;
> 30 giorni → `is_stale`, fuori dalla primaria B. Nuovo episodio solo con ancora oltre fine episodio + 30 giorni. Gate
valutati una volta a T (le persone che arrivano dopo compaiono nel dossier, non nello score). Righe considerate:
transazioni negli ultimi 365 giorni rispetto a T.

**Conseguenze.** Al trigger i cluster hanno quasi sempre esattamente 3 persone (report 02). **Test:** `tests/test_clusters.py`.

## ADR-019 — Dilution veto svedese

**Contesto.** Il veto USA usa i filing di offerta SEC e la crescita delle azioni XBRL. In Svezia l'equivalente osservabile
gratis è l'attività di sottoscrizione nel registro stesso e la serie azioni di Yahoo.

**Decisione.** BLOCKED se, con sole informazioni visibili a T: (partecipazione) Teckning o strumenti di emissione
dell'emittente con data in [ultimo acquisto − 5 gg, ultimo acquisto]; (trappola) idem in (ultimo acquisto, +75 gg] già
pubblicati; (crescita) azioni ≥ +25% su circa un anno. CAUTION ≥ +10%. UNKNOWN senza dati azioni. Crescita: ultima
osservazione con data ≤ T − 45 giorni (lag di pubblicazione) contro la baseline più vicina a un anno prima con distanza
180-700 giorni, normalizzata per gli split. Il gate passa se non BLOCKED, come nel test USA.

**Asimmetria dichiarata.** Nessun equivalente dei prospetti di offerta; le emissioni dirette senza PDMR sottoscrittori
sono visibili solo tramite la crescita azioni. **Test:** `tests/test_gates.py`.

## ADR-020 — Grande azionista

**Contesto.** MAR art. 19 non obbliga i detentori > 10% a notificare (FI, 2016): il registro non può dire che qualcuno
*non* è grande azionista.

**Decisione.** `large_holder` ∈ {true, unknown}, mai false. True se c'è una parola chiave di proprietà nel ruolo (Ägare,
Huvudägare, Större ägare, Owner, Grundare, 10+%…) o se la posizione minima visibile (ADR-012) è ≥ 10% delle azioni as-of
con lag. Gate `no_large_holder` = nessun true tra le persone del cluster. Solo colonna B.

**Test:** `tests/test_gates.py::test_large_holder_true_or_unknown_never_false`.

## ADR-021 — Routine

**Contesto.** Il prompt chiede "numero acquisti 12 mesi ÷ taglia mediana": come rapporto non ha unità coerenti. L'idea
("chi compra ogni mese la stessa cifra è un piano") richiede frequenza *e* regolarità dell'importo.

**Decisione.** Per persona ed emittente nei 365 giorni prima di T: routine = mesi con acquisti ≥ 6 **e** dispersione =
mediana(|x − mediana|)/mediana dei valori mensili in SEK ≤ 0,25. Gate `not_routine` = restano ≥ 3 persone non routine.
Etichetta CMP (stesso mese di calendario nei 3 blocchi da 365 giorni) calcolata **per ogni persona** (la versione USA la
calcolava solo per il primo owner), solo informativa. Soglie fissate prima di vedere rendimenti.

**Test:** `tests/test_gates.py` (routine, CMP per persona, righe future escluse).

## ADR-022 — Closed period MAR come attributo

**Decisione.** `days_since_report` = giorni tra T e l'ultima data report Yahoo ≤ T; UNKNOWN se assente (frequente per le
small cap). Finestra post-report primaria W = 10 giorni (come il flag USA), W = 30 descrittiva. Non entra nello score. Nel
backtest si confrontano eventi dentro, fuori e UNKNOWN; il confronto dentro/fuori usa solo il sottoinsieme con data nota.

**Limite.** La lista di date Yahoo è scaricata oggi: contiene date passate, non previsioni visibili a T.
**Test:** `tests/test_gates.py::test_closed_period`.

## ADR-023 — Composizione del Layer 1

**Decisione.** Score = cluster + not_routine + dilution ≠ BLOCKED + no_large_holder (0-4); S3 forza 0. Nessun verdetto nei
gate. La colonna A usa solo il dilution veto (parità USA). Colonna B primaria = score 4/4 e non stale; i risultati per
livello di score sono descrittivi. Negli USA solo i gate negativi hanno evidenza fuori campione: gli altri componenti
restano misurati, non ottimizzati.

## ADR-024 — Risoluzione ISIN → ticker e verifica

**Decisione.** Candidati in ordine: lista Nasdaq Nordic (attivi Main Market e First North, simbolo →
`SIMBOLO-CON-TRATTINO.ST`), `yf.Search(ISIN)`, ricerca per nome. Solo ticker `.ST`. Verifica obbligatoria: i prezzi
on-venue in SEK del registro per quell'ISIN devono cadere nel [Low, High] Yahoo ricostruito raw ±2% per ≥ 80% di almeno 3
righe → `verified=True`; rapporto mediano ~100× → `SCALE_SUSPECT`; meno di 3 righe → `verified=None` (usabile,
segnalato). Primaria: ticker dell'ISIN dell'evento con verified ≠ False; mai il ticker di un'altra classe. Sensibilità:
solo verified=True.

**Storia.** La prima esecuzione completa ha provato fino a 8 candidati per ricerca per nome; il limite a 3, introdotto per
velocità, vale per le esecuzioni successive e non ha cambiato gli esiti già in cache.

**Conseguenze.** Gli emittenti spariti non hanno serie: vedi ADR-032. **Test:** `tests/test_market.py::test_verify_against_register`.

## ADR-025 — Prezzi

**Decisione.** yfinance 1.6.0 pinnato, `auto_adjust=False`, `repair=False` (nessuna correzione silenziosa), cache su
disco immutabile per ticker (una risposta vuota è registrata come vuota), pausa 0,5 s tra chiamate. `Close` è
split-adjusted e senza dividendi; il prezzo raw si ricostruisce moltiplicando per gli split successivi.

## ADR-026 — Market cap

**Decisione.** mcap_SEK(d) = azioni × close raw. Azioni = ultima osservazione `get_shares_full` con data ≤ d − 45 giorni,
portata a d con gli split intermedi (la serie è as-reported: GCOR 348M → 34,8M allo split 1:10). La serie è il totale
societario (HOLM-A = HOLM-B): per i dual class si usa il prezzo della classe acquistata (dichiarato; sensibilità senza dual
class). USD con `SEK=X` (SEK per USD, controllo di orientamento) alla data. Banda [50M, 300M) USD chiusa a sinistra.
Nessun forward-fill: se manca un pezzo, mcap null con motivo, evento escluso e contato. Data della mcap: ultima data di
transazione dell'evento (A), ancora del cluster (B).

**Test:** `tests/test_returns.py::test_mcap_point_in_time_and_band`.

## ADR-027 — Benchmark `^OMXSPI` e forchetta Close/Adj Close

**Contesto.** Su yfinance l'unico indice svedese con storico è `^OMXSPI` (price index, senza dividendi); gli indici small
cap e gross restituiscono una riga sola.

**Decisione.** Primaria: rendimento di prezzo del titolo (Close) contro rendimento di prezzo dell'indice, entrambi in SEK
(coerenti). Limite superiore riportato: Adj Close (con dividendi) contro lo stesso indice, che gonfia l'eccesso di circa
metà del dividend yield annuo. L'effetto dimensione non è gestito dal benchmark: lo misura la colonna C (ADR-031). Gli USA
confrontavano con IWM in EUR; qui entrambe le gambe sono in SEK, quindi il cambio non entra nell'eccesso.

## ADR-028 — Rendimenti

**Decisione.** Calendario = sessioni `^OMXSPI`. Ingresso = primo bar del titolo con data ≥ prima sessione successiva al
giorno di pubblicazione (mai un prezzo precedente), entro 5 sessioni. Uscita = ultimo bar ≤ ingresso + h sessioni, entro
5 sessioni. Stati: OK, TOO_RECENT, NO_HISTORY, NO_ENTRY_BAR, ENDED_IN_WINDOW, ARTEFACT (|r| > 500%, escluso e contato).
Netto = lordo − 100bp. Sensibilità "parità di bar" (uscita a i0 + h nella serie del titolo, come negli USA). Diagnostici
`expost_`: massimo movimento giornaliero > 40%, emissione di diritti tra ingresso e uscita.

**Test:** `tests/test_returns.py`.

## ADR-029 — Eventi sovrapposti

**Decisione.** Variante (a) tutti gli eventi; variante (b) un evento per emittente, il successivo solo oltre 126 giorni di
calendario dall'ultimo tenuto, applicata dopo gate e banda come nel codice USA (`cooldown_filter`). Poiché 126 sessioni
sono ~180 giorni di calendario, una sovrapposizione residua resta: la gestiscono i t con cluster e il portafoglio
calendar-time.

## ADR-030 — Statistica

**Decisione.** Per ogni cella: n, media, mediana, sd, % positivi, t iid, t CR1 per emittente, t CR1 per mese di evento,
t two-way (emittente + mese), portafoglio calendar-time mensile equal-weight, CI bootstrap percentile 95% (1.000 draw,
seed 12345), MDE (α 5% bilaterale, potenza 80%). t con cluster = None sotto 10 cluster. Nel testo dei report: "t < 2",
"n < 30", "sotto MDE" quando valgono. Formule in `backtest/stats.py` e ripetute nei report.

**Test:** `tests/test_stats.py`.

## ADR-031 — Matched control

**Decisione.** Per ogni evento con rendimento OK: peer = emittente del registro con ticker non rifiutato, diverso
dall'emittente dell'evento (tutte le classi), nella stessa banda alla stessa data della mcap dell'evento, senza righe B_row
visibili a T con transazione in [D − 60, D], log-cap più vicino; a parità issuer_key minore. Eccesso = r_evento − r_peer
sulle stesse date. Gamba del peer non OK → coppia scartata e contata. La popolazione di C è la stessa della cella
confrontata. Pool ristretto agli emittenti presenti nel registro (quelli vigilati da altre autorità non compaiono: il
"quiet" non sarebbe verificabile).

**Test:** `tests/test_returns.py::test_peer_selection`, `test_quiet_index_is_point_in_time`.

## ADR-032 — Survivorship

**Contesto.** yfinance non ha serie per la maggior parte degli emittenti spariti (report 03); negli USA il 53% degli
spariti era stato acquisito, quindi −100% non è un limite conservativo.

**Decisione.** Copertura riportata per anno e segmento. Gli eventi senza ticker o senza mcap non hanno banda: scenari
S_minus100 (−1 − r̄_bench), S_minus50, S0, S_plus (+15%), S_draw (estrazione dalla distribuzione osservata) e S_mix
(acquisizione probabile → +15%, altrimenti −100%), applicati (i) alla quota attesa in banda, stimata sugli eventi con
banda nota dello stesso anno, e (ii) a tutti. Break-even p* = n_obs · m / (n_u · (1 + r̄_bench)). Acquisizione probabile =
≥ 2 persone che vendono fuori mercato allo stesso prezzo nei 120 giorni prima dell'ultima riga dell'emittente (indizio,
non prova). ENDED_IN_WINDOW → variante "ultimo prezzo tenuto piatto".

**Test:** `tests/test_survivorship.py`.

## ADR-033 — Colonne `expost_`

**Decisione.** Tutto ciò che usa informazione successiva all'evento ha prefisso `expost_` e serve solo a stratificare i
risultati. Un test AST verifica che nessun modulo di gate, eventi o control le nomini.

## ADR-034 — Contratto point-in-time

**Decisione.** Vedi ADR-015. In più: dati di mercato letti con data ≤ data della decisione; azioni con lag di 45 giorni;
date report ≤ T. Limiti dichiarati: la tipizzazione via ISIN (ADR-013) e le liste di risoluzione odierne (ADR-024) usano
informazione successiva, ma solo per identificare strumenti e ticker, non per scegliere eventi in base al loro esito.

## ADR-035 — Pre-registrazione

**Decisione.** Prima di calcolare qualunque rendimento successivo agli eventi si scrive `backtest/preregistration.md` con
sha256 di `config/pipeline.toml`, snapshot pinnato, cella primaria, criteri di verdetto e definizione di copertura, e lo
si committa. Il verdetto (`backtest/20_verdict.md`) applica solo quei criteri. Ogni modifica successiva = nuovo ADR,
riportato accanto ai risultati.

## ADR-036 — Storage

**Decisione.** SQLite stdlib (`data/fi.sqlite`, gitignored) per tabelle canoniche, eventi e risoluzione; snapshot grezzi
gzip con manifest; cache Yahoo come CSV per ticker. In git: codice, test, config, report markdown, pre-registrazione,
dossier. I CSV per evento sono gitignored (rigenerabili).

## ADR-037 — Dipendenze

**Decisione.** pandas, numpy, pydantic v2, yfinance (pinnato 1.6.0); pytest in dev. HTTP con `urllib`, SQLite e TOML dalla
stdlib. Nessun uso di API LLM (ADR-041).

## ADR-038 — Dossier

**Decisione.** Solo fatti con fonte (registro, report dell'emittente, comunicati) o UNKNOWN scritto; sezione
**NON VERIFICATO / MISSINGNESS** obbligatoria; punteggio WHO/WHERE/WHEN provvisorio con asterisco; nessun verdetto, nessun
linguaggio da raccomandazione (test di vocabolario). La regola di selezione del caso zero è fissata prima di guardare prezzi
successivi all'evento.

## ADR-039 — Isolamento

**Decisione.** Nessun import, path o package condiviso con form4-scanner o invest-system (test AST). Le idee riprese sono
reimplementate e citate con il file di riferimento nel README.

## ADR-040 — Rottura della soglia di notifica FI

**Contesto.** Dal 2024-12-04 la soglia annua di notifica è EUR 20.000 (prima EUR 5.000).

**Decisione.** Nessuna correzione: gli acquisti piccoli spariscono dal registro dopo quella data. Pesa poco sulla colonna A
(soglia $25.000 per riga), di più sui cluster B (righe senza soglia). I risultati per anno la rendono visibile.

## ADR-041 — Costi API

**Decisione.** Nessuna chiamata a modelli linguistici in nessun passo: token e costo per run = 0, registrato nei report.
Se in futuro un passo di parsing usasse un'API, il run deve registrare token e costo.


## ADR-042 — Storia Yahoo riscalata per emissioni di diritti e spin-off

**Contesto.** Verificando i ticker contro i prezzi del registro (ADR-024) è emerso che per molti titoli di Stoccolma il
`Close` Yahoo della storia precedente a un'emissione di diritti o a uno spin-off è diviso per un fattore costante che non
compare in `Stock Splits`: Securitas 1,20x prima dell'ottobre 2022, Dustin 2,0x prima del 2023, Scandic 1,4x prima del
2021, Sandvik 1,05x prima dello spin-off Alleima, Saab 1,08x prima del 2019, Peab 1,07x prima del 2021. Non è
uniforme: Midsummer (MIDS.ST) mostra il salto di prezzo non aggiustato. Con la verifica originale 259 ISIN, molti large cap,
risultavano `PRICE_MISMATCH` pur avendo il ticker giusto.

**Decisione** (presa al checkpoint 4, prima del congelamento).
1. La verifica del ticker guarda le **ultime 20 righe** del registro (la coda della storia non è riscalata) oppure tutte;
   il riscalamento dei tratti precedenti viene registrato in `adjusted_history` e nei `scale_segments`
   (fattore = mediana di prezzo registro / Close Yahoo, per anno, tratti fusi se entro 3%).
2. Il prezzo raw Yahoo a una data = Close × split successivi × fattore del tratto che contiene la data (o del tratto più vicino).
3. Per la market cap degli **eventi** si usa il **prezzo di esecuzione in SEK delle righe del registro** (mediana on-venue,
   altrimenti off-venue): è reale, alla data, e non dipende da Yahoo. Il prezzo Yahoo riscalato resta come confronto
   (`close_raw_yahoo`) e serve per il pool del matched control, dove non ci sono righe del registro alla data.
4. I rendimenti usano il `Close` Yahoo così com'è: dove la storia è riscalata, il rendimento attraverso l'emissione
   incorpora il valore teorico dei diritti (vicino a ciò che ottiene chi li vende); dove non lo è, il salto resta e viene
   stratificato con `expost_rights_issue`.

**Esito.** Ticker verificati da 742 a 809; 294 ISIN con storia riscalata rilevata; `NOT_VERIFIED` da 259 a 193.

**Test:** `tests/test_market.py::test_yahoo_rescaled_history_is_detected_and_verification_uses_recent_rows`,
`test_recent_mismatch_is_still_rejected`, `tests/test_returns.py::test_mcap_point_in_time_and_band`.
