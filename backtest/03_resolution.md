# 03 — Risoluzione ISIN → ticker Yahoo

Generato 2026-09-14T16:24:41+00:00. Universo: ISIN con righe azionarie valide nel registro. Un ticker è `verificato` se i prezzi on-venue in SEK del registro cadono nel range giornaliero Yahoo (±2%) per ≥ 80% di ≥ 3 righe.

## Esito per ISIN

| stato | ISIN |
|---|---|
| non risolto | 1,249 |
| verificato | 742 |
| risolto non verificabile (<3 righe) | 594 |

## Metodo del ticker accettato

| metodo | ISIN |
|---|---|
| (nessuno) | 1,249 |
| nasdaq_list | 591 |
| search_name | 539 |
| search_isin | 206 |

## Motivo dell'esito

| motivo | ISIN |
|---|---|
| NO_CANDIDATE | 990 |
| OK | 742 |
| TOO_FEW_ROWS | 594 |
| NOT_VERIFIED | 259 |

## Copertura per anno dell'ultima attività nel registro

Qui si vede la survivorship: gli emittenti spariti presto non hanno serie Yahoo.

| anno ultima attività | non risolto | risolto non verificabile (<3 righe) | verificato | % verificato |
|---|---|---|---|---|
| 2016 | 32 | 9 | 1 | 2.4 |
| 2017 | 66 | 20 | 3 | 3.4 |
| 2018 | 95 | 44 | 2 | 1.4 |
| 2019 | 85 | 31 | 7 | 5.7 |
| 2020 | 104 | 47 | 10 | 6.2 |
| 2021 | 141 | 67 | 10 | 4.6 |
| 2022 | 111 | 62 | 11 | 6.0 |
| 2023 | 115 | 55 | 22 | 11.5 |
| 2024 | 135 | 63 | 37 | 15.7 |
| 2025 | 161 | 84 | 90 | 26.9 |
| 2026 | 204 | 112 | 549 | 63.5 |

## Copertura per segmento

| segmento | non risolto | risolto non verificabile (<3 righe) | verificato | % verificato |
|---|---|---|---|---|
| fnse | 288 | 67 | 200 | 36.0 |
| ngm | 177 | 5 | 1 | 0.5 |
| solo fuori mercato/estero | 239 | 304 | 0 | 0.0 |
| spotlight | 194 | 59 | 82 | 24.5 |
| xsto | 351 | 159 | 459 | 47.4 |

## Copertura degli eventi A (eventi dry-run) per anno

| event_day | ISIN mancante/non azionario | non risolto | risolto non verificabile (<3 righe) | verificato | % verificato |
|---|---|---|---|---|---|
| 2016 | 0 | 145 | 6 | 199 | 56.9 |
| 2017 | 0 | 448 | 21 | 465 | 49.8 |
| 2018 | 15 | 488 | 39 | 633 | 53.9 |
| 2019 | 55 | 494 | 29 | 645 | 52.7 |
| 2020 | 42 | 561 | 39 | 732 | 53.3 |
| 2021 | 44 | 755 | 41 | 979 | 53.8 |
| 2022 | 22 | 581 | 31 | 1,159 | 64.6 |
| 2023 | 10 | 398 | 36 | 1,036 | 70.0 |
| 2024 | 15 | 384 | 56 | 1,062 | 70.0 |
| 2025 | 13 | 325 | 49 | 1,327 | 77.4 |
| 2026 | 7 | 193 | 40 | 1,148 | 82.7 |

## Copertura degli eventi B (trigger dry-run) per anno

| event_day | non risolto | risolto non verificabile (<3 righe) | verificato | % verificato |
|---|---|---|---|---|
| 2016 | 18 | 1 | 22 | 53.7 |
| 2017 | 46 | 0 | 64 | 58.2 |
| 2018 | 89 | 0 | 123 | 58.0 |
| 2019 | 76 | 4 | 126 | 61.2 |
| 2020 | 82 | 1 | 170 | 67.2 |
| 2021 | 112 | 0 | 173 | 60.7 |
| 2022 | 106 | 0 | 237 | 69.1 |
| 2023 | 66 | 0 | 237 | 78.2 |
| 2024 | 76 | 5 | 194 | 70.5 |
| 2025 | 63 | 3 | 235 | 78.1 |
| 2026 | 26 | 4 | 218 | 87.9 |

## 30 risoluzioni verificate estratte a caso (audit manuale)

| isin | issuer_name | symbol | method | n_checked | share_in_range | median_ratio |
|---|---|---|---|---|---|---|
| SE0009554454 | Samhällsbyggnadsbolaget I Norden AB (publ) | SBB-B.ST | nasdaq_list | 137 | 0.927 | 0.998 |
| SE0014401329 | Klimator AB | KLIMAT.ST | nasdaq_list | 17 | 0.824 | 0.998 |
| SE0010546911 | Done.ai Group AB | DONE.ST | nasdaq_list | 13 | 1.000 | 0.992 |
| SE0014609061 | SECTRA AB | SECT-B.ST | search_isin | 9 | 1.000 | 1.002 |
| SE0016843809 | SHT Smart High-Tech Aktiebolag | SHT-B.ST | search_isin | 20 | 0.950 | 1.012 |
| SE0015797873 | LL Lucky Games AB (publ) | EMB.ST | nasdaq_list | 32 | 0.844 | 1.000 |
| SE0020845071 | Gosol Energy AB | GOSOL.ST | search_isin | 6 | 1.000 | 0.981 |
| SE0015407382 | Aktiebolaget Fastator (publ) | FASTAT.ST | nasdaq_list | 11 | 1.000 | 0.989 |
| SE0018534471 | Tingsvalvet Fastighets AB (publ) | TINGS-A.ST | nasdaq_list | 17 | 1.000 | 0.992 |
| SE0010323998 | Balco Group AB | BALCO.ST | nasdaq_list | 136 | 0.934 | 0.997 |
| SE0011036821 | Björn Borg AB (publ) | BORG.ST | search_isin | 5 | 1.000 | 1.003 |
| SE0011166628 | ATLAS COPCO AKTIEBOLAG | ATCO-B.ST | search_name | 20 | 1.000 | 0.993 |
| SE0010245373 | Qiiwi Games AB (publ) | QIIWI.ST | nasdaq_list | 61 | 1.000 | 0.987 |
| SE0006091724 | Precomp Solutions Aktiebolag (publ) | PCOM-B.ST | nasdaq_list | 31 | 0.935 | 1.000 |
| SE0011923341 | CAG Group AB | CAG.ST | nasdaq_list | 39 | 0.974 | 1.000 |
| SE0027597691 | SmartCraft Group AB (publ) | SMCRT.ST | nasdaq_list | 4 | 1.000 | 0.980 |
| SE0011089929 | Bodyflight Sweden AB | STHLM.ST | search_isin | 27 | 1.000 | 1.006 |
| SE0015810502 | checkin.com Group AB | CHECK.ST | nasdaq_list | 35 | 1.000 | 0.992 |
| SE0015811559 | Boliden AB | BOL.ST | search_isin | 4 | 1.000 | 0.990 |
| SE0028354936 | Kjell Group AB (publ) | KJELL.ST | nasdaq_list | 3 | 1.000 | 0.969 |
| SE0013647385 | BICO Group AB | BICO.ST | nasdaq_list | 45 | 0.956 | 1.008 |
| SE0022447348 | Flerie AB | FLERIE.ST | nasdaq_list | 4 | 1.000 | 0.989 |
| SE0017133838 | Online Brands Nordic AB | OBAB.ST | nasdaq_list | 26 | 0.923 | 0.991 |
| SE0018012494 | Modern Times Group MTG AB (publ) | MTG-B.ST | nasdaq_list | 24 | 1.000 | 1.004 |
| SE0000314312 | Tele2 AB | TEL2-B.ST | search_name | 5 | 1.000 | 1.002 |
| SE0003756758 | Sdiptech AB (publ) | SDIP-B.ST | nasdaq_list | 147 | 1.000 | 1.000 |
| SE0007578141 | Minesto AB | MINEST.ST | nasdaq_list | 40 | 1.000 | 1.013 |
| SE0005568482 | Tourn International AB (publ) | TOURN.ST | nasdaq_list | 5 | 1.000 | 0.975 |
| SE0016074256 | Bokusgruppen AB | BOKUS.ST | nasdaq_list | 42 | 1.000 | 1.000 |
| SE0013101128 | waystream holding | WAYS.ST | search_name | 3 | 1.000 | 0.994 |

## ISIN non risolti con più righe nel registro (primi 40)

| isin | issuer_name | n_rows | anno ultima attività | reason | tried |
|---|---|---|---|---|---|
| SE0000112385 | SAAB AB | 1,597 | 2026 | NOT_VERIFIED | SAAB-B.ST:PRICE_MISMATCH |
| SE0005569290 | Polyplank | 1,106 | 2025 | NO_CANDIDATE |  |
| SE0013110186 | AKELIUS RESIDENTIAL PROPERTY AB (PUBL) | 792 | 2024 | NO_CANDIDATE |  |
| SE0000667891 | Sandvik AB | 740 | 2026 | NOT_VERIFIED | SAND.ST:PRICE_MISMATCH |
| SE0000872095 | Swedish Orphan Biovitrum AB (publ) | 442 | 2026 | NOT_VERIFIED | SOBI.ST:PRICE_MISMATCH |
| SE0000163594 | Securitas AB | 435 | 2026 | NOT_VERIFIED | SECU-B.ST:PRICE_MISMATCH |
| SE0002108001 | DIGNITANA AB | 416 | 2024 | NO_CANDIDATE |  |
| SE0009697204 | Quartiers Properties AB (publ) | 394 | 2026 | NOT_VERIFIED | BOHO.ST:PRICE_MISMATCH |
| SE0010023432 | Mertiva Aktiebolag | 375 | 2020 | NO_CANDIDATE |  |
| SE0020846392 | Nodebis Applications AB (publ) | 349 | 2026 | NO_CANDIDATE |  |
| SE0012481570 | Eurobattery Minerals AB | 331 | 2026 | NOT_VERIFIED | SE0012481570.SG:FOREIGN_ONLY |
| SE0009994445 | Seamless Distribution Systems AB | 328 | 2026 | NO_CANDIDATE |  |
| SE0007278841 | Serneke Group AB | 319 | 2023 | NO_CANDIDATE |  |
| SE0003088541 | Xavitech AB | 318 | 2026 | NO_CANDIDATE |  |
| SE0016075063 | Intellego Technologies AB | 310 | 2025 | NO_CANDIDATE |  |
| SE0001666553 | ENLABS AB | 299 | 2021 | NO_CANDIDATE |  |
| JE00BLD8Y945 | COINSHARES INTERNATIONAL LIMITED | 293 | 2026 | NO_CANDIDATE |  |
| SE0017131337 | Logistea AB (publ) | 277 | 2026 | NOT_VERIFIED | LOGI-B.ST:PRICE_MISMATCH |
| SE0019763988 | Eyeon Group AB | 257 | 2026 | NO_CANDIDATE |  |
| SE0017830789 | Hoi Publishing AB | 254 | 2026 | NO_CANDIDATE |  |
| SE0003883800 | DistIT AB | 251 | 2025 | NOT_VERIFIED | DIST.ST:PRICE_MISMATCH |
| SE0010769182 | Empir Group AB | 245 | 2026 | NOT_VERIFIED | SAFETY-B.ST:PRICE_MISMATCH |
| SE0007640156 | Scandic Hotels Group AB | 245 | 2026 | NOT_VERIFIED | SHOT.ST:PRICE_MISMATCH;SE0007640156.SG:FOREIGN_ONLY |
| CA31730E1016 | FILO MINING CORP. | 238 | 2025 | NO_CANDIDATE |  |
| SE0007665823 | Resurs Holding AB (publ) | 236 | 2025 | NO_CANDIDATE |  |
| SE0007331608 | TF Bank AB | 231 | 2026 | NO_CANDIDATE |  |
| SE0000652216 | ICA Gruppen Aktiebolag | 224 | 2022 | NO_CANDIDATE |  |
| SE0000680902 | MOMENT GROUP AB | 220 | 2025 | NOT_VERIFIED | MOMENT.ST:PRICE_MISMATCH;MMGR-B.ST:PRICE_MISMATCH |
| SE0015483276 | Cint Group AB (publ) | 216 | 2026 | NOT_VERIFIED | SE0015483276.SG:FOREIGN_ONLY;8QX.MU:FOREIGN_ONLY |
| SE0003210590 | Arbona AB (publ) | 213 | 2026 | NO_CANDIDATE |  |
| SE0007048020 | Collector AB | 212 | 2022 | NOT_VERIFIED | ABSL-B.ST:PRICE_MISMATCH |
| SE0000106205 | Peab AB | 212 | 2025 | NOT_VERIFIED | PEAB-B.ST:PRICE_MISMATCH |
| SE0007464862 | ADDvise Group AB (publ) | 206 | 2026 | NO_CANDIDATE |  |
| SE0006625471 | Dustin Group AB | 200 | 2026 | NOT_VERIFIED | DUST.ST:PRICE_MISMATCH |
| SE0005505898 | myFC Holding AB | 199 | 2022 | NO_CANDIDATE |  |
| SE0012116390 | Viaplay Group AB (publ) | 194 | 2026 | NOT_VERIFIED | VPLAY-B.ST:PRICE_MISMATCH;SE0012116390.SG:FOREIGN_ONLY;VPLAY-A.ST:PRICE_MISMATCH |
| SE0000407991 | Svedbergs i Dalstorp AB | 189 | 2026 | NOT_VERIFIED | SVED-B.ST:PRICE_MISMATCH |
| SE0000379190 | Castellum Aktiebolag | 186 | 2026 | NOT_VERIFIED | CAST.ST:PRICE_MISMATCH |
| SE0001799636 | GÖTENEHUS GROUP AB | 186 | 2024 | NO_CANDIDATE |  |
| SE0012323756 | Artificial Solutions International AB | 183 | 2024 | NO_CANDIDATE |  |
