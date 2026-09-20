# 10 — Backtest colonna A (analogo del test USA)

Generato 2026-09-20T13:26:11+00:00. Pre-registrazione: `backtest/preregistration.md`.

## Imbuto verso la cella primaria P

| passo | eventi |
|---|---|
| eventi A nel periodo (variante a) | 13,379 |
| dopo dilution gate | 12,325 |
| con ticker del proprio ISIN (verified ≠ False) | 8,916 |
| con market cap | 7,694 |
| in banda 50-300M | 1,645 |
| variante (b) | 827 |
| rendimento OK a 126 sessioni | 817 |

Stati del rendimento a 126 sessioni nella cella P:

| stato | n |
|---|---|
| OK | 817 |
| NO_ENTRY_BAR | 10 |

## Cella primaria P e colonna C

| cella | n | media | mediana | t iid | t CR1 emittente | t CR1 mese | t two-way | CI 95% | MDE | emittenti | note |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P: A (b) 50-300M 126s vs OMXSPI | 817 | -2.39% | -4.75% | -1.83 | -1.96 | -1.42 | -1.48 | [-5.00%, +0.12%] | 3.66% | 301 | t < 2, sotto MDE |
| C: stessi eventi vs peer | 817 | -0.58% | +0.00% | -0.33 | -0.34 | -0.34 | -0.36 | [-3.80%, +2.54%] | 4.90% | 301 | t < 2, sotto MDE |

Portafoglio calendar-time mensile di P: t = -0.60 su 120 mesi.


Copertura (A variante b, tutte le bande, rendimento OK / eventi): **68.3%**.


## P per anno

| anno | n | media | mediana | t iid | note |
|---|---|---|---|---|---|
| 2016 | 12 | +9.86% | +5.65% | 0.84 | n < 30 |
| 2017 | 25 | +5.94% | +7.07% | 0.68 | n < 30 |
| 2018 | 53 | +3.96% | +1.89% | 1.32 |  |
| 2019 | 74 | -3.41% | -4.44% | -1.11 |  |
| 2020 | 73 | +15.11% | +6.44% | 1.89 |  |
| 2021 | 103 | +0.30% | -1.41% | 0.11 |  |
| 2022 | 132 | -6.86% | -10.67% | -1.98 |  |
| 2023 | 123 | -8.76% | -11.06% | -3.39 |  |
| 2024 | 95 | -5.12% | -8.79% | -1.46 |  |
| 2025 | 127 | -6.65% | -10.44% | -2.42 |  |

## Sensibilità (descrittive)

| cella | n | media | mediana | t iid | t CR1 emittente | t CR1 mese | t two-way | CI 95% | MDE | emittenti | note |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P primaria | 817 | -2.39% | -4.75% | -1.83 | -1.96 | -1.42 | -1.48 | [-5.00%, +0.12%] | 3.66% | 301 | t < 2, sotto MDE |
| netto 100bp | 817 | -3.39% | -5.75% | -2.60 | -2.78 | -2.01 | -2.10 | [-6.00%, -0.88%] | 3.66% | 301 | sotto MDE |
| Adj Close (limite superiore) | 817 | -1.75% | -4.17% | -1.33 | -1.42 | -1.03 | -1.07 | [-4.35%, +0.76%] | 3.68% | 301 | t < 2, sotto MDE |
| parità di bar (uscita nella serie del titolo) | 817 | -2.32% | -4.75% | -1.78 | -1.90 | -1.37 | -1.43 | [-4.91%, +0.13%] | 3.66% | 301 | t < 2, sotto MDE |
| senza expost_rights_issue | 721 | -2.13% | -4.14% | -1.65 | -1.68 | -1.38 | -1.40 | [-4.93%, +0.32%] | 3.61% | 277 | t < 2, sotto MDE |
| senza expost_large_move | 797 | -2.42% | -4.74% | -1.94 | -1.97 | -1.55 | -1.57 | [-4.78%, +0.28%] | 3.51% | 298 | t < 2, sotto MDE |
| ENDED_IN_WINDOW all'ultimo prezzo | 817 | -2.39% | -4.75% | -1.83 | -1.96 | -1.42 | -1.48 | [-5.00%, +0.12%] | 3.66% | 301 | t < 2, sotto MDE |
| A_onvenue | 641 | -2.03% | -4.33% | -1.47 | -1.55 | -1.23 | -1.28 | [-4.64%, +0.61%] | 3.87% | 257 | t < 2, sotto MDE |
| senza dilution gate | 920 | -2.01% | -4.94% | -1.59 | -1.60 | -1.26 | -1.27 | [-4.35%, +0.57%] | 3.53% | 312 | t < 2, sotto MDE |
| solo ticker verified=True | 794 | -2.06% | -4.29% | -1.54 | -1.66 | -1.19 | -1.24 | [-4.91%, +0.63%] | 3.74% | 289 | t < 2, sotto MDE |
| senza emittenti dual class | 665 | -2.19% | -5.01% | -1.44 | -1.56 | -1.17 | -1.22 | [-4.94%, +0.90%] | 4.25% | 241 | t < 2, sotto MDE |
| solo tipo strumento dichiarato/unanime | 780 | -2.59% | -5.22% | -1.93 | -2.05 | -1.48 | -1.52 | [-5.13%, -0.06%] | 3.75% | 287 | sotto MDE |
| banda con bordi stretti ±20% | 641 | -1.98% | -4.98% | -1.29 | -1.38 | -1.03 | -1.07 | [-4.94%, +1.28%] | 4.31% | 257 | t < 2, sotto MDE |
| banda con bordi larghi ±20% | 1,007 | -2.08% | -4.91% | -1.81 | -1.86 | -1.38 | -1.40 | [-4.28%, +0.39%] | 3.22% | 340 | t < 2, sotto MDE |
| visibilità as_seen + timing pub | 826 | -2.40% | -4.75% | -1.86 | -1.99 | -1.44 | -1.50 | [-4.66%, +0.30%] | 3.63% | 304 | t < 2, sotto MDE |
| visibilità snapshot + timing first_pub | 818 | -2.37% | -4.82% | -1.81 | -1.94 | -1.41 | -1.46 | [-4.79%, +0.30%] | 3.66% | 302 | t < 2, sotto MDE |

## Closed period (descrittivo)

| cella | n | media | mediana | t iid | t CR1 emittente | t CR1 mese | t two-way | CI 95% | MDE | emittenti | note |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P: dentro finestra post-report ≤ 10 gg | 153 | -6.35% | -4.42% | -2.63 | -3.01 | -2.69 | -3.10 | [-10.82%, -1.48%] | 6.76% | 86 | sotto MDE |
| P: fuori finestra (> 10 gg) | 277 | +2.49% | -2.95% | 0.87 | 0.94 | 0.68 | 0.70 | [-2.75%, +8.49%] | 7.98% | 138 | t < 2, sotto MDE |
| P: dentro finestra post-report ≤ 30 gg | 253 | -3.11% | -3.57% | -1.40 | -1.48 | -1.29 | -1.36 | [-7.57%, +1.26%] | 6.22% | 121 | t < 2, sotto MDE |
| P: fuori finestra (> 30 gg) | 177 | +2.85% | -2.93% | 0.75 | 0.78 | 0.71 | 0.73 | [-3.70%, +10.76%] | 10.61% | 110 | t < 2, sotto MDE |
| P: data report UNKNOWN | 387 | -4.32% | -6.98% | -2.73 | -2.71 | -2.73 | -2.71 | [-7.09%, -1.16%] | 4.43% | 196 | sotto MDE |

## Tutte le celle A (descrittive)

| cella | n | media | mediana | t iid | t CR1 emittente | t CR1 mese | t two-way | CI 95% | MDE | emittenti | note |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A (b) lt50 21s | 511 | +0.63% | -1.39% | 0.71 | 0.69 | 0.65 | 0.64 | [-1.11%, +2.48%] | 2.49% | 240 | t < 2, sotto MDE |
| A (b) lt50 63s | 511 | +1.69% | -2.73% | 1.17 | 1.12 | 1.13 | 1.09 | [-0.96%, +4.53%] | 4.06% | 240 | t < 2, sotto MDE |
| A (b) lt50 126s | 509 | +1.66% | -6.41% | 0.85 | 0.78 | 0.69 | 0.65 | [-2.05%, +5.76%] | 5.50% | 240 | t < 2, sotto MDE |
| A (a) lt50 21s | 802 | +0.55% | -1.41% | 0.85 | 0.70 | 0.70 | 0.66 | [-0.66%, +1.80%] | 1.82% | 240 | t < 2, sotto MDE |
| A (a) lt50 63s | 802 | +1.03% | -3.38% | 0.94 | 0.68 | 0.81 | 0.70 | [-1.14%, +3.15%] | 3.08% | 240 | t < 2, sotto MDE |
| A (a) lt50 126s | 797 | +0.27% | -7.20% | 0.18 | 0.12 | 0.13 | 0.11 | [-2.68%, +3.22%] | 4.21% | 240 | t < 2, sotto MDE |
| A (b) 50_300 21s | 817 | -0.22% | -1.00% | -0.47 | -0.45 | -0.40 | -0.39 | [-1.19%, +0.72%] | 1.33% | 301 | t < 2, sotto MDE |
| A (b) 50_300 63s | 817 | -0.15% | -2.37% | -0.18 | -0.17 | -0.17 | -0.16 | [-1.87%, +1.65%] | 2.45% | 301 | t < 2, sotto MDE |
| A (b) 50_300 126s | 817 | -2.39% | -4.75% | -1.83 | -1.96 | -1.42 | -1.48 | [-5.00%, +0.12%] | 3.66% | 301 | t < 2, sotto MDE |
| A (a) 50_300 21s | 1,629 | +0.07% | -0.55% | 0.23 | 0.21 | 0.16 | 0.16 | [-0.55%, +0.69%] | 0.89% | 301 | t < 2, sotto MDE |
| A (a) 50_300 63s | 1,629 | +0.21% | -2.08% | 0.32 | 0.24 | 0.23 | 0.22 | [-1.02%, +1.38%] | 1.79% | 301 | t < 2, sotto MDE |
| A (a) 50_300 126s | 1,629 | -1.10% | -4.52% | -1.21 | -0.79 | -0.70 | -0.62 | [-2.88%, +0.58%] | 2.55% | 301 | t < 2, sotto MDE |
| A (b) gt300 21s | 1,892 | -0.04% | -0.27% | -0.19 | -0.19 | -0.15 | -0.15 | [-0.42%, +0.37%] | 0.56% | 346 | t < 2, sotto MDE |
| A (b) gt300 63s | 1,892 | -0.39% | -0.98% | -1.02 | -1.02 | -0.70 | -0.70 | [-1.13%, +0.39%] | 1.07% | 346 | t < 2, sotto MDE |
| A (b) gt300 126s | 1,892 | -0.05% | -1.69% | -0.09 | -0.08 | -0.06 | -0.06 | [-1.12%, +1.07%] | 1.58% | 346 | t < 2, sotto MDE |
| A (a) gt300 21s | 5,226 | -0.25% | -0.41% | -2.14 | -1.45 | -1.09 | -1.06 | [-0.49%, -0.04%] | 0.33% | 346 | t < 2, sotto MDE |
| A (a) gt300 63s | 5,226 | -0.35% | -0.86% | -1.61 | -0.90 | -0.84 | -0.73 | [-0.79%, +0.05%] | 0.62% | 346 | t < 2, sotto MDE |
| A (a) gt300 126s | 5,226 | -0.45% | -1.59% | -1.36 | -0.62 | -0.75 | -0.55 | [-1.13%, +0.17%] | 0.93% | 346 | t < 2, sotto MDE |
| A (b) tutte 21s | 3,559 | +0.11% | -0.64% | 0.48 | 0.44 | 0.35 | 0.34 | [-0.34%, +0.52%] | 0.62% | 757 | t < 2, sotto MDE |
| A (b) tutte 63s | 3,558 | +0.13% | -1.69% | 0.32 | 0.31 | 0.23 | 0.23 | [-0.61%, +0.92%] | 1.11% | 757 | t < 2, sotto MDE |
| A (b) tutte 126s | 3,557 | -0.14% | -2.91% | -0.26 | -0.26 | -0.16 | -0.16 | [-1.33%, +1.01%] | 1.56% | 757 | t < 2, sotto MDE |
| A (a) tutte 21s | 8,766 | -0.06% | -0.58% | -0.47 | -0.37 | -0.23 | -0.24 | [-0.30%, +0.19%] | 0.35% | 764 | t < 2, sotto MDE |
| A (a) tutte 63s | 8,764 | +0.07% | -1.44% | 0.30 | 0.19 | 0.15 | 0.14 | [-0.39%, +0.51%] | 0.67% | 764 | t < 2, sotto MDE |
| A (a) tutte 126s | 8,761 | -0.32% | -2.58% | -0.99 | -0.55 | -0.45 | -0.40 | [-0.92%, +0.31%] | 0.92% | 764 | t < 2, sotto MDE |

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

