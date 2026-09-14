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


### Possesso da fonte primaria

| persona | ruolo (sito) | ruolo (registro FI) | azioni (sito) | warrant (sito) | acquisto del cluster | variazione | fonte | covers |
|---|---|---|---|---|---|---|---|---|
| Jørgen Drejer | Deputy Chairman dal 2025; consigliere dal 2014; Chairman 2022-2025; 'not independent in relation to Saniona and its management' | Vice VD | 2.187.083 | non indicati | 9.000 azioni | +0,4% se il dato del sito include l'acquisto (2.178.083 -> 2.187.083): sotto l'1%, acquisto simbolico rispetto alla posizione | https://saniona.com/about/board-of-directors/ (data del dato non indicata sulla pagina; lettura 2026-09-14) | tabella dei maggiori azionisti / possesso degli insider (annual report o pagina IR) con data |
| Anna Ljung | Board member dal 2018, indipendente | Styrelseledamot | 12.033 | non indicati | 4.188 azioni | +53% se il dato del sito include l'acquisto (7.845 -> 12.033); il registro vedeva 4.629 azioni prima del cluster (limite inferiore) | https://saniona.com/about/board-of-directors/ (data non indicata; lettura 2026-09-14) | tabella dei maggiori azionisti / possesso degli insider (annual report o pagina IR) con data |
| Johnny Stilou | Chief Financial Officer | Ekonomichef/finanschef/finansdirektör | nessuna indicata | 200.000 (2025/2029) | 5.000 azioni via Nykredit Bank (internalizzatore sistematico) | prima posizione azionaria visibile (da 0); 57.700 SEK contro 200.000 warrant | https://saniona.com/about/executive-team/ (data non indicata; lettura 2026-09-14) | tabella dei maggiori azionisti / possesso degli insider (annual report o pagina IR) con data |
| Thomas Feldthus (CEO, co-fondatore) — NON nel cluster | CEO dal 2022 | — | 1.635.000 | 1.661.928 (2022/2028), 1.855.000 (2024/2029), 500.000 (2025/2029) | nessuno nella finestra | — | https://saniona.com/about/executive-team/ | tabella dei maggiori azionisti / possesso degli insider (annual report o pagina IR) con data |

## WHERE

Fatti letti su fonti primarie (URL e data di lettura):

| fatto | fonte | data lettura | covers |
|---|---|---|---|
| Interim report Q2 2026 pubblicato il 2026-08-27 08:00 (sei mesi al 30 giugno 2026): ricavi SEK 9,2 M (19,1), risultato operativo SEK -116,8 M (-42,4), risultato netto SEK -104,4 M (-3,3), cassa e equivalenti SEK 486,3 M (308,2), perdita per azione SEK -0,76 (-0,03). Il CEO parla di 'a strong financial position'. Nessuna dichiarazione esplicita di runway. | https://mfn.se/a/saniona/saniona-publishes-its-interim-report-for-the-second-quarter-of-2026 | 2026-09-14 | ultimo report infra-annuale (ricavi, EBIT, cassa, debito netto) letto dalla fonte primaria |
| 2026-08-10: AstronauTx esercita l'opzione sul programma ATX0926 (biologia del sonno / malattie neurologiche): US$ 5 M in azioni Series A di AstronauTx, milestone fino a US$ 172 M (97 sviluppo/regolatorie + 75 commerciali), royalty a scaglioni. Diciassette giorni prima del primo acquisto del cluster. | https://mfn.se/a/saniona/astronautx-exercises-option-from-saniona-to-acquire-worldwide-rights-to-neurological-disease-program-under-research-collaboration | 2026-09-14 | comunicati stampa dell'emittente nella finestra del cluster e nei 30 giorni precedenti |
| Comunicati 2026-06-01..2026-09-14 sul feed MFN: 2026-06-04 R&D day virtuale su SAN2668 (epilessie pediatriche); 2026-08-10 AstronauTx; 2026-08-27 report Q2. Nessun comunicato di emissione o finanziamento nella finestra. SAN2668 e SAN2465 'expected to enter Phase 1 around year-end 2026' (dal report Q2). | https://mfn.se/all/a/saniona | 2026-09-14 | comunicati stampa dell'emittente nella finestra del cluster e nei 30 giorni precedenti |
| Finanziamenti visibili sul feed MFN 2025: conversione di convertibili Fenja Capital II A/S (nominale SEK 6 M, 2025-06-26) e variazione del numero di azioni 2025-07-31. Il feed non riporta i dettagli dell'aumento del ~23% delle azioni in circolazione (serie Yahoo, 2024-11 -> 2025-11) usato dal dilution veto (CAUTION): la fonte di quell'emissione non e' stata letta. | https://mfn.se/all/a/saniona | 2026-09-14 | eventuali prospetti, emissioni dirette, programmi di incentivazione in corso |
| Pagina 'Ownership structure' del sito IR: tabella dei maggiori azionisti resa via JavaScript (Monitor by Modular Finance), non leggibile con il fetch: tabella NON letta. | https://saniona.com/investors/the-share/ownership-structure/ | 2026-09-14 | non letto |

### NON VERIFICATO / MISSINGNESS

- [letto] ultimo report infra-annuale (ricavi, EBIT, cassa, debito netto) letto dalla fonte primaria
- [letto] tabella dei maggiori azionisti / possesso degli insider (annual report o pagina IR) con data
- [letto] comunicati stampa dell'emittente nella finestra del cluster e nei 30 giorni precedenti
- [letto] calendario finanziario (prossimo report, AGM) dalla pagina IR
- [letto] eventuali prospetti, emissioni dirette, programmi di incentivazione in corso
- [letto] verbali/avviso di convocazione dell'ultima AGM (mandati, autorizzazioni a emettere)
- [NON LETTO] retribuzione in contanti dei dirigenti (per rapportare la taglia dell'acquisto)
- [NON LETTO] lock-up o accordi tra azionisti

## WHEN

- Date report note a Yahoo: ultima prima di T 2022-05-25 (1560 giorni prima di T) — lista incompleta (ultima data oltre 200 giorni prima di T): attributo della pipeline UNKNOWN, vale la fonte primaria; prossime —.
- Closed period MAR: 30 giorni prima di ogni report; gli acquisti PDMR si concentrano strutturalmente nei giorni successivi (attributo, non segnale).

Eventi databili da fonti primarie:

| data | evento | fonte | covers |
|---|---|---|---|
| 2026-05-26 | Report Q1 2026 | https://mfn.se/all/a/saniona | calendario finanziario (prossimo report, AGM) dalla pagina IR |
| 2026-05-27 | Assemblea annuale (bulletin pubblicato) | https://mfn.se/all/a/saniona | verbali/avviso di convocazione dell'ultima AGM (mandati, autorizzazioni a emettere) |
| 2026-08-10 | AstronauTx esercita l'opzione (US$ 5 M in azioni + milestone) | https://mfn.se/a/saniona/astronautx-exercises-option-from-saniona-to-acquire-worldwide-rights-to-neurological-disease-program-under-research-collaboration | comunicati stampa dell'emittente nella finestra del cluster e nei 30 giorni precedenti |
| 2026-08-27 08:00 | Report Q2 2026: fine del closed period MAR; primo acquisto del cluster lo stesso giorno | https://mfn.se/a/saniona/saniona-publishes-its-interim-report-for-the-second-quarter-of-2026 | calendario finanziario (prossimo report, AGM) dalla pagina IR |
| 2026-09-15 | Affärsvärlden Börsdagarna, Stoccolma (presentazione) | https://saniona.com/investors/ | calendario finanziario (prossimo report, AGM) dalla pagina IR |
| 2026-11-09/11 | BIO-Europe Fall 2026, Colonia | https://saniona.com/investors/ | calendario finanziario (prossimo report, AGM) dalla pagina IR |
| 2026-11-26 | Report Q3 2026 (dal calendario nel report Q2) | https://mfn.se/a/saniona/saniona-publishes-its-interim-report-for-the-second-quarter-of-2026 | calendario finanziario (prossimo report, AGM) dalla pagina IR |
| fine 2026 (non fissata) | Ingresso in Fase 1 di SAN2668 e SAN2465 'around year-end 2026' | https://mfn.se/a/saniona/saniona-publishes-its-interim-report-for-the-second-quarter-of-2026 | calendario finanziario (prossimo report, AGM) dalla pagina IR |

## Punteggio provvisorio

| dimensione | punteggio |
|---|---|
| WHO | 1/3* |
| WHERE | 2/3* |
| WHEN | 2/3* |
| Totale | 5/9* |

- WHO 1*: tre persone fisiche, importi piccoli (50, 58 e 103 kSEK, tutti sotto i 250 kSEK dell'ancora 2). La variazione verificata sul sito supera il 10% solo per Anna Ljung (+53%); per Drejer e' +0,4% (simbolica rispetto a 2,19 M azioni); Stilou parte da zero azioni con 200.000 warrant in mano. Il CEO co-fondatore (1,6 M azioni, 4 M warrant) non compare nel cluster. Discrepanza di ruolo: il registro FI dice 'Vice VD' per Drejer, il sito 'Deputy Chairman' (consigliere dal 2014, non indipendente dal management).
- WHERE 2*: report Q2 e comunicati letti dal feed MFN (testi diffusi dall'emittente), non il PDF del report ne' la tabella azionisti (resa via JavaScript). Contesto: cassa 486 MSEK contro perdita operativa semestrale di 117 MSEK; deal AstronauTx 17 giorni prima degli acquisti. Non letti: retribuzioni, prospetti dell'emissione 2025, lock-up.
- WHEN 2*: un evento databile e confermato entro sei mesi (report Q3 il 2026-11-26) piu' conferenze; l'ingresso in Fase 1 'around year-end' non ha data fissata. Il primo acquisto cade il giorno del report Q2: finestra post-report, cioe' il momento strutturale in cui gli insider europei possono comprare; non discrimina.
- La data report che la pipeline prende da Yahoo per questo emittente e' del 2022 (lista incompleta): l'attributo days_since_report della pipeline e' inaffidabile qui e viene sostituito dalla data primaria 2026-08-27 (0 giorni prima del primo acquisto).
- Il dato '685.175 azioni' che il fetch ha estratto dal report Q2 non e' coerente con le 138 M azioni della serie Yahoo e non viene usato: numero di azioni dal report NON verificato.

\* provvisorio: riflette ciò che è stato letto alla data del dossier, non un giudizio sul titolo. Nessun verdetto.


### Ancore del punteggio (provvisorie, ADR-038)

- **WHO** 0: acquisti simbolici, routine o solo veicoli senza persona identificata · 1: tre persone, importi piccoli e nessuna variazione di posizione misurabile · 2: tre o più persone con importi materiali (≥ 250 kSEK a testa dal registro) oppure variazione di posizione verificata ≥ 10% · 3: CEO/CFO e presidente insieme, importi materiali e variazione di posizione verificata su fonte primaria.
- **WHERE** 0: nessuna fonte primaria letta · 1: un report letto, nessun fatto che spieghi il momento · 2: report e comunicati letti, contesto coerente con gli acquisti · 3: fatto verificabile e databile che precede gli acquisti (risultati, contratto, ristrutturazione) letto sulla fonte.
- **WHEN** 0: nessun evento databile · 1: solo il report appena pubblicato (closed period appena aperto: strutturale in Europa) · 2: un evento databile futuro entro 6 mesi (AGM, scadenza, report) · 3: più eventi databili con date confermate dal calendario dell'emittente.

Ogni punteggio porta un asterisco: dipende da ciò che è stato letto, non da ciò che esiste.


Costo API di modelli linguistici per questo dossier: 0 token, 0 USD.

