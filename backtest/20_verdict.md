# 20 — Verdetto pre-registrato

Generato 2026-09-20T13:26:22+00:00. Criteri: `backtest/preregistration.md`. Nessuna interpretazione oltre i criteri.

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

- Il placebo (stessi emittenti, date spostate di −252 sessioni) contro il peer vale +4.54% (t iid 2.31, n 636): il confronto con il peer non è neutro. Gli emittenti che un anno dopo avranno acquisti insider battevano già i pari dimensione, quindi -0.58% va letto contro quel baseline positivo, non contro zero.
- Scomposizione per anno (report 12): l'eccesso contro l'indice segue il rendimento dei peer contro l'indice, cioè l'effetto dimensione. Il numero USA, misurato contro IWM, era esposto allo stesso confondimento.
- Closed period: acquisti entro 10 giorni dal report -6.35% (n 153, t CR1 -3.01); oltre 10 giorni +2.49% (n 277, t 0.87). La direzione è quella ipotizzata, ma la media sta sotto la propria MDE, la differenza fra i due sottoinsiemi non è testata e la data report è nota solo per il 52% degli eventi della cella P.
- Bande: A (b) lt50 vs peer +4.17% (t 1.38); B (b) lt50 vs peer +5.76% (t 1.18); A (b) 50_300 vs peer -0.58% (t -0.33); B (b) 50_300 vs peer -0.62% (t -0.18); A (b) gt300 vs peer +0.23% (t 0.29); B (b) gt300 vs peer -1.94% (t -1.48).
- Colonna B (cluster 4/4, banda): B primaria: 4/4 non stale (b) 50-300M -1.22% (n 238, MDE 7.06%).
- Sensibilità della cella P: tutte fra -3.39% e -1.75%; nessuna cambia segno.
- Il dilution veto resta UNKNOWN per il 39% degli eventi A (nessuna serie azioni alla data).

## Survivorship

- 2,126 eventi A (b) su 5,211 (41%) non hanno banda perché l'emittente non ha una serie Yahoo verificata o un conteggio azioni alla data; 509 di questi sarebbero attesi in banda. Con lo scenario S0 la media di P resta -1.48%. Il break-even p* non è definito perché la media osservata è negativa.


## Cosa non è stato possibile fare, e perché

1. Tenere i delistati "con l'ultimo prezzo disponibile": Yahoo non ha le serie degli emittenti spariti (report 03:
   2,4% di ticker verificati tra chi ha smesso di comparire nel 2016, 69,5% tra chi è ancora attivo nel 2026).
   Sostituito da copertura per anno, scenari e break-even.
2. Un benchmark small cap o total return: su yfinance esistono solo `^OMXSPI` (price index) e nessun indice
   small/gross con storico. Sostituito dal peer della stessa banda (colonna C), che il placebo mostra non neutro.
3. Il flag closed period per tutti gli eventi: le date report Yahoo mancano o sono vecchie per molte small cap (ADR-043).
4. Un dilution veto simmetrico a quello USA: niente prospetti, l'attività di emissione si vede solo dal registro e
   dalla crescita delle azioni Yahoo.
5. Il test di invarianza per troncamento su 200 eventi previsto dal piano: non implementato. Le garanzie point-in-time
   restano nei test unitari di `Register.visible`, cluster e gate, e nel test AST che vieta `expost_` e la lettura
   diretta degli status nei moduli che decidono.
6. La correzione per il cambio di soglia FI (EUR 5.000 → 20.000 dal 2024-12-04, ADR-040): non applicata; le tabelle
   per anno la rendono visibile.
7. Righe identiche reali perse dalla dedup upstream prima del 2026-08-16: non recuperabili dal bulk (ADR-002).
8. Nessun modello linguistico è stato usato in nessun passo: token e costo per run = 0.

