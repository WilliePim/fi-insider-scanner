# 02 — Dry-run eventi (solo registro + FX)

Generato 2026-09-14T15:03:51+00:00. Nessun prezzo azionario usato. Senza dati di mercato la crescita azioni del dilution veto e la soglia 10% del grande azionista restano sconosciute: qui BLOCKED viene solo da partecipazione/trappola nel registro e `large_holder` solo dalle parole chiave.

## Colonna A — eventi (emittente, giorno di pubblicazione) con ≥ 1 riga A_exact

| anno | eventi (a) | variante (b) | con riga on-venue | BLOCKED (registro) |
|---|---|---|---|---|
| 2016 | 350 | 190 | 279 | 12 |
| 2017 | 934 | 441 | 719 | 18 |
| 2018 | 1,175 | 525 | 912 | 29 |
| 2019 | 1,223 | 544 | 871 | 36 |
| 2020 | 1,374 | 601 | 1,078 | 34 |
| 2021 | 1,819 | 779 | 1,401 | 76 |
| 2022 | 1,793 | 686 | 1,464 | 33 |
| 2023 | 1,480 | 610 | 1,201 | 39 |
| 2024 | 1,517 | 594 | 1,221 | 46 |
| 2025 | 1,714 | 657 | 1,365 | 41 |
| 2026 | 1,388 | 484 | 1,170 | 17 |
| totale | 14,767 | 6,111 | 11,681 | 381 |

Righe per evento: mediana 1, p90 2. Valore USD per evento: mediana 102,349.


## Colonna B — trigger cluster (snapshot, timing pub)

| anno | trigger | stale (>30 gg) | S3 nella finestra | prezzo uniforme on-venue | BLOCKED (registro) | routine < 3 non-routine | grande azionista (parole chiave) | 4/4 non stale | 4/4 non stale, variante (b) |
|---|---|---|---|---|---|---|---|---|---|
| 2016 | 41 | 0 | 1 | 5 | 2 | 0 | 0 | 38 | 35 |
| 2017 | 110 | 2 | 2 | 16 | 3 | 6 | 0 | 97 | 79 |
| 2018 | 212 | 1 | 3 | 23 | 7 | 8 | 0 | 194 | 165 |
| 2019 | 206 | 1 | 0 | 24 | 5 | 8 | 1 | 191 | 169 |
| 2020 | 253 | 1 | 1 | 17 | 4 | 13 | 1 | 234 | 198 |
| 2021 | 285 | 4 | 1 | 17 | 3 | 13 | 0 | 265 | 226 |
| 2022 | 343 | 3 | 3 | 17 | 6 | 15 | 0 | 319 | 243 |
| 2023 | 303 | 1 | 4 | 13 | 2 | 19 | 2 | 277 | 227 |
| 2024 | 275 | 2 | 1 | 20 | 6 | 18 | 0 | 248 | 205 |
| 2025 | 301 | 2 | 3 | 18 | 6 | 12 | 1 | 279 | 221 |
| 2026 | 248 | 0 | 1 | 6 | 1 | 11 | 0 | 236 | 186 |
| totale | 2,577 | 17 | 20 | 176 | 45 | 123 | 5 | 2,378 | 1,954 |

Distribuzione dello score Layer 1 (tutti i trigger):

| score | n |
|---|---|
| 0 | 20 |
| 2 | 1 |
| 3 | 161 |
| 4 | 2,395 |

Persone per cluster:

| persone (8 = 8+) | n |
|---|---|
| 3 | 2,575 |
| 4 | 2 |

Trigger con due persone uguali a meno dei diacritici (possibile doppio conteggio): **4**; di questi con esattamente 3 persone (sparirebbero unendo i nomi): **4**.


Confronto con la stima grezza dello Step 0 (~3.300 cluster: ≥3 PDMR, Förvärv Aktie Aktuell non-programma, qualunque venue, nessuna esclusione di entità né di S3, cooldown 30 gg): qui 2,577 trigger con persone fisiche, righe on-venue, azioni inferite anche nel 2016-18 e S3 escluso.


## Colonna B — robustezza di visibilità e timing

| anno | snapshot + pub | as_seen + pub | snapshot + first_pub | snapshot + pub, 4/4 non stale | as_seen + pub, 4/4 non stale | first_pub, 4/4 non stale |
|---|---|---|---|---|---|---|
| 2016 | 41 | 44 | 41 | 38 | 40 | 38 |
| 2017 | 110 | 113 | 110 | 97 | 97 | 97 |
| 2018 | 212 | 215 | 213 | 194 | 197 | 195 |
| 2019 | 206 | 209 | 206 | 191 | 194 | 191 |
| 2020 | 253 | 257 | 254 | 234 | 238 | 236 |
| 2021 | 285 | 287 | 284 | 265 | 266 | 263 |
| 2022 | 343 | 346 | 344 | 319 | 325 | 323 |
| 2023 | 303 | 303 | 303 | 277 | 275 | 277 |
| 2024 | 275 | 275 | 275 | 248 | 247 | 249 |
| 2025 | 301 | 304 | 301 | 279 | 282 | 279 |
| 2026 | 248 | 249 | 248 | 236 | 237 | 236 |
| totale | 2,577 | 2,602 | 2,579 | 2,378 | 2,398 | 2,384 |

## Potenza: effetto minimo rilevabile (MDE)

MDE = (1,96 + 0,84) · sd / √n con la sd USA a 126 giorni (46%). Il finding USA è +3,50%.

| n eventi | MDE |
|---|---|
| 30 | 23.53% |
| 100 | 12.89% |
| 300 | 7.44% |
| 600 | 5.26% |
| 1,000 | 4.08% |
| 1,350 | 3.51% |
| 2,000 | 2.88% |
| 3,213 | 2.27% |

Il numero di eventi in banda $50-300M si conosce solo dopo market cap (checkpoint 6).

