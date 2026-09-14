# 13 — Survivorship

Generato 2026-09-14T17:09:16+00:00.

## Stato del rendimento per anno (A variante b, tutte le bande)

| event_day | ARTEFACT | NO_ENTRY_BAR | NO_SYMBOL | OK |
|---|---|---|---|---|
| 2016 | 0 | 4 | 68 | 110 |
| 2017 | 0 | 10 | 159 | 247 |
| 2018 | 0 | 11 | 180 | 290 |
| 2019 | 0 | 13 | 202 | 296 |
| 2020 | 1 | 7 | 216 | 333 |
| 2021 | 0 | 16 | 262 | 433 |
| 2022 | 0 | 6 | 188 | 451 |
| 2023 | 1 | 7 | 117 | 443 |
| 2024 | 0 | 4 | 97 | 429 |
| 2025 | 0 | 1 | 84 | 525 |
| totale | 2 | 79 | 1,573 | 3,557 |

## Eventi senza banda (ticker o mcap mancanti)

| anno | non risolti (banda ignota) | attesi in banda |
|---|---|---|
| 2016 | 114 | 20 |
| 2017 | 255 | 35 |
| 2018 | 269 | 65 |
| 2019 | 246 | 59 |
| 2020 | 263 | 63 |
| 2021 | 341 | 90 |
| 2022 | 240 | 75 |
| 2023 | 155 | 45 |
| 2024 | 138 | 32 |
| 2025 | 105 | 25 |

Non risolti: **2,126**; attesi in banda 50-300M: **509**; con indizio di acquisizione (vendite fuori mercato allo stesso prezzo prima dell'ultima riga): 377. r̄_OMXSPI sugli eventi osservati: +4.11%.


Break-even p* (quota dei non risolti a −100% che azzera la media di P): sugli attesi in banda —, su tutti —.


## P con gli scenari aggiunti

| cella | n | media | mediana | t iid | t CR1 emittente | t CR1 mese | t two-way | CI 95% | MDE | emittenti | note |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P osservata | 817 | -2.39% | -4.75% | -1.83 | -1.96 | -1.42 | -1.48 | [-5.00%, +0.12%] | 3.66% | 301 | t < 2, sotto MDE |
| attesi_in_banda · S_minus100 (+509) | 1,326 | -41.44% | -29.06% | -26.23 | -17.77 | -9.68 | -8.99 | [-44.63%, -38.43%] | 4.43% | 600 |  |
| attesi_in_banda · S_minus50 (+509) | 1,326 | -22.25% | -29.06% | -20.96 | -16.42 | -10.23 | -9.54 | [-24.24%, -20.22%] | 2.97% | 600 |  |
| attesi_in_banda · S0 (+509) | 1,326 | -1.48% | +0.00% | -1.83 | -1.96 | -1.37 | -1.42 | [-3.08%, +0.04%] | 2.26% | 600 | t < 2, sotto MDE |
| attesi_in_banda · S_plus (+509) | 1,326 | +4.28% | +15.00% | 5.11 | 5.13 | 2.87 | 2.87 | [+2.63%, +5.97%] | 2.35% | 600 |  |
| attesi_in_banda · S_draw (+509) | 1,326 | -2.63% | -4.42% | -2.71 | -2.87 | -2.18 | -2.26 | [-4.50%, -0.73%] | 2.71% | 600 | sotto MDE |
| attesi_in_banda · S_mix_acquired (+509) | 1,326 | -33.00% | -18.34% | -21.29 | -15.43 | -9.74 | -8.93 | [-36.04%, -29.88%] | 4.34% | 600 |  |
| tutti · S_minus100 (+2126) | 2,943 | -75.87% | -104.11% | -82.94 | -44.91 | -52.19 | -37.33 | [-77.81%, -74.07%] | 2.56% | 1,030 |  |
| tutti · S_minus50 (+2126) | 2,943 | -39.75% | -54.11% | -70.94 | -43.77 | -51.27 | -37.70 | [-40.92%, -38.61%] | 1.57% | 1,030 |  |
| tutti · S0 (+2126) | 2,943 | -0.66% | +0.00% | -1.83 | -1.95 | -1.39 | -1.44 | [-1.37%, +0.04%] | 1.02% | 1,030 | t < 2, sotto MDE |
| tutti · S_plus (+2126) | 2,943 | +10.17% | +15.00% | 26.06 | 23.15 | 16.94 | 16.06 | [+9.38%, +10.92%] | 1.09% | 1,030 |  |
| tutti · S_draw (+2126) | 2,943 | -2.88% | -4.42% | -4.32 | -4.46 | -4.04 | -4.16 | [-4.15%, -1.55%] | 1.87% | 1,030 |  |
| tutti · S_mix_acquired (+2126) | 2,943 | -60.61% | -104.11% | -58.26 | -29.66 | -41.88 | -26.60 | [-62.68%, -58.56%] | 2.92% | 1,030 |  |

S_minus100 = −1 − r̄_bench; S_minus50 = −0,5 − r̄_bench; S0 = 0; S_plus = +15%; S_draw = estrazione dalla distribuzione osservata; S_mix_acquired = +15% se c'è indizio di acquisizione, altrimenti −100%.

