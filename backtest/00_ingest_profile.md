# 00 — Profilo dello snapshot grezzo

Generato 2026-09-14T13:07:14+00:00.

## Fonte

| campo | valore |
|---|---|
| repo | civictechsweden/oppna-insynsregistret |
| commit dati | 27d8523376497b0eac9759edf6ae319e828d8c55 |
| data commit | 2026-09-14T05:48:10Z |
| sha256 | 462fbf2cc9bc88f1f64f1d4177946bdbafecc7113f231a4720bb123d42af02c5 |
| byte | 42,576,638 |
| encoding | utf-8 (BOM: no) |

## Conteggi

| voce | n |
|---|---|
| record fisici letti | 166,210 |
| righe accettate | 166,201 |
| ricomposte (join) | 0 |
| celle con a capo normalizzate | 0 |
| in quarantena | 9 |

Record in quarantena (non ricomposti: la metà corrispondente non è adiacente, l'accoppiamento sarebbe una congettura):

| line_no | n_fields | kind | raw |
|---|---|---|---|
| 116,783 | 22 | truncated | 2020-03-16 13:37:05;Biovica International AB;549300VADE1VRR555N78;Anders Rylander Investment AB;Anders Rylander Investment AB;VD;Ja;Förvärv; |
| 117,090 | 22 | truncated | 2020-03-13 11:03:58;Biovica International AB;549300VADE1VRR555N78;Anders Rylander Investment AB;Anders Rylander;VD;Ja;Ja;Förvärv;Aktie;BIOVI |
| 135,321 | 22 | truncated | 2018-12-14 16:38:14;Biovica B;549300VADE1VRR555N78;Arinvest AB;Arinvest AB;Styrelseledamot/suppleant;Ja;Fel utgivare;Förvärv;Aktie;Biovica I |
| 135,391 | 22 | truncated | 2018-12-14 09:18:25;Biovica B;549300VADE1VRR555N78;Arinvest AB;Anders Rylander;Styrelseledamot/suppleant;Ja;Ja;Förvärv;Aktie;Biovica Interna |
| 135,666 | 22 | truncated | 2018-12-09 17:51:04;Biovica International AB;549300VADE1VRR555N78;Arinvest AB;Anders Rylander;VD;Ja;Ja;Lån utlåning;Aktie;Biovica B;SE000861 |
| 166,208 | 22 | continuation | 2018-12-14 00:00:00;6034,0;Antal;8,9;SEK;FIRST NORTH SWEDEN;Makulerad |
| 166,209 | 22 | continuation | 2018-12-06 00:00:00;10000,0;Antal;0,0;SEK;Utanför handelsplats;Aktuell |
| 166,210 | 22 | continuation | 2020-03-13 00:00:00;5000,0;Antal;9,6;SEK;NASDAQ STOCKHOLM AB;Aktuell |
| 166,211 | 22 | continuation | 2020-03-16 00:00:00;5800,0;Antal;8,67;SEK;NASDAQ STOCKHOLM AB;Aktuell |

## Header e mappatura canonica

Header identico alle 22 colonne attese.

| # | FI | canonico |
|---|---|---|
| 0 | Publiceringsdatum | published_at |
| 1 | Emittent | issuer_name_raw → issuer_key |
| 2 | LEI-kod | issuer_lei |
| 3 | Anmälningsskyldig | notifier_name → associate_kind |
| 4 | Person i ledande ställning | pdmr_name → person_key |
| 5 | Befattning | role_raw → roles |
| 6 | Närstående | is_closely_associated |
| 7 | Korrigering | is_amendment |
| 8 | Beskrivning av korrigering | amendment_note |
| 9 | Är förstagångsrapportering | is_initial |
| 10 | Är kopplad till aktieprogram | is_share_program |
| 11 | Karaktär | nature_raw → txn_kind |
| 12 | Instrumenttyp | instrument_type_raw → instrument_type (+ type_source) |
| 13 | Instrumentnamn | instrument_name → share_class |
| 14 | ISIN | isin |
| 15 | Transaktionsdatum | trade_date |
| 16 | Volym | volume |
| 17 | Volymsenhet | volume_unit |
| 18 | Pris | price |
| 19 | Valuta | currency |
| 20 | Handelsplats | venue_raw → venue_class |
| 21 | Status | status_raw → is_current / chain_status |

## Status e invarianti

| Status | n |
|---|---|
| Aktuell | 151322 |
| Reviderad | 11279 |
| Makulerad | 3600 |

Korrigering × Är förstagångsrapportering:

| Korrigering | (vuoto) | Ja |
|---|---|---|
| (vuoto) | 0 | 153,132 |
| Ja | 13,069 | 0 |

Violazioni dell'invariante (Korrigering=Ja ⟺ förstagång vuoto): **0**.


Duplicati esatti (22 campi): **0**. Duplicati sulla chiave upstream a 9 campi: **0** (la dedup civictech li ha già fusi: righe identiche reali perse a monte, non recuperabili dal bulk).


## Valori vuoti per colonna e anno di pubblicazione (%)

| index | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Publiceringsdatum | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| Emittent | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| LEI-kod | 62.8 | 35.6 | 4.4 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| Anmälningsskyldig | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| Person i ledande ställning | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| Befattning | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| Närstående | 77.3 | 78.9 | 73.2 | 74.9 | 71.1 | 72.3 | 76.1 | 71.9 | 72.8 | 71.7 | 70.7 |
| Korrigering | 90.5 | 92.4 | 92.2 | 92.3 | 90.7 | 90.7 | 91.9 | 93.5 | 90.9 | 93.8 | 94.5 |
| Beskrivning av korrigering | 90.5 | 92.4 | 92.2 | 92.3 | 90.7 | 90.7 | 91.9 | 93.5 | 90.9 | 93.8 | 94.5 |
| Är förstagångsrapportering | 9.5 | 7.6 | 7.8 | 7.7 | 9.3 | 9.3 | 8.1 | 6.5 | 9.1 | 6.2 | 5.5 |
| Är kopplad till aktieprogram | 87.6 | 82.8 | 86.6 | 87.7 | 87.0 | 87.0 | 88.7 | 89.2 | 89.7 | 88.0 | 87.0 |
| Karaktär | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| Instrumenttyp | 100.0 | 100.0 | 67.5 | 0.5 | 0.2 | 0.1 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| Instrumentnamn | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| ISIN | 17.0 | 13.0 | 10.5 | 10.0 | 8.4 | 8.3 | 7.0 | 6.0 | 5.9 | 6.9 | 8.4 |
| Transaktionsdatum | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| Volym | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| Volymsenhet | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| Pris | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| Valuta | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| Handelsplats | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| Status | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |

## Righe per giorno di pubblicazione

| voce | valore |
|---|---|
| massimo righe in un giorno | 456 |
| giorno con il massimo | 2021-11-18 |
| giorni con ≥ 1.000 righe (sospetto troncamento export) | 0 |
| giorni lun-ven senza righe (include festivi svedesi) | 4 |

Giorni lun-ven senza righe per anno (festivi inclusi; ~10-12/anno attesi):

| anno | giorni |
|---|---|
| 2,016 | 1 |
| 2,018 | 1 |
| 2,023 | 1 |
| 2,025 | 1 |

## Ora di pubblicazione (fuso non dichiarato dalla fonte)

| ora | righe |
|---|---|
| 0 | 937 |
| 1 | 436 |
| 2 | 293 |
| 3 | 145 |
| 4 | 308 |
| 5 | 367 |
| 6 | 665 |
| 7 | 2,598 |
| 8 | 6,939 |
| 9 | 13,790 |
| 10 | 15,638 |
| 11 | 14,142 |
| 12 | 9,908 |
| 13 | 12,902 |
| 14 | 14,115 |
| 15 | 13,749 |
| 16 | 14,040 |
| 17 | 12,246 |
| 18 | 8,394 |
| 19 | 5,855 |
| 20 | 5,944 |
| 21 | 5,378 |
| 22 | 4,708 |
| 23 | 2,704 |

## Ritardo pubblicazione − transazione (giorni)

| _year | p50 | p90 | p95 | p99 | > 30 gg (%) |
|---|---|---|---|---|---|
| 2016 | 2.0 | 6.0 | 10.0 | 39.0 | 1.7 |
| 2017 | 2.0 | 6.0 | 24.0 | 180.2 | 4.6 |
| 2018 | 2.0 | 6.0 | 15.0 | 222.1 | 3.5 |
| 2019 | 1.0 | 5.0 | 8.4 | 269.3 | 2.2 |
| 2020 | 2.0 | 5.0 | 7.8 | 117.0 | 2.4 |
| 2021 | 1.0 | 5.0 | 6.0 | 49.0 | 1.4 |
| 2022 | 1.0 | 5.0 | 7.0 | 294.8 | 2.4 |
| 2023 | 2.0 | 5.0 | 8.0 | 199.6 | 2.7 |
| 2024 | 1.0 | 5.0 | 7.0 | 158.9 | 2.3 |
| 2025 | 1.0 | 5.0 | 13.0 | 501.7 | 4.3 |
| 2026 | 1.0 | 5.0 | 6.0 | 75.8 | 1.6 |

## Karaktär per anno di pubblicazione

| Karaktär | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 | totale |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Förvärv | 2,722 | 6,817 | 7,850 | 7,739 | 8,879 | 10,741 | 11,897 | 11,455 | 9,584 | 9,181 | 6,524 | 93,389 |
| Avyttring | 1,617 | 3,213 | 3,004 | 3,372 | 4,647 | 3,813 | 3,424 | 3,196 | 3,780 | 3,493 | 1,667 | 35,226 |
| Teckning | 458 | 805 | 994 | 829 | 926 | 1,283 | 1,240 | 1,556 | 1,571 | 1,065 | 745 | 11,472 |
| Tilldelning | 0 | 228 | 592 | 646 | 897 | 1,330 | 1,086 | 1,116 | 1,102 | 1,050 | 943 | 8,990 |
| Lösen minskning | 71 | 178 | 285 | 405 | 428 | 674 | 587 | 580 | 578 | 541 | 301 | 4,628 |
| Lösen ökning | 111 | 179 | 267 | 315 | 311 | 526 | 444 | 435 | 424 | 476 | 268 | 3,756 |
| Gåva mottagen | 35 | 381 | 140 | 98 | 69 | 58 | 48 | 43 | 35 | 28 | 18 | 953 |
| Lån utlåning | 32 | 70 | 99 | 88 | 77 | 155 | 66 | 60 | 58 | 35 | 43 | 783 |
| Gåva lämnad | 43 | 86 | 103 | 75 | 100 | 79 | 54 | 64 | 62 | 39 | 31 | 736 |
| Lån återgång ökning | 0 | 32 | 57 | 71 | 69 | 127 | 61 | 126 | 63 | 25 | 16 | 647 |
| Utbyte ökning | 15 | 30 | 38 | 58 | 92 | 111 | 34 | 51 | 39 | 75 | 80 | 623 |
| Utbyte minskning | 14 | 33 | 29 | 52 | 62 | 113 | 36 | 53 | 40 | 71 | 88 | 591 |
| Konvertering ökning | 71 | 91 | 44 | 61 | 32 | 73 | 43 | 33 | 63 | 21 | 14 | 546 |
| Utdelning mottagen | 0 | 0 | 79 | 38 | 77 | 114 | 84 | 19 | 43 | 19 | 33 | 506 |
| Konvertering minskning | 40 | 51 | 28 | 54 | 21 | 95 | 29 | 45 | 39 | 10 | 10 | 422 |
| Lån mottaget | 20 | 29 | 30 | 15 | 20 | 55 | 56 | 38 | 26 | 43 | 28 | 360 |
| Inlösen egenutfärdat instrument | 10 | 41 | 31 | 19 | 45 | 33 | 21 | 66 | 46 | 13 | 5 | 330 |
| Utfärdande av instrument | 16 | 31 | 23 | 14 | 21 | 26 | 29 | 36 | 52 | 26 | 20 | 294 |
| Pantsättning | 9 | 60 | 18 | 23 | 13 | 61 | 24 | 22 | 20 | 19 | 16 | 285 |
| Lån återgång minskning | 0 | 21 | 24 | 15 | 16 | 36 | 56 | 23 | 21 | 31 | 19 | 262 |
| Fusion ökning | 0 | 0 | 0 | 1 | 20 | 34 | 26 | 33 | 31 | 26 | 67 | 238 |
| Interntransaktion – Avyttring | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 13 | 91 | 43 | 67 | 214 |
| Interntransaktion – Förvärv | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 16 | 80 | 43 | 74 | 213 |
| Utdelning lämnad | 0 | 0 | 17 | 21 | 7 | 40 | 24 | 8 | 13 | 14 | 12 | 156 |
| Pantsättning åter | 4 | 2 | 3 | 18 | 9 | 9 | 21 | 16 | 14 | 9 | 8 | 113 |
| Koncernintern överföring ökning | 0 | 0 | 0 | 0 | 0 | 17 | 12 | 3 | 21 | 12 | 6 | 71 |
| Koncernintern överföring minskning | 0 | 0 | 0 | 0 | 0 | 11 | 14 | 6 | 20 | 10 | 2 | 63 |
| Fusion minskning | 0 | 0 | 0 | 0 | 5 | 13 | 40 | 3 | 0 | 0 | 0 | 61 |
| Arv mottagen | 0 | 0 | 0 | 0 | 0 | 9 | 10 | 17 | 10 | 8 | 5 | 59 |
| Arv ökning | 12 | 12 | 15 | 8 | 10 | 0 | 0 | 0 | 0 | 0 | 0 | 57 |
| Koncernintern överföring förvärv | 0 | 0 | 8 | 19 | 14 | 2 | 0 | 0 | 0 | 0 | 0 | 43 |
| Koncernintern överföring avyttring | 0 | 0 | 8 | 14 | 15 | 2 | 0 | 0 | 0 | 0 | 0 | 39 |
| Bodelning minskning | 0 | 0 | 0 | 0 | 0 | 3 | 7 | 2 | 1 | 2 | 1 | 16 |
| Fission ökning | 0 | 0 | 0 | 0 | 0 | 8 | 0 | 5 | 1 | 0 | 1 | 15 |
| Arv minskning | 2 | 1 | 2 | 3 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 9 |
| Bodelning ökning | 0 | 0 | 0 | 0 | 0 | 2 | 5 | 1 | 0 | 1 | 0 | 9 |
| Fission minskning | 0 | 0 | 0 | 1 | 0 | 4 | 0 | 3 | 0 | 0 | 1 | 9 |
| Bodelning avyttring | 0 | 0 | 3 | 1 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 6 |
| Arv lämnad | 0 | 0 | 0 | 0 | 0 | 3 | 0 | 2 | 0 | 1 | 0 | 6 |
| Blankning | 0 | 1 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3 |
| Bodelning förvärv | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2 |

## Instrumenttyp per anno di pubblicazione

| Instrumenttyp | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 | totale |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Aktie | 0 | 0 | 3,320 | 10,329 | 13,049 | 15,256 | 15,112 | 14,691 | 13,841 | 13,347 | 9,068 | 108,013 |
| (vuoto) | 5,302 | 12,392 | 9,307 | 66 | 38 | 10 | 1 | 0 | 0 | 0 | 0 | 27,116 |
| Teckningsoption | 0 | 0 | 153 | 783 | 1,046 | 1,828 | 1,460 | 1,311 | 1,095 | 970 | 728 | 9,374 |
| BTA (betald tecknad aktie) | 0 | 0 | 380 | 974 | 758 | 516 | 715 | 996 | 727 | 660 | 430 | 6,156 |
| Option | 0 | 0 | 149 | 474 | 449 | 620 | 569 | 449 | 407 | 434 | 258 | 3,809 |
| BTU (betald tecknad unit) | 0 | 0 | 95 | 207 | 353 | 185 | 413 | 499 | 578 | 177 | 96 | 2,603 |
| Teckningsrätt/Uniträtt | 0 | 0 | 0 | 0 | 179 | 420 | 389 | 441 | 433 | 193 | 105 | 2,160 |
| Teckningsrätt | 0 | 0 | 264 | 696 | 450 | 0 | 0 | 0 | 0 | 0 | 0 | 1,410 |
| Köpoption | 0 | 0 | 0 | 107 | 134 | 198 | 193 | 209 | 257 | 171 | 98 | 1,367 |
| Warrant | 0 | 0 | 26 | 60 | 124 | 209 | 122 | 113 | 170 | 166 | 82 | 1,072 |
| Obligation | 0 | 0 | 22 | 77 | 41 | 60 | 96 | 118 | 132 | 73 | 48 | 667 |
| Konvertibel | 0 | 0 | 28 | 115 | 69 | 84 | 89 | 57 | 68 | 25 | 8 | 543 |
| Övriga derivatkontrakt | 0 | 0 | 38 | 53 | 16 | 12 | 49 | 98 | 82 | 41 | 41 | 430 |
| Inlösenaktie | 0 | 0 | 0 | 59 | 61 | 75 | 96 | 47 | 29 | 29 | 27 | 423 |
| Interimsaktie | 0 | 0 | 0 | 54 | 49 | 63 | 61 | 45 | 35 | 14 | 0 | 321 |
| Syntetisk option | 0 | 0 | 0 | 2 | 26 | 54 | 45 | 15 | 8 | 48 | 16 | 214 |
| Kapitalandelsbevis | 0 | 0 | 13 | 13 | 21 | 36 | 24 | 19 | 12 | 7 | 6 | 151 |
| Swap | 0 | 0 | 0 | 0 | 0 | 3 | 17 | 3 | 1 | 15 | 65 | 104 |
| Företagscertifikat | 0 | 0 | 0 | 1 | 15 | 4 | 13 | 6 | 27 | 0 | 0 | 66 |
| Terminer | 0 | 0 | 0 | 2 | 6 | 3 | 3 | 5 | 2 | 23 | 20 | 64 |
| Depåbevis | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 16 | 17 | 20 | 7 | 62 |
| Inlösenrätt | 0 | 0 | 0 | 0 | 0 | 10 | 3 | 4 | 5 | 16 | 9 | 47 |
| Säljoption | 0 | 0 | 0 | 1 | 0 | 12 | 5 | 3 | 2 | 1 | 1 | 25 |
| Utsläppsrätt | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 2 |
| Finansiella kontrakt avseende prisdifferenser (CFD) | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 1 |
| Auktionerad produkt baserad på en utsläppsrätt | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 1 |

## Valuta per anno di pubblicazione

| Valuta | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 | totale |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| SEK | 5,073 | 11,882 | 13,229 | 13,451 | 16,274 | 18,717 | 18,302 | 18,105 | 17,135 | 15,752 | 10,679 | 158,599 |
| CAD | 124 | 211 | 301 | 358 | 293 | 418 | 422 | 332 | 231 | 355 | 177 | 3,222 |
| EUR | 33 | 75 | 88 | 61 | 68 | 299 | 516 | 231 | 175 | 99 | 83 | 1,728 |
| USD | 32 | 112 | 110 | 135 | 148 | 100 | 147 | 327 | 244 | 120 | 87 | 1,562 |
| CHF | 20 | 44 | 32 | 34 | 47 | 63 | 29 | 43 | 37 | 41 | 22 | 412 |
| NOK | 10 | 35 | 16 | 30 | 38 | 35 | 28 | 7 | 33 | 13 | 16 | 261 |
| GBP | 0 | 0 | 3 | 1 | 3 | 15 | 23 | 41 | 37 | 40 | 42 | 205 |
| DKK | 10 | 32 | 16 | 2 | 7 | 12 | 11 | 59 | 36 | 10 | 7 | 202 |
| SCR | 0 | 0 | 0 | 0 | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 5 |
| BND | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| BWP | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 1 |
| BSD | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| RUB | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| SVC | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |

## Volymsenhet per anno di pubblicazione

| Volymsenhet | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 | totale |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Antal | 5,053 | 12,104 | 13,579 | 13,875 | 16,730 | 19,547 | 19,318 | 19,030 | 17,851 | 16,430 | 11,113 | 164,630 |
| Belopp | 249 | 288 | 216 | 198 | 155 | 113 | 160 | 115 | 77 | 0 | 0 | 1,571 |

## Handelsplats per anno di pubblicazione

| Handelsplats | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 | totale |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Utanför handelsplats | 1,985 | 4,714 | 5,038 | 5,405 | 5,663 | 8,130 | 6,710 | 6,594 | 6,542 | 5,810 | 4,349 | 60,940 |
| NASDAQ STOCKHOLM AB | 1,431 | 3,845 | 4,244 | 3,955 | 4,850 | 5,045 | 6,466 | 6,594 | 5,956 | 5,434 | 3,669 | 51,489 |
| FIRST NORTH SWEDEN | 653 | 1,677 | 1,911 | 2,144 | 3,221 | 2,479 | 2,824 | 2,315 | 2,047 | 1,839 | 1,078 | 22,188 |
| SPOTLIGHT STOCK MARKET | 0 | 0 | 432 | 1,087 | 1,193 | 1,154 | 1,428 | 1,266 | 1,243 | 719 | 521 | 9,043 |
| NORDIC GROWTH MARKET | 77 | 180 | 450 | 290 | 287 | 328 | 202 | 403 | 245 | 551 | 272 | 3,285 |
| NORDIC SME | 0 | 0 | 0 | 0 | 417 | 359 | 229 | 419 | 493 | 483 | 297 | 2,697 |
| FIRST NORTH SWEDEN - SME GROWTH MARKET | 0 | 0 | 0 | 6 | 308 | 578 | 477 | 394 | 323 | 366 | 156 | 2,608 |
| AKTIETORGET | 543 | 1,176 | 579 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 2,300 |
| OMX NORDIC EXCHANGE STOCKHOLM AB | 172 | 285 | 245 | 242 | 180 | 123 | 178 | 143 | 107 | 90 | 41 | 1,806 |
| NORDIC MTF | 62 | 175 | 393 | 299 | 124 | 36 | 11 | 11 | 0 | 5 | 8 | 1,124 |
| TORONTO STOCK EXCHANGE | 38 | 29 | 65 | 60 | 55 | 117 | 118 | 110 | 55 | 59 | 21 | 727 |
| SEB ENSKILDA | 9 | 31 | 21 | 30 | 85 | 59 | 49 | 47 | 75 | 78 | 49 | 533 |
| NASDAQ STOCKHOLM AB - NORDIC@MID | 108 | 41 | 62 | 13 | 30 | 56 | 34 | 35 | 45 | 69 | 31 | 524 |
| CBOE EUROPE - DXE ORDER BOOKS (NL) | 0 | 0 | 0 | 0 | 0 | 95 | 82 | 63 | 71 | 113 | 29 | 453 |
| FIRST NORTH SWEDEN - NORDIC@MID | 111 | 32 | 23 | 25 | 33 | 35 | 39 | 28 | 23 | 42 | 7 | 398 |
| AQUIS EXCHANGE EUROPE | 0 | 0 | 0 | 0 | 2 | 79 | 15 | 37 | 45 | 59 | 33 | 270 |
| SVENSKA HANDELSBANKEN AB - SVEX | 0 | 0 | 4 | 9 | 54 | 35 | 28 | 22 | 65 | 25 | 14 | 256 |
| TURQUOISE EUROPE | 0 | 0 | 0 | 0 | 1 | 56 | 13 | 31 | 40 | 48 | 26 | 215 |
| SVENSKA HANDELSBANKEN AB - SYSTEMATIC INTERNALISER | 0 | 0 | 4 | 18 | 24 | 31 | 33 | 41 | 20 | 19 | 8 | 198 |
| NASDAQ - ALL MARKETS | 17 | 31 | 22 | 21 | 15 | 15 | 20 | 11 | 13 | 11 | 3 | 179 |
| (altri) | 96 | 176 | 302 | 467 | 343 | 850 | 522 | 581 | 520 | 610 | 501 | 4,968 |

## Status per anno di pubblicazione

| Status | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 | totale |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Aktuell | 4,557 | 10,661 | 12,370 | 12,871 | 15,353 | 17,738 | 17,860 | 17,742 | 16,284 | 15,402 | 10,484 | 151,322 |
| Reviderad | 483 | 849 | 855 | 814 | 1,317 | 1,674 | 1,357 | 1,159 | 1,360 | 863 | 548 | 11,279 |
| Makulerad | 262 | 882 | 570 | 388 | 215 | 248 | 261 | 244 | 284 | 165 | 81 | 3,600 |

## Befattning: valori distinti per anno

| anno | valori distinti |
|---|---|
| 2016 | 594 |
| 2017 | 1,330 |
| 2018 | 1,295 |
| 2019 | 1,212 |
| 2020 | 1,127 |
| 2021 | 43 |
| 2022 | 35 |
| 2023 | 33 |
| 2024 | 25 |
| 2025 | 27 |
| 2026 | 22 |
