"""Persist kernel state as JSON, with an append-only log and a lock for concurrent agents."""
from __future__ import annotations
import fcntl
import json
import os
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from .kernel import Grant, Kernel


def home() -> Path:
    return Path(os.environ.get("CLEARANCE_HOME", Path(__file__).resolve().parent.parent / ".state"))


def dump(k: Kernel) -> dict[str, object]:
    return {
        "open": sorted(k.open),
        "grants": [{**vars(g), "tags": sorted(g.tags)} for g in k.grants.values()],
        "log": k.log,
    }


def load(data: dict) -> Kernel:
    k = Kernel()
    k.open = set(data["open"])
    k.grants = {g["id"]: Grant(**{**g, "tags": set(g["tags"])}) for g in data["grants"]}
    k.log = data["log"]
    return k


@contextmanager
def session() -> Iterator[Kernel]:
    """Load state under an exclusive lock and save it on exit, including after a refusal."""
    root = home()
    root.mkdir(parents=True, exist_ok=True)
    with open(root / "lock", "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        path = root / "state.json"
        k = load(json.loads(path.read_text())) if path.exists() else Kernel()
        try:
            yield k
        finally:
            tmp = path.with_suffix(".tmp")
            tmp.write_text(json.dumps(dump(k), indent=1))
            tmp.replace(path)
