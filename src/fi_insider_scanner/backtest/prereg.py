"""Checkpoint 6b: pre-registrazione. Scritta e committata prima di calcolare qualsiasi rendimento futuro."""

from __future__ import annotations

import subprocess
from datetime import datetime, timezone

from .. import config


def _git_head() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=config.REPO_ROOT, capture_output=True, text=True, check=True).stdout.strip()
    except Exception:  # noqa: BLE001
        return "(sconosciuto)"


def build(cfg: dict) -> str:
    src, bt, band = cfg["source"], cfg["backtest"], cfg["band"]
    return f"""# Pre-registrazione del backtest

Scritta il {datetime.now(timezone.utc).isoformat(timespec='seconds')}, **prima** di calcolare qualsiasi rendimento successivo agli eventi.
Codice al commit `{_git_head()}` (il commit che contiene questo file lo congela).

## Impronte

| voce | valore |
|---|---|
| sha256 `config/pipeline.toml` | `{config.config_sha256()}` |
| snapshot dati (commit upstream) | `{src['pinned_commit']}` |
| sha256 snapshot | `{src['pinned_sha256']}` |

Ogni modifica successiva a `config/pipeline.toml` o alle definizioni sotto richiede un nuovo ADR in `DECISIONS.md`
e va riportata accanto ai risultati.

## Cella primaria P

- Colonna **A** (analogo del test USA): evento = (emittente, giorno di pubblicazione) con ≥ 1 riga A_exact
  (Förvärv, azione, non programma, prezzo > 0, Antal, ≥ ${cfg['openmarket']['min_usd_per_row']:,.0f} per riga al cambio della data di transazione), qualunque venue.
- Gate: dilution veto ≠ BLOCKED.
- Visibilità `snapshot`, timing `pub`.
- Market cap as-of l'ultima data di transazione dell'evento, banda **[${band['low_usd']/1e6:.0f}M, ${band['high_usd']/1e6:.0f}M)** in USD.
- Ordine dei filtri come nel test USA: gate → banda → variante (b) (un evento per emittente, successivo solo oltre {bt['cooldown_calendar_days']} giorni di calendario).
- Eventi pubblicati dal {bt['start']} al {bt['end']}.
- Rendimento a **{bt['primary_horizon']} sessioni**, Close split-adjusted senza dividendi, meno `{bt['benchmark']}` sulle stesse date, lordo.
- Ingresso alla prima sessione dopo il giorno di pubblicazione; eventi con |r| > {bt['artefact_abs_return']:.0%} esclusi come artefatti e contati.

## Colonna C sulla stessa popolazione

Peer = emittente diverso del registro con ticker non rifiutato, stessa banda alla stessa data, nessuna riga B_row visibile
con transazione negli ultimi {bt['quiet_days_control']} giorni, log-cap più vicino. Eccesso = r_evento − r_peer sulle stesse date.

## Criteri di verdetto

- **Copertura** = eventi della colonna A variante (b), tutte le bande, con rendimento a {bt['primary_horizon']} sessioni in stato OK
  ÷ tutti gli eventi della colonna A variante (b) nel periodo. Se < {bt['min_coverage_for_verdict']:.0%} → **INCONCLUSIVO**, qualunque sia il resto.
- **REGGE** se valgono tutte: media P > 0 con t CR1 per emittente ≥ 2; media C > 0 con t CR1 per emittente ≥ 2;
  la media di P con lo scenario S0 (non risolti attesi in banda a eccesso 0) ha lo stesso segno di P.
- **NON REGGE** se media C ≤ 0, oppure MDE di P ≤ 3,5% e il CI bootstrap 95% di P include 0.
- **INCONCLUSIVO** altrimenti.
- Il t con cluster è None (quindi criterio non soddisfatto) se i cluster sono meno di {bt['min_clusters_for_cr1']}.

## Tutto il resto è descrittivo

Colonna B (cluster 4/4 non stale), bande <50M e >300M, orizzonti 21 e 63, variante (a), closed period, A_onvenue,
as_seen, first_pub, Adj Close, netto 100bp, esclusione `expost_rights_issue`, dual class, bordi di banda ±20%,
solo ticker verificati, parità di bar, scenari survivorship, placebo. Nessuna di queste celle può cambiare il verdetto.
"""
