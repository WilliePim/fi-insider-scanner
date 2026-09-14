# 12 — Matched control

Generato 2026-09-14T17:09:16+00:00. Peer: stessa banda alla stessa data, nessuna riga B_row visibile nei 60 giorni prima, log-cap più vicino.

## Esito della selezione del peer nella cella P

| stato gamba peer | n |
|---|---|
| OK | 817 |

## Celle per banda

| cella | n | media | mediana | t iid | t CR1 emittente | t CR1 mese | t two-way | CI 95% | MDE | emittenti | note |
|---|---|---|---|---|---|---|---|---|---|---|---|
| A (b) lt50 vs indice | 509 | +1.66% | -6.41% | 0.85 | 0.78 | 0.69 | 0.65 | [-2.05%, +5.76%] | 5.50% | 240 | t < 2, sotto MDE |
| A (b) lt50 vs peer | 509 | +4.17% | +6.94% | 1.38 | 1.26 | 1.35 | 1.24 | [-1.99%, +9.83%] | 8.46% | 240 | t < 2, sotto MDE |
| B (b) lt50 vs indice | 160 | +1.20% | -3.84% | 0.35 | 0.32 | 0.36 | 0.33 | [-5.29%, +7.13%] | 9.57% | 94 | t < 2, sotto MDE |
| B (b) lt50 vs peer | 160 | +5.76% | +4.39% | 1.18 | 1.10 | 1.28 | 1.18 | [-3.50%, +14.72%] | 13.66% | 94 | t < 2, sotto MDE |
| A (b) 50_300 vs indice | 817 | -2.39% | -4.75% | -1.83 | -1.96 | -1.42 | -1.48 | [-5.00%, +0.12%] | 3.66% | 301 | t < 2, sotto MDE |
| A (b) 50_300 vs peer | 817 | -0.58% | +0.00% | -0.33 | -0.34 | -0.34 | -0.36 | [-3.80%, +2.54%] | 4.90% | 301 | t < 2, sotto MDE |
| B (b) 50_300 vs indice | 238 | -1.22% | -3.93% | -0.48 | -0.46 | -0.47 | -0.45 | [-5.70%, +3.80%] | 7.06% | 134 | t < 2, sotto MDE |
| B (b) 50_300 vs peer | 238 | -0.62% | +0.58% | -0.18 | -0.18 | -0.15 | -0.16 | [-7.13%, +5.83%] | 9.64% | 134 | t < 2, sotto MDE |
| A (b) gt300 vs indice | 1,892 | -0.05% | -1.69% | -0.09 | -0.08 | -0.06 | -0.06 | [-1.12%, +1.07%] | 1.58% | 346 | t < 2, sotto MDE |
| A (b) gt300 vs peer | 1,892 | +0.23% | +0.00% | 0.29 | 0.28 | 0.29 | 0.28 | [-1.18%, +1.77%] | 2.19% | 346 | t < 2, sotto MDE |
| B (b) gt300 vs indice | 721 | -0.76% | -1.99% | -0.80 | -0.76 | -0.67 | -0.64 | [-2.59%, +1.20%] | 2.66% | 202 | t < 2, sotto MDE |
| B (b) gt300 vs peer | 721 | -1.94% | +0.00% | -1.48 | -1.44 | -1.44 | -1.41 | [-4.52%, +0.80%] | 3.66% | 202 | t < 2, sotto MDE |

## Scomposizione per anno (cella P)

`eccesso vs indice` − `eccesso vs peer` = rendimento medio dei peer contro l'indice: la parte attribuibile alla dimensione.

| anno | n P | eccesso vs indice | coppie | eccesso vs peer | peer vs indice |
|---|---|---|---|---|---|
| 2016 | 12 | +9.86% | 12 | -4.31% | +14.18% |
| 2017 | 25 | +5.94% | 25 | -7.39% | +13.33% |
| 2018 | 53 | +3.96% | 53 | -5.58% | +9.54% |
| 2019 | 74 | -3.41% | 74 | -4.94% | +1.53% |
| 2020 | 73 | +15.11% | 73 | -6.28% | +21.38% |
| 2021 | 103 | +0.30% | 103 | -2.57% | +2.87% |
| 2022 | 132 | -6.86% | 132 | -0.74% | -6.12% |
| 2023 | 123 | -8.76% | 123 | +2.77% | -11.53% |
| 2024 | 95 | -5.12% | 95 | +2.78% | -7.90% |
| 2025 | 127 | -6.65% | 127 | +5.06% | -11.71% |

## Placebo (date spostate di −252 sessioni, stessi emittenti)

| cella | n | media | mediana | t iid | t CR1 emittente | t CR1 mese | t two-way | CI 95% | MDE | emittenti | note |
|---|---|---|---|---|---|---|---|---|---|---|---|
| placebo vs indice | 636 | +1.76% | -4.23% | 1.19 | 1.14 | 1.11 | 1.06 | [-0.97%, +4.88%] | 4.13% | 247 | t < 2, sotto MDE |
| placebo vs peer | 636 | +4.54% | +4.88% | 2.31 | 2.23 | 2.63 | 2.51 | [+0.29%, +8.43%] | 5.49% | 247 | sotto MDE |

Atteso ≈ 0 contro il peer: un valore lontano da zero indica un bias della pipeline, non un segnale.


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

