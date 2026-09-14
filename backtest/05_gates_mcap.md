# 05 — Gate con dati di mercato e market cap

Generato 2026-09-14T16:56:09+00:00. Nessun rendimento successivo agli eventi calcolato.

## Colonna A

Eventi nel periodo 2016-07-01 – 2025-12-31: **13,379**.


Dilution veto per anno:

| event_day | BLOCKED | CAUTION | CLEAR | UNKNOWN |
|---|---|---|---|---|
| 2016 | 13 | 11 | 56 | 270 |
| 2017 | 48 | 20 | 207 | 659 |
| 2018 | 94 | 27 | 284 | 770 |
| 2019 | 77 | 25 | 490 | 631 |
| 2020 | 102 | 87 | 635 | 550 |
| 2021 | 188 | 86 | 733 | 812 |
| 2022 | 123 | 112 | 999 | 559 |
| 2023 | 105 | 84 | 910 | 381 |
| 2024 | 151 | 62 | 966 | 338 |
| 2025 | 153 | 90 | 1,243 | 228 |
| totale | 1,054 | 604 | 6,523 | 5,198 |

Motivo della market cap (data mcap = `last_trade`):

| motivo | n |
|---|---|
| OK | 8,416 |
| NO_SYMBOL | 3,669 |
| SHARES_NOT_YET_PUBLIC | 1,263 |
| NO_SHARES | 24 |
| NO_PRICE_AT_DATE | 7 |

Banda per anno:

| event_day | (null) | 50_300 | gt300 | lt50 |
|---|---|---|---|---|
| 2016 | 213 | 20 | 97 | 20 |
| 2017 | 554 | 43 | 303 | 34 |
| 2018 | 580 | 125 | 397 | 73 |
| 2019 | 550 | 182 | 373 | 118 |
| 2020 | 600 | 161 | 498 | 115 |
| 2021 | 864 | 226 | 649 | 80 |
| 2022 | 573 | 311 | 805 | 104 |
| 2023 | 415 | 299 | 626 | 140 |
| 2024 | 352 | 211 | 780 | 174 |
| 2025 | 262 | 293 | 990 | 169 |
| totale | 4,963 | 1,871 | 5,518 | 1,027 |

Dopo il gate, in banda 50-300M: **1,645**; con bordi stretti ±20%: 1,259; con bordi larghi ±20%: 2,045. Dual class tra gli eventi in banda: 292 (17.8%). Righe con tipo strumento debole (maggioranza/nome/emittente): 73. Data report nota a T: 74.8% degli eventi in banda.

## Colonna B

Eventi nel periodo 2016-07-01 – 2025-12-31: **2,329**.


Dilution veto per anno:

| event_day | BLOCKED | CAUTION | CLEAR | UNKNOWN |
|---|---|---|---|---|
| 2016 | 2 | 1 | 7 | 31 |
| 2017 | 7 | 5 | 26 | 72 |
| 2018 | 17 | 5 | 56 | 134 |
| 2019 | 10 | 4 | 87 | 105 |
| 2020 | 15 | 17 | 133 | 88 |
| 2021 | 24 | 25 | 123 | 113 |
| 2022 | 25 | 27 | 200 | 91 |
| 2023 | 25 | 21 | 190 | 67 |
| 2024 | 31 | 10 | 183 | 51 |
| 2025 | 24 | 20 | 226 | 31 |
| totale | 180 | 135 | 1,231 | 783 |

Score Layer 1 per anno (con dati di mercato):

| event_day | 0 | 2 | 3 | 4 |
|---|---|---|---|---|
| 2016 | 1 | 0 | 2 | 38 |
| 2017 | 2 | 0 | 13 | 95 |
| 2018 | 3 | 0 | 25 | 184 |
| 2019 | 0 | 0 | 19 | 187 |
| 2020 | 1 | 1 | 29 | 222 |
| 2021 | 1 | 0 | 40 | 244 |
| 2022 | 3 | 2 | 41 | 297 |
| 2023 | 4 | 3 | 43 | 253 |
| 2024 | 1 | 2 | 53 | 219 |
| 2025 | 3 | 4 | 39 | 255 |
| totale | 19 | 12 | 304 | 1,994 |

Stale: 17; 4/4 non stale (primaria B): 1978. Persone con `large_holder=true` (parole chiave o posizione ≥ 10%): 57; acquisti simbolici (limite superiore < 1%): 344.


Motivo della market cap (data mcap = `anchor`):

| motivo | n |
|---|---|
| OK | 1,632 |
| NO_SYMBOL | 474 |
| SHARES_NOT_YET_PUBLIC | 216 |
| NO_SHARES | 7 |

Banda per anno:

| event_day | (null) | 50_300 | gt300 | lt50 |
|---|---|---|---|---|
| 2016 | 25 | 2 | 12 | 2 |
| 2017 | 62 | 4 | 43 | 1 |
| 2018 | 108 | 16 | 74 | 14 |
| 2019 | 73 | 31 | 76 | 26 |
| 2020 | 91 | 34 | 96 | 32 |
| 2021 | 106 | 43 | 118 | 18 |
| 2022 | 85 | 64 | 163 | 31 |
| 2023 | 71 | 47 | 129 | 56 |
| 2024 | 51 | 44 | 131 | 49 |
| 2025 | 25 | 56 | 185 | 35 |
| totale | 697 | 341 | 1,027 | 264 |

Dopo il gate, in banda 50-300M: **275**; con bordi stretti ±20%: 198; con bordi larghi ±20%: 361. Dual class tra gli eventi in banda: 56 (20.4%). Righe con tipo strumento debole (maggioranza/nome/emittente): 6. Data report nota a T: 79.3% degli eventi in banda.


## Bordi della banda in SEK

| anno | USDSEK medio | bordo basso (M SEK) | bordo alto (M SEK) |
|---|---|---|---|
| 2016 | 8.555 | 428 | 2,567 |
| 2017 | 8.545 | 427 | 2,564 |
| 2018 | 8.693 | 435 | 2,608 |
| 2019 | 9.450 | 473 | 2,835 |
| 2020 | 9.199 | 460 | 2,760 |
| 2021 | 8.577 | 429 | 2,573 |
| 2022 | 10.113 | 506 | 3,034 |
| 2023 | 10.605 | 530 | 3,181 |
| 2024 | 10.562 | 528 | 3,169 |
| 2025 | 9.811 | 491 | 2,943 |
