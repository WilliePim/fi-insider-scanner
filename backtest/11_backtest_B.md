# 11 — Backtest colonna B (cluster Layer 1, versione del prompt)

Generato 2026-09-20T13:26:13+00:00. Descrittivo: il verdetto dipende solo dalla colonna A.

## Imbuto

| passo | eventi |
|---|---|
| trigger B nel periodo | 2,329 |
| non stale | 2,312 |
| 4/4 non stale | 1,978 |
| con ticker del proprio ISIN | 1,546 |
| in banda 50-300M | 275 |
| variante (b) | 240 |
| rendimento OK a 126 sessioni | 238 |

## Cella B e controllo

| cella | n | media | mediana | t iid | t CR1 emittente | t CR1 mese | t two-way | CI 95% | MDE | emittenti | note |
|---|---|---|---|---|---|---|---|---|---|---|---|
| B primaria: 4/4 non stale (b) 50-300M | 238 | -1.22% | -3.93% | -0.48 | -0.46 | -0.47 | -0.45 | [-5.70%, +3.80%] | 7.06% | 134 | t < 2, sotto MDE |
| C: stessi eventi vs peer | 238 | -0.62% | +0.58% | -0.18 | -0.18 | -0.15 | -0.16 | [-7.13%, +5.83%] | 9.64% | 134 | t < 2, sotto MDE |
| senza acquisti simbolici | 222 | -0.82% | -3.62% | -0.31 | -0.30 | -0.30 | -0.29 | [-5.63%, +4.58%] | 7.45% | 127 | t < 2, sotto MDE |
| score ≥ 3 non stale | 282 | -2.05% | -5.35% | -0.89 | -0.86 | -0.88 | -0.85 | [-6.38%, +2.55%] | 6.47% | 151 | t < 2, sotto MDE |
| senza expost_rights_issue | 207 | -0.68% | -3.81% | -0.24 | -0.23 | -0.25 | -0.23 | [-5.74%, +4.46%] | 7.83% | 122 | t < 2, sotto MDE |
| Adj Close (limite superiore) | 238 | -0.79% | -2.82% | -0.31 | -0.30 | -0.30 | -0.29 | [-5.29%, +4.22%] | 7.06% | 134 | t < 2, sotto MDE |
| netto 100bp | 238 | -2.22% | -4.93% | -0.88 | -0.84 | -0.85 | -0.82 | [-6.70%, +2.80%] | 7.06% | 134 | t < 2, sotto MDE |
| score 4 non stale (b) 50-300M | 238 | -1.22% | -3.93% | -0.48 | -0.46 | -0.47 | -0.45 | [-5.70%, +3.80%] | 7.06% | 134 | t < 2, sotto MDE |
| score 3 non stale (b) 50-300M | 49 | -1.21% | -7.22% | -0.20 | -0.21 | -0.21 | -0.21 | [-12.15%, +10.39%] | 16.54% | 40 | t < 2, sotto MDE |
| score 2 non stale (b) 50-300M | 4 | +3.87% | -2.47% | 0.21 | — | — | — | [-26.56%, +34.30%] | 51.50% | 4 | n < 30, t < 2, sotto MDE |
| score 1 non stale (b) 50-300M | 0 | — | — | — | — | — | — | — | — | 0 | n < 30, t < 2 |
| score 0 non stale (b) 50-300M | 0 | — | — | — | — | — | — | — | — | 0 | n < 30, t < 2 |

Portafoglio calendar-time mensile di B: t = -0.47 su 119 mesi.


## B per anno

| anno | n | media | mediana | t iid | note |
|---|---|---|---|---|---|
| 2016 | 2 | -0.37% | -0.37% | -0.01 | n < 30 |
| 2017 | 2 | -5.52% | -5.52% | -1.95 | n < 30 |
| 2018 | 13 | +6.29% | +9.41% | 0.87 | n < 30 |
| 2019 | 28 | +0.35% | -6.89% | 0.06 | n < 30 |
| 2020 | 27 | +21.36% | +11.26% | 2.39 | n < 30 |
| 2021 | 23 | -0.53% | -1.71% | -0.07 | n < 30 |
| 2022 | 42 | -2.44% | -2.63% | -0.29 |  |
| 2023 | 31 | -2.89% | -3.42% | -0.55 |  |
| 2024 | 31 | -3.95% | -4.41% | -0.57 |  |
| 2025 | 39 | -15.91% | -23.49% | -4.05 |  |

## Closed period (descrittivo)

| cella | n | media | mediana | t iid | t CR1 emittente | t CR1 mese | t two-way | CI 95% | MDE | emittenti | note |
|---|---|---|---|---|---|---|---|---|---|---|---|
| B: dentro finestra post-report ≤ 10 gg | 36 | -5.97% | -14.83% | -0.62 | -0.62 | -0.61 | -0.61 | [-20.36%, +16.51%] | 26.81% | 30 | t < 2, sotto MDE |
| B: fuori finestra (> 10 gg) | 101 | -0.45% | -1.15% | -0.14 | -0.13 | -0.16 | -0.15 | [-6.16%, +5.78%] | 9.04% | 67 | t < 2, sotto MDE |
| B: dentro finestra post-report ≤ 30 gg | 81 | -3.95% | -4.06% | -0.83 | -0.85 | -0.85 | -0.87 | [-11.92%, +5.75%] | 13.30% | 54 | t < 2, sotto MDE |
| B: fuori finestra (> 30 gg) | 56 | +1.06% | -5.56% | 0.22 | 0.21 | 0.22 | 0.22 | [-7.97%, +10.90%] | 13.77% | 42 | t < 2, sotto MDE |
| B: data report UNKNOWN | 101 | -0.29% | -3.42% | -0.08 | -0.07 | -0.08 | -0.07 | [-6.94%, +7.46%] | 10.31% | 74 | t < 2, sotto MDE |

## Tutte le celle B (descrittive)

| cella | n | media | mediana | t iid | t CR1 emittente | t CR1 mese | t two-way | CI 95% | MDE | emittenti | note |
|---|---|---|---|---|---|---|---|---|---|---|---|
| B (b) lt50 21s | 162 | -1.15% | -1.57% | -0.84 | -0.81 | -0.83 | -0.80 | [-4.01%, +1.45%] | 3.81% | 94 | t < 2, sotto MDE |
| B (b) lt50 63s | 162 | +5.59% | -2.47% | 1.73 | 1.63 | 1.77 | 1.66 | [-0.33%, +12.25%] | 9.03% | 94 | t < 2, sotto MDE |
| B (b) lt50 126s | 160 | +1.20% | -3.84% | 0.35 | 0.32 | 0.36 | 0.33 | [-5.29%, +7.13%] | 9.57% | 94 | t < 2, sotto MDE |
| B (a) lt50 21s | 180 | -0.20% | -1.31% | -0.15 | -0.15 | -0.15 | -0.15 | [-2.75%, +2.35%] | 3.80% | 94 | t < 2, sotto MDE |
| B (a) lt50 63s | 180 | +6.66% | -2.47% | 2.14 | 1.69 | 2.19 | 1.71 | [+0.88%, +12.95%] | 8.73% | 94 | t < 2, sotto MDE |
| B (a) lt50 126s | 178 | +1.85% | -3.35% | 0.57 | 0.50 | 0.61 | 0.52 | [-4.03%, +8.44%] | 9.07% | 94 | t < 2, sotto MDE |
| B (b) 50_300 21s | 238 | -1.33% | -1.38% | -1.83 | -1.80 | -1.57 | -1.55 | [-2.74%, +0.05%] | 2.03% | 134 | t < 2, sotto MDE |
| B (b) 50_300 63s | 238 | -0.06% | -1.43% | -0.03 | -0.04 | -0.04 | -0.04 | [-3.13%, +3.29%] | 4.67% | 134 | t < 2, sotto MDE |
| B (b) 50_300 126s | 238 | -1.22% | -3.93% | -0.48 | -0.46 | -0.47 | -0.45 | [-5.70%, +3.80%] | 7.06% | 134 | t < 2, sotto MDE |
| B (a) 50_300 21s | 273 | -1.22% | -1.40% | -1.87 | -1.85 | -1.52 | -1.51 | [-2.60%, +0.03%] | 1.83% | 134 | t < 2, sotto MDE |
| B (a) 50_300 63s | 273 | -0.39% | -1.16% | -0.26 | -0.29 | -0.28 | -0.32 | [-3.18%, +2.62%] | 4.18% | 134 | t < 2, sotto MDE |
| B (a) 50_300 126s | 273 | -1.54% | -4.58% | -0.67 | -0.62 | -0.67 | -0.62 | [-5.92%, +3.18%] | 6.49% | 134 | t < 2, sotto MDE |
| B (b) gt300 21s | 721 | -0.57% | -0.73% | -1.68 | -1.82 | -1.61 | -1.73 | [-1.24%, +0.11%] | 0.96% | 202 | t < 2, sotto MDE |
| B (b) gt300 63s | 721 | -0.23% | -0.31% | -0.35 | -0.36 | -0.32 | -0.33 | [-1.52%, +1.12%] | 1.81% | 202 | t < 2, sotto MDE |
| B (b) gt300 126s | 721 | -0.76% | -1.99% | -0.80 | -0.76 | -0.67 | -0.64 | [-2.59%, +1.20%] | 2.66% | 202 | t < 2, sotto MDE |
| B (a) gt300 21s | 887 | -0.43% | -0.42% | -1.42 | -1.51 | -1.26 | -1.32 | [-1.04%, +0.16%] | 0.85% | 202 | t < 2, sotto MDE |
| B (a) gt300 63s | 887 | -0.18% | -0.33% | -0.30 | -0.30 | -0.25 | -0.25 | [-1.28%, +0.93%] | 1.63% | 202 | t < 2, sotto MDE |
| B (a) gt300 126s | 887 | -0.32% | -1.62% | -0.37 | -0.32 | -0.30 | -0.27 | [-1.98%, +1.49%] | 2.46% | 202 | t < 2, sotto MDE |
| B (b) tutte 21s | 1,248 | -0.72% | -0.67% | -2.30 | -2.33 | -1.91 | -1.93 | [-1.32%, -0.12%] | 0.88% | 397 | sotto MDE |
| B (b) tutte 63s | 1,248 | +0.58% | -1.21% | 0.78 | 0.79 | 0.66 | 0.66 | [-0.82%, +2.05%] | 2.08% | 397 | t < 2, sotto MDE |
| B (b) tutte 126s | 1,246 | -0.42% | -2.88% | -0.47 | -0.48 | -0.36 | -0.36 | [-2.13%, +1.29%] | 2.53% | 397 | t < 2, sotto MDE |
| B (a) tutte 21s | 1,522 | -0.48% | -0.60% | -1.70 | -1.77 | -1.38 | -1.42 | [-1.00%, +0.08%] | 0.79% | 397 | t < 2, sotto MDE |
| B (a) tutte 63s | 1,522 | +0.78% | -1.02% | 1.18 | 1.09 | 0.95 | 0.90 | [-0.46%, +2.12%] | 1.85% | 397 | t < 2, sotto MDE |
| B (a) tutte 126s | 1,520 | +0.12% | -2.48% | 0.14 | 0.14 | 0.11 | 0.11 | [-1.47%, +1.81%] | 2.30% | 397 | t < 2, sotto MDE |

### Formule usate

- Rendimento evento: r = Close(uscita) / Close(ingresso) − 1 (Close split-adjusted, senza dividendi).
- Eccesso: e = r − r_OMXSPI sulle stesse date di ingresso e uscita. Eccesso contro il peer: e_C = r_evento − r_peer.
- t iid = media / (sd / √n), sd con n − 1.
- t CR1 per cluster g: V = G/(G−1) · Σ_g (Σ_{i∈g} (x_i − media))² / n², t = media / √V; non calcolato con meno di 10 cluster.
- t two-way (emittente, mese di evento): V = V_emittente + V_mese − V_intersezione.
- Calendar-time: per ogni mese di calendario, media equal-weight degli eccessi mensili degli eventi in portafoglio; t iid sulla serie mensile.
- CI 95%: bootstrap percentile sugli eventi, 1.000 estrazioni, seed 12345.
- MDE (α 5% bilaterale, potenza 80%) = (1,96 + 0,84) · sd / √n.
- Costo API di modelli linguistici: 0 token, 0 USD (nessuna chiamata in nessun passo).

