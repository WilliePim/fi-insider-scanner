# 01 — Tabella canonica

Generato 2026-09-14T14:05:06+00:00 dallo snapshot `27d8523376`.

## Mapping

| voce | n |
|---|---|
| righe mappate | 166,201 |
| righe rifiutate (Publiceringsdatum non interpretabile o schema) | 0 |
| righe con almeno un errore di parse | 0 |

## Tassonomie

Karaktär non mappati: **0**. Instrumenttyp dichiarati non mappati: **0**.


| txn_kind | n |
|---|---|
| acq_purchase | 93,389 |
| disp_sale | 35,226 |
| subscription | 11,472 |
| grant | 8,990 |
| exercise_out | 4,628 |
| exercise_in | 3,756 |
| gift_in | 953 |
| loan_out | 783 |
| gift_out | 736 |
| loan_return_in | 647 |
| exchange_in | 623 |
| exchange_out | 591 |
| conversion_in | 546 |
| dividend_in | 506 |
| conversion_out | 422 |
| loan_in | 360 |
| redemption | 330 |
| internal_in | 327 |
| internal_out | 316 |
| issuance | 294 |
| pledge | 285 |
| loan_return_out | 262 |
| merger_in | 238 |
| dividend_out | 156 |
| inheritance_in | 116 |
| pledge_release | 113 |
| merger_out | 61 |
| division_out | 22 |
| demerger_in | 15 |
| inheritance_out | 15 |
| division_in | 11 |
| demerger_out | 9 |
| short | 3 |

| venue_class | n |
|---|---|
| off_venue | 60,992 |
| xsto | 54,020 |
| fnse | 25,243 |
| spotlight | 11,343 |
| ngm | 7,110 |
| mtf_si | 5,585 |
| foreign_exchange | 1,712 |
| other_venue | 196 |

Venue classificate come `other_venue` (trattate come on-venue):

| Handelsplats | n |
|---|---|
| NASDAQ - ALL MARKETS | 179 |
| NASDAQ CLEARING AB | 5 |
| NORDIC DERIVATIVES EXCHANGE | 3 |
| LUXEMBOURG STOCK EXCHANGE | 2 |
| NASDAQ OMX DERIVATIVES MARKETS | 2 |
| MERRILL LYNCH INTERNATIONAL | 2 |
| VANCOUVER STOCK EXCHANGE | 1 |
| INTERCONTINENTAL EXCHANGE - ICE FUTURES CANADA | 1 |
| FONDS DES RENTES / RENTENFONDS | 1 |

| associate_kind | n |
|---|---|
| self | 124,631 |
| vehicle | 34,387 |
| family | 7,183 |

| PDMR persona fisica | n |
|---|---|
| True | 159,668 |
| False | 6,501 |
| (null) | 32 |

## Identità emittente

| fonte issuer_key | n |
|---|---|
| lei | 157,856 |
| name | 3,775 |
| isin_backfill | 2,603 |
| name_backfill | 1,967 |

Emittenti distinti: **2,573** (di cui chiave da nome: 523).


## Tipo strumento

| type_source | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| isin_majority | 1,246 | 3,484 | 2,678 | 16 | 6 | 6 | 0 | 0 | 0 | 0 | 0 |
| isin_rows | 1,472 | 3,479 | 3,079 | 32 | 4 | 1 | 1 | 0 | 0 | 0 | 0 |
| issuer_name_match | 291 | 728 | 259 | 2 | 0 | 1 | 0 | 0 | 0 | 0 | 0 |
| name_rule | 886 | 1,737 | 1,285 | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| none | 1,407 | 2,964 | 2,006 | 11 | 28 | 2 | 0 | 0 | 0 | 0 | 0 |
| reported | 0 | 0 | 4,488 | 14,007 | 16,847 | 19,650 | 19,477 | 19,145 | 17,928 | 16,430 | 11,113 |

Conflitti di tipo sullo stesso ISIN (righe senza tipo dichiarato lasciate a null): **3982**.


| instrument_type | n |
|---|---|
| share | 124,415 |
| subscription_warrant | 10,455 |
| bta | 7,126 |
| (null) | 6,418 |
| option | 6,184 |
| subscription_right | 4,230 |
| btu | 2,843 |
| warrant | 1,199 |
| bond | 836 |
| convertible | 738 |
| derivative_other | 600 |
| redemption_share | 447 |
| interim_share | 418 |
| capital_certificate | 162 |
| depositary_receipt | 80 |
| redemption_right | 47 |
| emission_allowance | 3 |

Classe azioni sulle righe azionarie:

| share_class | n |
|---|---|
| (null) | 84,201 |
| B | 33,097 |
| A | 5,407 |
| D | 1,034 |
| C | 676 |

ISIN azionari con classi diverse dal nome: **53** su 2,585.


## Catene di revisione

| voce | n |
|---|---|
| correzioni (Korrigering=Ja, Aktuell o Reviderad) | 11,765 |
| collegate | 9,036 |
|   di cui a una riga Aktuell stantia (post-orizzonte) | 6 |
| ambigue (nessun link) | 60 |
| correzioni orfane | 2,669 |
| Reviderad orfane | 2,249 |

| chain_status | n |
|---|---|
| current | 151,316 |
| superseded | 9,030 |
| cancelled | 3,600 |
| orphan_revised | 2,249 |
| superseded_inferred | 6 |

Ritardo correzione − versione precedente (giorni):

| quantile | giorni |
|---|---|
| p50 | 0.5 |
| p75 | 2.1 |
| p90 | 8.1 |
| p95 | 33.0 |
| p99 | 483.9 |

Campi modificati dalla correzione (% dei link):

| campo | % |
|---|---|
| changed_isin | 20.8 |
| changed_instrument_name | 11.8 |
| changed_txn_kind | 10.1 |
| changed_volume | 10.7 |
| changed_price | 13.7 |
| changed_venue_raw | 14.2 |
| changed_role_raw | 5.8 |
| changed_notifier_name | 7.2 |
| changed_currency | 0.7 |

Righe `superseded_inferred` per mese di pubblicazione:

| mese | n |
|---|---|
| 2026-08 | 1 |
| 2026-09 | 5 |

30 catene casuali (audit manuale):

| emittente | persona | trade | pub prec. | pub corr. | status prec. | score | nota |
|---|---|---|---|---|---|---|---|
| Tangiamo Touch Technology AB | Rickard Möllerström | 2023-08-23 | 2023-08-24 10:04:13 | 2023-08-24 10:07:01 | Reviderad | 9 | Felaktigt pris per aktie |
| Netel Holding AB (publ) | Alireza Etemad | 2025-10-24 | 2025-10-25 11:44:31 | 2025-10-25 12:04:28 | Reviderad | 10 | Tre avslut har justerats då antal aktier var fel |
| Ascelia Pharma AB | Carin Linde | 2024-09-04 | 2024-09-05 17:08:26 | 2024-09-09 19:44:26 | Reviderad | 10 | Korrigering av "finansiellt instrument" pga felsrk |
| Prevas AB | Robert Demark | 2025-07-17 | 2026-02-16 09:53:16 | 2026-02-16 11:17:15 | Reviderad | 10 | Justerat befattning |
| Skanska AB | Magnus Persson | 2019-02-11 | 2019-02-13 14:42:34 | 2019-02-15 16:04:52 | Reviderad | 9 | Fel Aktiekurs rapporterad av Global Shares, ändrat |
| Profoto Holding AB | Anders  Hedebark | 2021-07-05 | 2021-07-08 10:39:03 | 2021-07-08 16:28:16 | Reviderad | 10 | Aktierna ägs av Burken Invest AB inte direkt av An |
| Enity Holding AB (publ) | Caroline Redare | 2025-06-13 | 2025-06-13 11:10:11 | 2025-06-17 13:49:04 | Reviderad | 10 | Felaktigt angiven Befattning för person i ledande  |
| Getinge | Carsten Blecker | 2022-03-01 | 2022-03-02 16:06:17 | 2022-03-03 06:53:35 | Reviderad | 6 | Initial error reporting net stock option value |
| Nordic Entertainment Group,  | Anders Borg | 2019-03-28 | 2019-03-28 10:35:09 | 2019-03-28 11:06:14 | Reviderad | 6 | Jag har rapporterar 2 transaktioner som en. Dels h |
| Clavister Holding | HENRIK OLSÉN | 2016-08-04 | 2016-08-08 13:47:38 | 2016-09-07 13:12:19 | Reviderad | 9 | Korrigering av handelsplats |
| Nolato AB | Christer Wahlquist | 2019-06-03 | 2019-06-05 12:09:43 | 2019-06-05 14:30:23 | Reviderad | 9 | handelsplats |
| Nobina AB (publ) | Martin Pagrotsky | 2022-01-25 | 2022-01-25 11:57:12 | 2022-01-25 19:45:58 | Reviderad | 9 | Felrapportering. Accept av uppköpsbud är inte på N |
| LIDDS AB | Daniel Lifveredson | 2020-07-07 | 2020-07-10 10:57:38 | 2020-07-15 11:14:37 | Reviderad | 10 | Det var fel ruta klickat. Har ändrat från "Antal"  |
| EQT AB | Christian  Sinding | 2021-12-15 | 2021-12-16 08:13:57 | 2021-12-16 08:25:37 | Reviderad | 8 | Made an error and chose the wrong "Transaktionens  |
| Betsson AB | Tristan Sjöberg | 2025-12-04 | 2025-12-04 13:38:59 | 2026-01-08 10:39:15 | Reviderad | 9 | Volym |
| Berner Industrier | Hans Lindqvist | 2024-07-30 | 2024-08-01 08:44:11 | 2024-08-01 08:55:59 | Reviderad | 8 | Ändrat namn till Berner Industrier under transakti |
| Infrea AB | Tony Andersson | 2021-08-12 | 2021-08-19 15:09:17 | 2021-08-19 16:24:43 | Reviderad | 5 | Ändrad typ av finansiellt instrument samt att det  |
| Mentice AB | Gulf Offshore Limited | 2021-08-19 | 2021-08-23 15:28:58 | 2021-08-24 22:00:58 | Reviderad | 8 | Acquisition of shares and not subscription |
| Lime Technologies AB (publ) | Tommas Davoust | 2025-07-14 | 2025-07-17 12:00:49 | 2025-07-17 12:08:39 | Reviderad | 7 | ISIN-kod nu ifylld |
| Codemill AB, org. nr 556762- | Johanna Björklund | 2021-06-22 | 2021-06-29 16:16:35 | 2021-07-01 08:39:49 | Reviderad | 7 | Ändrat namn på finansiellt instrument samt lagt ti |
| Cedergrenska AB | Per John Niklas Pålsso | 2021-05-24 | 2021-05-26 17:36:28 | 2021-05-26 21:07:01 | Reviderad | 9 | Skedde i samband med notering på First North men e |
| Coor Service Management Hold | Magdalena Viveka Maria | 2021-11-18 | 2021-11-21 19:16:57 | 2021-11-23 09:22:18 | Reviderad | 9 | pris per enhet ändrad till 2,99 |
| Hansa Medical AB | Lena Winstedt | 2018-06-14 | 2018-06-18 11:06:20 | 2018-06-19 14:30:41 | Reviderad | 10 | Pris per enhet ska var 0 SEK |
| Sportamore AB | Johan Ryding | 2020-04-07 | 2020-04-09 11:04:56 | 2020-04-09 14:16:54 | Reviderad | 9 | Uppdaterat pris per aktie |
| Avanza Bank Holding AB | Hans Toll | 2020-07-17 | 2020-07-17 15:13:16 | 2020-08-05 11:46:18 | Reviderad | 7 | Ändring av ISIN-kod. Aktien bytte tydligen ISIN-ko |
| Clas Ohlson AB | Anne Thorstvedt Sjober | 2018-06-14 | 2018-06-17 17:51:22 | 2018-06-18 10:27:53 | Reviderad | 9 | handelsplats angavs som annan istället för Nasdaq  |
| Storskogen Group AB (publ) | Pär Fredrik Bergegård | 2024-05-27 | 2024-05-29 20:21:03 | 2024-05-30 19:26:45 | Reviderad | 7 | Ändrat val av befattning |
| Aptahem AB | Ola Skanung | 2018-12-05 | 2018-12-07 09:45:50 | 2018-12-07 09:49:11 | Reviderad | 8 | Rättad från förvärv till teckning  teckningsrätter |
| SAS AB | Jens Lippestad | 2020-10-19 | 2020-10-19 22:42:51 | 2020-10-20 10:59:34 | Reviderad | 4 | Fel isin kode |
| Strax AB | Ingvi Tomasson | 2022-09-06 | 2022-09-08 18:34:30 | 2022-10-26 17:30:30 | Reviderad | 7 | Correction of ISIN code |

## Persone

| voce | n |
|---|---|
| regole di merge (middle name, stesso emittente) | 639 |
| flag NAME_AMBIGUOUS | 20 |
| flag NEAR_DUP_NAME (solo flag) | 78 |

30 merge casuali (audit manuale):

| issuer_key | nome lungo | nome breve | valido da | valido fino |
|---|---|---|---|---|
| 549300IY6ZWVN0V2P455 | pia henriksson renaudin | pia renaudin | 2024-05-07 |  |
| 54930051FIQE3WNZR345 | jane bertilsdotter jangenfeldt | jane jangenfeldt | 2021-06-16 |  |
| 549300NZXXE5X4QTK642 | helena rosenberg norrthon | helena norrthon | 2022-03-22 |  |
| 254900MYZTNVBEN5HN98 | peter jimenez hamnebo | peter hamnebo | 2021-11-09 |  |
| 529900JYCV3JMCOGGU35 | keven walter marier | keven marier | 2023-08-21 |  |
| 549300ZCX5WJ0J9YD162 | per olof danielsson | per danielsson | 2018-11-15 |  |
| 5493000MVHMSSMX8ZF36 | rolf tarnow björn åbjörnsson | rolf åbjörnsson | 2017-06-13 |  |
| 549300MBWR5H8SIJLE03 | birgitta elisabeth klasén | birgitta klasén | 2018-07-13 |  |
| 9845000469E56665DD98 | kerstin åkesson jakobsson | kerstin jakobsson | 2022-12-19 |  |
| 5299008ZUAXN43LVZF54 | johan max molin | johan molin | 2018-02-28 |  |
| 549300WF2ILKHMGV9I45 | erik jan åfors | erik åfors | 2021-05-03 |  |
| 549300AO9GBHGX75HB20 | anders f. börjesson | anders börjesson | 2016-12-06 |  |
| 213800SWOEKEF29R3C35 | nina elisabeth gilljam | nina gilljam | 2020-08-27 |  |
| 54930003B7X85HQRKN25 | alex haahr gouliaev | alex gouliaev | 2018-06-04 |  |
| 549300R9ZBT8YSFFK266 | jan-olof vilhelm arne brüer | jan-olof brüer | 2017-10-20 | 2021-11-08 |
| 549300Q5OJJLZN6Z9D25 | zendry walter zaschor svärdkrona | zendry svärdkrona | 2018-02-15 |  |
| 529900HNJP0335URJQ76 | mats kristian andersson | mats andersson | 2020-02-18 |  |
| 549300DLW63ZHWJPCF27 | mats ivan högberg | mats högberg | 2017-10-16 |  |
| 5493000EHCBQ7QQBGX32 | henrik gustaf knutsson blomquist | henrik blomquist | 2019-02-20 |  |
| 549300ZWVSKHHDQPES93 | lars erik mikael corneliusson | lars corneliusson | 2017-06-19 |  |
| 549300QNP402ETFTHA84 | joel magnus eklund | joel eklund | 2021-06-19 |  |
| 529900A9NKQW5UTHBG13 | asger drewes joergensen | asger joergensen | 2021-05-25 |  |
| 636700YZV2OGKR4JT044 | magnus thousgaard terrvik | magnus terrvik | 2023-12-04 |  |
| 54930038JVQ3CMTEO084 | johan magnus hagberg | johan hagberg | 2018-07-17 |  |
| 549300BFHBYZ3X96EP25 | kurt gösta ingemar nilsson | kurt nilsson | 2020-05-25 |  |
| 529900BGZZZTLLBR1X49 | john lennart brehmer | john brehmer | 2018-04-27 |  |
| 967600FS3960QOJQ3O11 | anders olof althin | anders althin | 2016-10-20 |  |
| 9845005C4CS60BD72F25 | hans gustaf jacobsson | hans jacobsson | 2022-07-13 | 2024-07-29 |
| 549300NZXXE5X4QTK642 | peter a jörgensen | peter jörgensen | 2026-05-19 |  |
| 254900UBKNY2EJ588J53 | erik jonas petter fällström | erik fällström | 2018-10-19 |  |

Esempi NEAR_DUP_NAME:

| issuer_key | detail |
|---|---|
| 213800T8PC8Q4FYJZR07 | mats rahmstrom; mats rahmström |
| 213800U7P9GOIRKCTB34 | per franzen; per franzén |
| 529900BWE386D22MGZ23 | simon saneback; sïmon saneback |
| 5493000J0DZNPRLJ3M37 | lars-hakan thorell; lars-håkan thorell |
| 5493002L6I4YHANEYR87 | magnus soderlind; magnus söderlind |
| 5493002M678EZ84V7V02 | helge krogsbol; helge krogsböl |
| 5493002YR9VCJJPWYN08 | rene spogard; rené spogard |
| 549300371XEVL2VPY229 | gunnar steinn jonsson; gunnar steinn jónsson |
| 54930037JP1GWORMFS83 | carl jonas ahlen; carl jonas ahlén |
| 5493003DT9I74XXUSM04 | mats jamterud; mats jämterud |
| 54930054EB7KX3MY2Q11 | lars hojgard hansen; lars höjgard hansen; lars höjgård hansen |
| 5493006B6J2A44JJYD81 | mattias moden; mattias modén |
| 5493006E0IJD0DHJSR89 | jorgen lindemann; jörgen lindemann |
| 5493006Z2OCWV16RAE42 | linda canive; linda canivé |
| 54930070F55O6PDFDF97 | johan nordstrom; johan nordström |
| 54930075I19A3091WR29 | joao caldas; joão caldas |
| 54930075I19A3091WR29 | oscar salen; oscar salén |
| 5493007I1HS4U2HMQH48 | bulent balikci; bülent balikci |
| 5493008XT7ASRU1BJF11 | ozkan ego; özkan ego |
| 549300C0DH9EESDQUA52 | mats thoren; mats thorén |
