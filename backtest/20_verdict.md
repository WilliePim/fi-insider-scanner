# 20 — Verdetto pre-registrato

Generato 2026-09-14T17:09:16+00:00. Criteri: `backtest/preregistration.md`. Nessuna interpretazione oltre i criteri.

## Esito: **NON REGGE**

- matched control con media <= 0

## Numeri usati

| cella | n | media | mediana | t iid | t CR1 emittente | t CR1 mese | t two-way | CI 95% | MDE | emittenti | note |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P: A (b) 50-300M 126s vs OMXSPI | 817 | -2.39% | -4.75% | -1.83 | -1.96 | -1.42 | -1.48 | [-5.00%, +0.12%] | 3.66% | 301 | t < 2, sotto MDE |
| C: stessi eventi vs peer | 817 | -0.58% | +0.00% | -0.33 | -0.34 | -0.34 | -0.36 | [-3.80%, +2.54%] | 4.90% | 301 | t < 2, sotto MDE |

Media di P con scenario S0 sugli attesi in banda: -1.48%. Copertura: 68.3%.


## Controlli

| criterio | valore |
|---|---|
| copertura | 0.6825945116100557 |
| copertura_minima | 0.6 |
| P_media_positiva | False |
| P_t_cr1_emittente_ge_2 | False |
| C_media_positiva | False |
| C_t_cr1_emittente_ge_2 | False |
| segno_invariato_S0 | True |
| C_media_le_0 | True |
| MDE_le_3_5 | False |
| CI_P_include_0 | True |

## Riferimento USA

Scanner USA su Form 4, stessa definizione: +3,50% (t = 4,30, iid) a 126 giorni in banda $50-300M vs IWM; matched control +2,41% (t = 2,02).



## Letture descrittive (non entrano nel verdetto)

- Il placebo (stessi emittenti, date spostate di -252 sessioni) contro il peer vale +4,54% (t 2,3; n 636): il confronto con il peer non e' neutro. Gli emittenti che un anno dopo avranno acquisti insider battevano gia' i pari dimensione. C = -0,58% va letto contro quel baseline positivo, non contro zero: in nessuna lettura favorisce l'ipotesi.
- Scomposizione per anno: l'eccesso contro l'indice e' quasi tutto effetto dimensione (peer vs indice +14% nel 2016-18 e +21% nel 2020, -6/-12% nel 2022-25). Il numero USA, misurato contro un indice, era esposto allo stesso confondimento.
- Closed period (colonna A, banda, 126s): acquisti entro 10 giorni dal report -6,35% (n 153, t CR1 -3,0); oltre 10 giorni +2,49% (n 277, t 0,9); data ignota 387. La direzione e' quella ipotizzata nel prompt (gli acquisti fuori dalla finestra post-report sono diversi), ma non e' significativa, e' una cella descrittiva tra molte e la data report e' nota solo per il 53% degli eventi.
- Bande: <50M vs peer +4,17% (t 1,4); >300M vs peer +0,23% (t 0,3). Nessuna banda regge il t = 2 contro il peer.
- Colonna B (cluster 4/4, banda): -1,22% (n 238, t -0,5, MDE 7,1%): sottodimensionata per rilevare +3,5%, come previsto al checkpoint 3.
- Sensibilita' della P: tutte tra -1,75% (Adj Close) e -3,39% (netto 100bp); nessuna cambia segno.

## Survivorship

- 2.126 eventi A (b) su 5.683 (37%) non hanno banda perche' l'emittente non ha una serie Yahoo verificata o un conteggio azioni alla data; 509 di questi sarebbero attesi in banda. Con lo scenario S0 la media resta -1,48%; con S_plus (+15%, uscita per acquisizione) diventerebbe +4,28%: il segno della P dipende dall'ipotesi sugli eventi mancanti solo nello scenario piu' favorevole. Il break-even p* non e' definito perche' la media osservata e' negativa.

## Cosa non e' stato possibile fare, e perche'

1. Tenere i delistati "con l'ultimo prezzo disponibile": Yahoo non ha le serie degli emittenti spariti (report 03: 2,4% verificati tra chi ha smesso di comparire nel 2016, 63% nel 2026). Sostituito da copertura per anno e scenari.
2. Un benchmark small cap o total return: su yfinance esistono solo `^OMXSPI` (price index) e nessun indice small/gross con storico. Sostituito dal peer della stessa banda (colonna C), che il placebo mostra non neutro.
3. Il flag closed period per tutti gli eventi: le date report Yahoo mancano o sono vecchie per molte small cap (ADR-043); nota solo per il 53% della P.
4. Un dilution veto simmetrico a quello USA: niente prospetti SEC; l'attivita' di emissione si vede solo dal registro (sottoscrizioni dei PDMR) e dalla crescita delle azioni Yahoo, UNKNOWN per il 39% degli eventi A.
5. Il test di invarianza per troncamento su 200 eventi (piano, `tests/snapshot/`): non implementato per tempo. Le garanzie point-in-time restano quelle dei test unitari (`Register.visible`, `test_clusters`, `test_gates`) e del test AST che vieta `expost_` e l'accesso diretto agli status nei moduli che decidono.
6. La correzione per il cambio di soglia FI (EUR 5.000 -> 20.000 dal 2024-12-04, ADR-040): non applicata; le tabelle per anno la rendono visibile.
7. Nel caso zero: tabella dei maggiori azionisti (pagina resa via JavaScript), retribuzioni, prospetto dell'emissione 2025 e lock-up non letti; le date del possesso degli insider sul sito non sono indicate.
8. Righe identiche reali perse dalla dedup upstream prima del 2026-08-16: non recuperabili dal bulk (ADR-002).
9. Nessun modello linguistico usato in nessun passo: token e costo per run = 0.
