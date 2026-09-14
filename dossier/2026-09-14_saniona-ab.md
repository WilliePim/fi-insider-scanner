# Caso zero — Saniona AB

Dossier generato dal registro FI (snapshot pinnato + refresh FI (['2026-05-17', '2026-09-14'])). Formato rubric WHO / WHERE / WHEN. **Nessun verdetto, nessun ordine.**

## Selezione

Regola dichiarata prima di guardare i prezzi successivi: trigger B con T in [2026-06-16, 2026-09-14], score 4/4, non stale, banda 50-300M USD as-of l'ancora, ticker verificato sui prezzi del registro; spareggi: più persone fisiche, poi T più recente; se nessuno è in banda, il migliore fuori banda con nota.

Esito: in banda.

## Testata

| campo | valore |
|---|---|
| Emittente | Saniona AB |
| LEI / issuer_key | 549300XO4L9XNOCFCZ84 |
| ISIN | SE0005794617 |
| Ticker (verificato sui prezzi del registro) | SANION.ST |
| T (prima pubblicazione che completa il cluster) | 2026-09-01 16:54:07 |
| Ancora (prima transazione) | 2026-08-27 |
| Ultima transazione della finestra | 2026-09-01 |
| Market cap as-of ancora | 1,592,867,746 SEK = 167 M USD (azioni 138,030,134 al 2025-11-17 da Yahoo, prezzo 11.54 da register_onvenue, USDSEK 9.523) |
| Banda | 50_300 |
| Persone fisiche distinte | 3 |
| Valore SEK del cluster | 210,395 |
| Staleness (giorni) | 4 |

## Layer 1 a T

| gate | esito | evidenza |
|---|---|---|
| cluster ≥ 3 persone / 30 gg | sì | record 225069c243c84fb679f9:0\|a70ba57e0392376c565f:0\|86195ecd8f270b41e89f:0 |
| non routine (≥ 3 persone non routine) | sì | n_routine = 0 |
| dilution veto ≠ BLOCKED | sì | verdetto CAUTION, partecipazione False, trappola False, crescita azioni +23.4% |
| nessun grande azionista `true` | sì | n_large_holder = 0 |
| S3 (sottoscrizione strutturale) nella finestra | no | prezzo uniforme on-venue: False; S1 False, S2 False |

Score Layer 1 = **4/4**. Acquisti simbolici (limite superiore < 1%): 0.


## WHO

### Anna Helena Constance Ljung

- Ruolo (Befattning): Styrelseledamot → canonico board
- Chi notifica: Anna Helena Constance Ljung (self)

Acquisti del cluster (registro FI):

| transazione | pubblicazione | quantità | prezzo | valuta | SEK | venue | record |
|---|---|---|---|---|---|---|---|
| 2026-08-27 | 2026-08-28 07:59:19 | 4,188.00 | 11.94 | SEK | 50,004.72 | NASDAQ STOCKHOLM AB | 225069c243c84fb679f9:0 |

- Variazione di posizione: ≤ 90.5% (limite superiore: posizione minima visibile nel registro 4,629 azioni). Possesso da fonte primaria: vedi WHERE; se assente → UNKNOWN.
- Storia 5 anni nel registro (questo emittente): 2 righe in aumento (acq_purchase, subscription), 1 in diminuzione (exercise_out); prima riga 2024-01-23.
- Dopo il cluster (fino allo snapshot): nessuna riga.
- Routine a T: mesi con acquisti (12m) 1, dispersione 0.00 → non routine; etichetta CMP: sparse.
- Grande azionista: unknown (mai `false`: MAR non copre i >10%).

### Johnny Stilou / johnny stilou

- Ruolo (Befattning): Ekonomichef/finanschef/finansdirektör → canonico cfo
- Chi notifica: johnny stilou (self)

Acquisti del cluster (registro FI):

| transazione | pubblicazione | quantità | prezzo | valuta | SEK | venue | record |
|---|---|---|---|---|---|---|---|
| 2026-08-28 | 2026-09-01 16:54:07 | 5,000.00 | 11.54 | SEK | 57,700.00 | NYKREDIT BANK - SYSTEMATIC INTERNALISER | a70ba57e0392376c565f:0 |

- Variazione di posizione: UNKNOWN (nessuna posizione visibile nel registro prima del cluster: il registro parte dal 2016-07 e non contiene il possesso). Possesso da fonte primaria: vedi WHERE; se assente → UNKNOWN.
- Storia 5 anni nel registro (questo emittente): 2 righe in aumento (acq_purchase, grant), 0 in diminuzione (—); prima riga 2025-07-01.
- Dopo il cluster (fino allo snapshot): nessuna riga.
- Routine a T: mesi con acquisti (12m) 1, dispersione 0.00 → non routine; etichetta CMP: sparse.
- Grande azionista: unknown (mai `false`: MAR non copre i >10%).

### Jorgen Drejer

- Ruolo (Befattning): Vice VD → canonico deputy_ceo
- Chi notifica: Jorgen Drejer (self)

Acquisti del cluster (registro FI):

| transazione | pubblicazione | quantità | prezzo | valuta | SEK | venue | record |
|---|---|---|---|---|---|---|---|
| 2026-09-01 | 2026-09-01 09:26:24 | 9,000.00 | 11.41 | SEK | 102,690.00 | NASDAQ STOCKHOLM AB | 86195ecd8f270b41e89f:0 |

- Variazione di posizione: UNKNOWN (nessuna posizione visibile nel registro prima del cluster: il registro parte dal 2016-07 e non contiene il possesso). Possesso da fonte primaria: vedi WHERE; se assente → UNKNOWN.
- Storia 5 anni nel registro (questo emittente): 6 righe in aumento (acq_purchase, subscription), 2 in diminuzione (disp_sale, exercise_out); prima riga 2021-11-19.
- Dopo il cluster (fino allo snapshot): nessuna riga.
- Routine a T: mesi con acquisti (12m) 0, dispersione — → non routine; etichetta CMP: sparse.
- Grande azionista: unknown (mai `false`: MAR non copre i >10%).


## WHERE

Nessuna fonte primaria letta: tutto ciò che segue è MISSINGNESS.


### NON VERIFICATO / MISSINGNESS

- [NON LETTO] ultimo report infra-annuale (ricavi, EBIT, cassa, debito netto) letto dalla fonte primaria
- [NON LETTO] tabella dei maggiori azionisti / possesso degli insider (annual report o pagina IR) con data
- [NON LETTO] comunicati stampa dell'emittente nella finestra del cluster e nei 30 giorni precedenti
- [NON LETTO] calendario finanziario (prossimo report, AGM) dalla pagina IR
- [NON LETTO] eventuali prospetti, emissioni dirette, programmi di incentivazione in corso
- [NON LETTO] verbali/avviso di convocazione dell'ultima AGM (mandati, autorizzazioni a emettere)
- [NON LETTO] retribuzione in contanti dei dirigenti (per rapportare la taglia dell'acquisto)
- [NON LETTO] lock-up o accordi tra azionisti

## WHEN

- Date report note a Yahoo: ultima prima di T 2022-05-25 (1560 giorni prima di T); prossime —.
- Closed period MAR: 30 giorni prima di ogni report; gli acquisti PDMR si concentrano strutturalmente nei giorni successivi (attributo, non segnale).
- Nessun evento databile letto da fonte primaria (AGM, scadenze, emissioni): MISSINGNESS.

## Punteggio provvisorio

| dimensione | punteggio |
|---|---|
| WHO | n/d* |
| WHERE | n/d* |
| WHEN | n/d* |
| Totale | n/d* |

\* provvisorio: riflette ciò che è stato letto alla data del dossier, non un giudizio sul titolo. Nessun verdetto.


### Ancore del punteggio (provvisorie, ADR-038)

- **WHO** 0: acquisti simbolici, routine o solo veicoli senza persona identificata · 1: tre persone, importi piccoli e nessuna variazione di posizione misurabile · 2: tre o più persone con importi materiali (≥ 250 kSEK a testa dal registro) oppure variazione di posizione verificata ≥ 10% · 3: CEO/CFO e presidente insieme, importi materiali e variazione di posizione verificata su fonte primaria.
- **WHERE** 0: nessuna fonte primaria letta · 1: un report letto, nessun fatto che spieghi il momento · 2: report e comunicati letti, contesto coerente con gli acquisti · 3: fatto verificabile e databile che precede gli acquisti (risultati, contratto, ristrutturazione) letto sulla fonte.
- **WHEN** 0: nessun evento databile · 1: solo il report appena pubblicato (closed period appena aperto: strutturale in Europa) · 2: un evento databile futuro entro 6 mesi (AGM, scadenza, report) · 3: più eventi databili con date confermate dal calendario dell'emittente.

Ogni punteggio porta un asterisco: dipende da ciò che è stato letto, non da ciò che esiste.


Costo API di modelli linguistici per questo dossier: 0 token, 0 USD.

