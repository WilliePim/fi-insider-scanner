# 03 — Risoluzione ISIN → ticker Yahoo

Generato 2026-09-15T07:28:49+00:00. Universo: ISIN con righe azionarie valide nel registro. Un ticker è `verificato` se i prezzi on-venue in SEK del registro cadono nel range giornaliero Yahoo (±2%) per ≥ 80% di ≥ 3 righe.

## Esito per ISIN

| stato | ISIN |
|---|---|
| non risolto | 1,183 |
| verificato | 809 |
| risolto non verificabile (<3 righe) | 593 |

## Metodo del ticker accettato

| metodo | ISIN |
|---|---|
| (nessuno) | 1,183 |
| nasdaq_list | 650 |
| search_name | 542 |
| search_isin | 210 |

## Motivo dell'esito

| motivo | ISIN |
|---|---|
| NO_CANDIDATE | 990 |
| OK | 809 |
| TOO_FEW_ROWS | 593 |
| NOT_VERIFIED | 193 |

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
| 2025 | 146 | 84 | 105 | 31.3 |
| 2026 | 153 | 111 | 601 | 69.5 |

## Copertura per segmento

| segmento | non risolto | risolto non verificabile (<3 righe) | verificato | % verificato |
|---|---|---|---|---|
| fnse | 267 | 67 | 221 | 39.8 |
| ngm | 177 | 5 | 1 | 0.5 |
| solo fuori mercato/estero | 239 | 304 | 0 | 0.0 |
| spotlight | 188 | 58 | 89 | 26.6 |
| xsto | 312 | 159 | 498 | 51.4 |

## Copertura degli eventi A (eventi dry-run) per anno

| event_day | ISIN mancante/non azionario | non risolto | risolto non verificabile (<3 righe) | verificato | % verificato |
|---|---|---|---|---|---|
| 2016 | 0 | 122 | 6 | 222 | 63.4 |
| 2017 | 0 | 374 | 21 | 539 | 57.7 |
| 2018 | 15 | 371 | 37 | 752 | 64.0 |
| 2019 | 55 | 397 | 27 | 744 | 60.8 |
| 2020 | 42 | 441 | 38 | 853 | 62.1 |
| 2021 | 44 | 614 | 36 | 1,125 | 61.8 |
| 2022 | 22 | 418 | 26 | 1,327 | 74.0 |
| 2023 | 10 | 278 | 30 | 1,162 | 78.5 |
| 2024 | 15 | 240 | 45 | 1,217 | 80.2 |
| 2025 | 13 | 198 | 44 | 1,459 | 85.1 |
| 2026 | 7 | 97 | 40 | 1,244 | 89.6 |

## Copertura degli eventi B (trigger dry-run) per anno

| event_day | non risolto | risolto non verificabile (<3 righe) | verificato | % verificato |
|---|---|---|---|---|
| 2016 | 15 | 1 | 25 | 61.0 |
| 2017 | 31 | 0 | 79 | 71.8 |
| 2018 | 64 | 0 | 148 | 69.8 |
| 2019 | 57 | 4 | 145 | 70.4 |
| 2020 | 58 | 1 | 194 | 76.7 |
| 2021 | 80 | 0 | 205 | 71.9 |
| 2022 | 67 | 0 | 276 | 80.5 |
| 2023 | 45 | 0 | 258 | 85.1 |
| 2024 | 37 | 4 | 234 | 85.1 |
| 2025 | 20 | 0 | 281 | 93.4 |
| 2026 | 5 | 3 | 240 | 96.8 |

## 30 risoluzioni verificate estratte a caso (audit manuale)

| isin | issuer_name | symbol | method | n_checked | share_in_range | median_ratio |
|---|---|---|---|---|---|---|
| SE0009607252 | Intervacc AB | IVACC.ST | nasdaq_list | 51 | 0.667 | 1.006 |
| SE0009983893 | Inhalation Sciences Sweden AB | ISAB.ST | search_isin | 3 | 1.000 | 1.000 |
| SE0010663161 | Veteranpoolen AB | VPAB-B.ST | search_isin | 204 | 0.985 | 1.000 |
| SE0014781795 | Addtech AB | ADDT-B.ST | nasdaq_list | 70 | 1.000 | 0.994 |
| SE0017083835 | ChargePanel AB | CHARGE.ST | nasdaq_list | 39 | 0.795 | 1.003 |
| SE0015244520 | BioInvent International AB | BINV.ST | nasdaq_list | 59 | 1.000 | 1.001 |
| SE0000697948 | Arctic Minerals AB (publ) | ARCT.ST | search_isin | 18 | 1.000 | 1.000 |
| CH0322161768 | TalkPool AG | TALK.ST | nasdaq_list | 6 | 0.833 | 1.003 |
| SE0011337708 | AAK AB (PUBL) | AAK.ST | nasdaq_list | 41 | 1.000 | 0.999 |
| SE0014428447 | ES Energy Save Holding AB (publ) | ESGR-B.ST | nasdaq_list | 106 | 0.689 | 1.012 |
| SE0006826046 | Evolution Gaming Group AB | EVO.ST | search_isin | 40 | 1.000 | 0.996 |
| SE0014401014 | Magle Chemoswed Holding AB | MAGLE.ST | nasdaq_list | 12 | 0.917 | 0.988 |
| SE0011896661 | Bibbinstruments AB | BIBB.ST | search_name | 3 | 1.000 | 0.995 |
| SE0015382080 | Elicera Therapeutics AB | ELIC.ST | nasdaq_list | 7 | 1.000 | 0.974 |
| SE0015988167 | Swedencare AB (publ) | SECARE.ST | nasdaq_list | 59 | 1.000 | 0.998 |
| SE0025399199 | Opsy Holding AB | OPSYH.ST | search_isin | 19 | 1.000 | 1.000 |
| SE0002834507 | Micropos Medical AB | MPOS.ST | search_isin | 60 | 0.667 | 0.972 |
| SE0010441139 | Railcare Group AB | RAIL.ST | nasdaq_list | 28 | 0.893 | 0.993 |
| SE0000108847 | L E Lundbergföretagen Aktiebolag (publ) | LUND-B.ST | nasdaq_list | 37 | 1.000 | 0.998 |
| SE0006758587 | Transtema Group AB | TRANS.ST | nasdaq_list | 29 | 1.000 | 1.006 |
| SE0015948591 | Modelon AB (publ) | MODEL.ST | search_name | 38 | 0.947 | 1.000 |
| SE0016785786 | Fastighetsbolaget Emilshus AB | EMIL-B.ST | nasdaq_list | 17 | 1.000 | 0.995 |
| SE0017911480 | Heba Fastighets AB | HEBA-B.ST | nasdaq_list | 9 | 1.000 | 1.003 |
| SE0015556873 | LMK Group AB (publ) | CHEF.ST | nasdaq_list | 97 | 0.990 | 0.997 |
| SE0009663834 | Bambuser AB | BUSER.ST | search_name | 95 | 0.863 | 1.001 |
| SE0021921327 | Björn Borg AB | BORG.ST | nasdaq_list | 3 | 1.000 | 1.002 |
| SE0006117297 | Safeture AB | SFTR.ST | nasdaq_list | 79 | 0.633 | 1.045 |
| SE0007871363 | Vitec Software Group AB | VIT-B.ST | nasdaq_list | 61 | 1.000 | 1.000 |
| SE0003943620 | Enzymatica AB (publ) | ENZY.ST | nasdaq_list | 188 | 0.984 | 0.987 |
| SE0000135485 | RaySearch Laboratories AB | RAY-B.ST | nasdaq_list | 530 | 0.998 | 1.006 |

## ISIN non risolti con più righe nel registro (primi 40)

| isin | issuer_name | n_rows | anno ultima attività | reason | tried |
|---|---|---|---|---|---|
| SE0005569290 | Polyplank | 1,106 | 2025 | NO_CANDIDATE |  |
| SE0013110186 | AKELIUS RESIDENTIAL PROPERTY AB (PUBL) | 792 | 2024 | NO_CANDIDATE |  |
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
| SE0019763988 | Eyeon Group AB | 257 | 2026 | NO_CANDIDATE |  |
| SE0017830789 | Hoi Publishing AB | 254 | 2026 | NO_CANDIDATE |  |
| SE0003883800 | DistIT AB | 251 | 2025 | NOT_VERIFIED | DIST.ST:PRICE_MISMATCH |
| CA31730E1016 | FILO MINING CORP. | 238 | 2025 | NO_CANDIDATE |  |
| SE0007665823 | Resurs Holding AB (publ) | 236 | 2025 | NO_CANDIDATE |  |
| SE0007331608 | TF Bank AB | 231 | 2026 | NO_CANDIDATE |  |
| SE0000652216 | ICA Gruppen Aktiebolag | 224 | 2022 | NO_CANDIDATE |  |
| SE0015483276 | Cint Group AB (publ) | 216 | 2026 | NOT_VERIFIED | SE0015483276.SG:FOREIGN_ONLY;8QX.MU:FOREIGN_ONLY |
| SE0003210590 | Arbona AB (publ) | 213 | 2026 | NO_CANDIDATE |  |
| SE0007048020 | Collector AB | 212 | 2022 | NOT_VERIFIED | ABSL-B.ST:PRICE_MISMATCH |
| SE0007464862 | ADDvise Group AB (publ) | 206 | 2026 | NO_CANDIDATE |  |
| SE0005505898 | myFC Holding AB | 199 | 2022 | NO_CANDIDATE |  |
| SE0001799636 | GÖTENEHUS GROUP AB | 186 | 2024 | NO_CANDIDATE |  |
| SE0012323756 | Artificial Solutions International AB | 183 | 2024 | NO_CANDIDATE |  |
| SE0009664303 | Tangiamo Touch Technology AB | 182 | 2024 | NO_CANDIDATE |  |
| SE0008348767 | Trention AB | 180 | 2021 | NO_CANDIDATE |  |
| SE0007192018 | Vostok Emerging Finance Ltd | 176 | 2021 | NO_CANDIDATE |  |
| SE0013460375 | Creturner Group AB (publ) | 175 | 2026 | NO_CANDIDATE |  |
| SE0007897251 | Sydsvenska Hem AB (publ) | 173 | 2025 | NO_CANDIDATE |  |
| SE0009997331 | Omnicar Holding AB | 170 | 2023 | NO_CANDIDATE |  |
| SE0011870195 | Lime Technologies AB (publ) | 164 | 2026 | NOT_VERIFIED | LIME.ST:PRICE_MISMATCH;SE0011870195.SG:FOREIGN_ONLY |
| SE0015504626 | Ytrade Group AB | 163 | 2025 | NO_CANDIDATE |  |
| SE0005992419 | Mavshack AB (publ) | 159 | 2023 | NO_CANDIDATE |  |
| SE0005991411 | Besqab AB | 158 | 2025 | NOT_VERIFIED | BESQAB.ST:PRICE_MISMATCH;BESQAB-PREF-B.ST:PRICE_MISMATCH |
| SE0000949331 | Nobia AB | 157 | 2026 | NOT_VERIFIED | NOBI.ST:PRICE_MISMATCH |
| SE0009580756 | H100 Group AB | 153 | 2026 | NO_CANDIDATE |  |
| SE0013888963 | Ecore Group AB (publ) | 152 | 2024 | NOT_VERIFIED | HUNTER.ST:PRICE_MISMATCH |
