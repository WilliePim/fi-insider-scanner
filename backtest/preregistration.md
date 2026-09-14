# Pre-registrazione del backtest

Scritta il 2026-09-14T16:57:41+00:00, **prima** di calcolare qualsiasi rendimento successivo agli eventi.
Codice al commit `3b68c6117d7de0d8d86f92a081b457b0817741d9` (il commit che contiene questo file lo congela).

## Impronte

| voce | valore |
|---|---|
| sha256 `config/pipeline.toml` | `b67e29d72bebd4d5cab9276ee66ce0e953e27e21b23e90f3c2d84aac5c0ef8fd` |
| snapshot dati (commit upstream) | `27d8523376497b0eac9759edf6ae319e828d8c55` |
| sha256 snapshot | `462fbf2cc9bc88f1f64f1d4177946bdbafecc7113f231a4720bb123d42af02c5` |

Ogni modifica successiva a `config/pipeline.toml` o alle definizioni sotto richiede un nuovo ADR in `DECISIONS.md`
e va riportata accanto ai risultati.

## Cella primaria P

- Colonna **A** (analogo del test USA): evento = (emittente, giorno di pubblicazione) con ≥ 1 riga A_exact
  (Förvärv, azione, non programma, prezzo > 0, Antal, ≥ $25,000 per riga al cambio della data di transazione), qualunque venue.
- Gate: dilution veto ≠ BLOCKED.
- Visibilità `snapshot`, timing `pub`.
- Market cap as-of l'ultima data di transazione dell'evento, banda **[$50M, $300M)** in USD.
- Ordine dei filtri come nel test USA: gate → banda → variante (b) (un evento per emittente, successivo solo oltre 126 giorni di calendario).
- Eventi pubblicati dal 2016-07-01 al 2025-12-31.
- Rendimento a **126 sessioni**, Close split-adjusted senza dividendi, meno `^OMXSPI` sulle stesse date, lordo.
- Ingresso alla prima sessione dopo il giorno di pubblicazione; eventi con |r| > 500% esclusi come artefatti e contati.

## Colonna C sulla stessa popolazione

Peer = emittente diverso del registro con ticker non rifiutato, stessa banda alla stessa data, nessuna riga B_row visibile
con transazione negli ultimi 60 giorni, log-cap più vicino. Eccesso = r_evento − r_peer sulle stesse date.

## Criteri di verdetto

- **Copertura** = eventi della colonna A variante (b), tutte le bande, con rendimento a 126 sessioni in stato OK
  ÷ tutti gli eventi della colonna A variante (b) nel periodo. Se < 60% → **INCONCLUSIVO**, qualunque sia il resto.
- **REGGE** se valgono tutte: media P > 0 con t CR1 per emittente ≥ 2; media C > 0 con t CR1 per emittente ≥ 2;
  la media di P con lo scenario S0 (non risolti attesi in banda a eccesso 0) ha lo stesso segno di P.
- **NON REGGE** se media C ≤ 0, oppure MDE di P ≤ 3,5% e il CI bootstrap 95% di P include 0.
- **INCONCLUSIVO** altrimenti.
- Il t con cluster è None (quindi criterio non soddisfatto) se i cluster sono meno di 10.

## Tutto il resto è descrittivo

Colonna B (cluster 4/4 non stale), bande <50M e >300M, orizzonti 21 e 63, variante (a), closed period, A_onvenue,
as_seen, first_pub, Adj Close, netto 100bp, esclusione `expost_rights_issue`, dual class, bordi di banda ±20%,
solo ticker verificati, parità di bar, scenari survivorship, placebo. Nessuna di queste celle può cambiare il verdetto.
