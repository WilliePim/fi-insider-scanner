"""Snapshot bulk dal repo civictech, pinnato a un commit upstream.

Scarica il file al commit esatto (non a `main`), così lo snapshot è riproducibile e
il suo sha256 può entrare nella pre-registrazione.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from .. import config

USER_AGENT = "fi-insider-scanner/0.1 (research)"


@dataclass
class Snapshot:
    commit_sha: str
    commit_date: str
    sha256: str
    n_bytes: int
    fetched_at: str
    path: str


def _get(url: str, accept: str | None = None) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    if accept:
        req.add_header("Accept", accept)
    with urllib.request.urlopen(req, timeout=180) as resp:
        return resp.read()


def latest_upstream_commit(repo: str, path: str) -> tuple[str, str]:
    url = f"https://api.github.com/repos/{repo}/commits?path={path}&per_page=1"
    payload = json.loads(_get(url, accept="application/vnd.github+json"))
    return payload[0]["sha"], payload[0]["commit"]["committer"]["date"]


def bulk_dir() -> Path:
    return config.RAW_DIR / "bulk"


def download(commit_sha: str | None = None) -> Snapshot:
    src = config.load()["source"]
    repo, path = src["upstream_repo"], src["upstream_path"]
    if commit_sha is None:
        commit_sha, commit_date = latest_upstream_commit(repo, path)
    else:
        info = json.loads(_get(f"https://api.github.com/repos/{repo}/commits/{commit_sha}"))
        commit_date = info["commit"]["committer"]["date"]
    data = _get(f"https://raw.githubusercontent.com/{repo}/{commit_sha}/{path}")
    digest = hashlib.sha256(data).hexdigest()
    out_dir = bulk_dir()
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{commit_date[:10]}_{commit_sha[:10]}.csv.gz"
    with gzip.open(out, "wb") as f:
        f.write(data)
    snap = Snapshot(
        commit_sha=commit_sha,
        commit_date=commit_date,
        sha256=digest,
        n_bytes=len(data),
        fetched_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        path=out.relative_to(config.REPO_ROOT).as_posix(),
    )
    out.with_suffix("").with_suffix(".json").write_text(json.dumps(asdict(snap), indent=2), encoding="utf-8")
    return snap


def load(commit_sha: str) -> tuple[bytes, Snapshot]:
    matches = sorted(bulk_dir().glob(f"*_{commit_sha[:10]}.json"))
    if not matches:
        raise FileNotFoundError(f"nessuno snapshot locale per il commit {commit_sha}; eseguire `fi-scan ingest`")
    snap = Snapshot(**json.loads(matches[0].read_text(encoding="utf-8")))
    with gzip.open(config.REPO_ROOT / snap.path, "rb") as f:
        data = f.read()
    if hashlib.sha256(data).hexdigest() != snap.sha256:
        raise ValueError(f"sha256 dello snapshot {snap.path} non corrisponde al manifest")
    return data, snap
