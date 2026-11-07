"""CLI the room's agents call. Exit 0 = done, 3 = refused, 2 = bad use.

Authority commands need the key created by `claim-gate` in the gate agent's own directory.
"""
from __future__ import annotations
import hashlib
import json
import secrets
import sys
from pathlib import Path
from . import store
from .kernel import Refused

GATE = {"issue": "issue", "open": "open_switch", "tag": "tag", "untag": "untag", "close": "close_switch"}
CREW = {"request": "request", "test-dead": "test_dead", "ground": "ground", "start-work": "start_work",
        "clear-line": "clear_line", "remove-ground": "remove_ground", "release": "release"}
KEY = Path(".gate.key")


def digest(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def claim() -> int:
    root = store.home()
    root.mkdir(parents=True, exist_ok=True)
    reg = root / "gate.sha256"
    if reg.exists():
        print("REFUSED: the gate is already claimed")
        return 3
    key = secrets.token_hex(32)
    KEY.write_text(key)
    KEY.chmod(0o600)
    reg.write_text(digest(key))
    print("gate claimed")
    return 0


def is_gate() -> bool:
    reg = store.home() / "gate.sha256"
    return reg.exists() and KEY.exists() and digest(KEY.read_text().strip()) == reg.read_text().strip()


def board(k) -> str:
    """The feeder as one line, for a chat room. [ ] open, [X] closed, and who is on each section."""
    status = k.status()
    def sw(name: str) -> str:
        return f"[ ]{name}" if name in status["open_switches"] else f"[X]{name}"
    def sec(name: str) -> str:
        crews = [g["crew"] for g in status["clearances"] if g["section"] == name and g["state"] == "issued"]
        power = "LIVE" if name in status["live_sections"] else "DEAD"
        return f"{name}({power}{' ' + '+'.join(crews) if crews else ''})"
    lines = [f"SUB_A {sw('S1')} {sec('SEC_1')} {sw('S2')} {sec('SEC_2')} {sw('S3')} {sec('SEC_3')} {sw('TIE')} SUB_B",
             f"DG {sw('DG_SW')} SEC_2"]
    for g in status["clearances"]:
        lines.append(f"{g['id']} {g['crew']} {g['state']} tags: {' '.join(g['tags']) or 'none'}")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    cmd, args = argv[0], argv[1:]
    if cmd == "claim-gate":
        return claim()
    if cmd == "sample":
        from .sample import main as sample
        sample()
        return 0
    if cmd in GATE and not is_gate():
        print(f"REFUSED: {cmd} is for the gate agent only")
        return 3
    if cmd not in ("status", "board", "log") and cmd not in GATE and cmd not in CREW:
        print(f"unknown command {cmd}")
        return 2
    with store.session() as k:
        if cmd == "status":
            print(json.dumps(k.status(), indent=1))
            return 0
        if cmd == "board":
            print(board(k))
            return 0
        if cmd == "log":
            for row in k.log:
                print(json.dumps(row))
            return 0
        try:
            getattr(k, GATE.get(cmd) or CREW[cmd])(*args)
        except Refused as e:
            print(f"REFUSED: {e}")
            return 3
        except TypeError:
            print(f"wrong arguments for {cmd}")
            return 2
        print(f"OK {cmd} {' '.join(args)}")
        return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
