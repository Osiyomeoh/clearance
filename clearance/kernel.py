"""Clearance state machine following the order of 29 CFR 1910.269(m)(3).

The kernel checks physics and procedure. It does not know who is speaking: that is
Switch's job, via the addressing policy on the gate agent. `enforce=False` exists only
so the eval can measure what the same steps do with no checks.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from .network import BY_NAME, NORMALLY_OPEN, SECTIONS, SWITCHES, live_path


class Refused(Exception):
    """A step was refused. The message says why, naming what blocks it."""


@dataclass
class Grant:
    id: str
    crew: str
    section: str
    state: str = "requested"  # requested > issued > released
    tags: set[str] = field(default_factory=set)
    tested: bool = False
    grounded: bool = False
    on_line: bool = False


class Kernel:
    def __init__(self, enforce: bool = True) -> None:
        self.enforce = enforce
        self.open: set[str] = set(NORMALLY_OPEN)
        self.grants: dict[str, Grant] = {}
        self.log: list[dict[str, object]] = []

    # ---- helpers
    def _check(self, ok: bool, why: str) -> None:
        if self.enforce and not ok:
            raise Refused(why)

    def _grant(self, cid: str) -> Grant:
        if cid not in self.grants:
            raise Refused(f"no clearance {cid}")
        return self.grants[cid]

    def _active(self) -> list[Grant]:
        return [g for g in self.grants.values() if g.state != "released"]

    def _rec(self, action: str, **detail: object) -> None:
        self.log.append({"seq": len(self.log) + 1, "action": action, **detail})

    def violations(self) -> list[str]:
        """Physical facts only: is anyone or any ground on a live section right now?"""
        out = []
        for g in self.grants.values():
            path = live_path(g.section, self.open)
            if path and g.on_line:
                out.append(f"{g.crew} on live {g.section} via {'-'.join(path)}")
            if path and g.grounded:
                out.append(f"ground on live {g.section} via {'-'.join(path)}")
        return out

    # ---- (m)(3)(i)
    def request(self, cid: str, crew: str, section: str) -> None:
        if cid in self.grants:
            raise Refused(f"clearance {cid} already exists")
        if section not in SECTIONS:
            raise Refused(f"unknown section {section}")
        self.grants[cid] = Grant(cid, crew, section)
        self._rec("request", clearance=cid, crew=crew, section=section)

    # ---- (m)(3)(ii): open, then tag
    def open_switch(self, name: str) -> None:
        if name not in BY_NAME:
            raise Refused(f"unknown switch {name}")
        self.open.add(name)
        self._rec("open", switch=name)

    def tag(self, cid: str, name: str) -> None:
        g = self._grant(cid)
        if name not in BY_NAME:
            raise Refused(f"unknown switch {name}")
        self._check(name in self.open, f"cannot tag {name}: it is closed. Open it first")
        g.tags.add(name)
        self._rec("tag", clearance=cid, switch=name)

    # ---- (m)(3)(vi) precondition: the system operator gives the clearance
    def issue(self, cid: str) -> None:
        g = self._grant(cid)
        self._check(g.state == "requested", f"{cid} is {g.state}, not requested")
        path = live_path(g.section, self.open)
        self._check(path is None, f"cannot issue {cid}: {g.section} is still live via {'-'.join(path or [])}")
        unprotected = self._boundary(g.section) - g.tags
        self._check(not unprotected, f"cannot issue {cid}: not tagged for this clearance: {sorted(unprotected)}")
        g.state = "issued"
        self._rec("issue", clearance=cid)

    @staticmethod
    def _boundary(section: str) -> set[str]:
        return {s.name for s in SWITCHES if section in (s.a, s.b)}

    # ---- (m)(3)(vi), (vii), (viii)
    def test_dead(self, cid: str) -> None:
        g = self._grant(cid)
        self._check(g.state == "issued", f"{cid} has no issued clearance to test under")
        path = live_path(g.section, self.open)
        self._check(path is None, f"voltage detected on {g.section} via {'-'.join(path or [])}")
        g.tested = True
        self._rec("test_dead", clearance=cid)

    def ground(self, cid: str) -> None:
        g = self._grant(cid)
        self._check(g.tested, f"cannot ground under {cid}: not tested dead")
        g.grounded = True
        self._rec("ground", clearance=cid)

    def start_work(self, cid: str) -> None:
        g = self._grant(cid)
        self._check(g.tested and g.grounded, f"{g.crew} cannot start: {g.section} not tested and grounded")
        g.on_line = True
        self._rec("start_work", clearance=cid)

    # ---- (m)(3)(x)
    def clear_line(self, cid: str) -> None:
        g = self._grant(cid)
        g.on_line = False
        self._rec("clear_line", clearance=cid)

    def remove_ground(self, cid: str) -> None:
        g = self._grant(cid)
        self._check(not g.on_line, f"cannot remove grounds under {cid}: {g.crew} still on the line")
        g.grounded = False
        self._rec("remove_ground", clearance=cid)

    def release(self, cid: str, crew: str) -> None:
        g = self._grant(cid)
        self._check(g.state == "issued", f"{cid} is {g.state}, not issued")
        # (m)(3)(xi): only the employee in charge who requested it
        self._check(crew == g.crew, f"only {g.crew} may release {cid}, not {crew}")
        self._check(not g.on_line, f"cannot release {cid}: {g.crew} still on the line")
        self._check(not g.grounded, f"cannot release {cid}: grounds still installed")
        g.state = "released"
        self._rec("release", clearance=cid, crew=crew)

    # ---- (m)(3)(xii)
    def untag(self, cid: str, name: str) -> None:
        g = self._grant(cid)
        self._check(g.state == "released", f"cannot remove tag on {name}: {cid} not released")
        g.tags.discard(name)
        self._rec("untag", clearance=cid, switch=name)

    # ---- (m)(3)(xiii)
    def close_switch(self, name: str) -> None:
        if name not in BY_NAME:
            raise Refused(f"unknown switch {name}")
        holders = sorted(f"{g.id} ({g.crew})" for g in self.grants.values() if name in g.tags)
        self._check(not holders, f"cannot close {name}: tagged under {', '.join(holders)}")
        after = self.open - {name}
        for g in self._active():
            if g.state == "issued":
                path = live_path(g.section, after)
                self._check(path is None, f"cannot close {name}: {g.section} is under open clearance "
                                          f"{g.id} ({g.crew}) and would go live via {'-'.join(path or [])}")
        self.open.discard(name)
        self._rec("close", switch=name)

    def status(self) -> dict[str, object]:
        return {
            "open_switches": sorted(self.open),
            "live_sections": [s for s in SECTIONS if live_path(s, self.open)],
            "clearances": [
                {"id": g.id, "crew": g.crew, "section": g.section, "state": g.state, "tags": sorted(g.tags),
                 "tested": g.tested, "grounded": g.grounded, "on_line": g.on_line}
                for g in self.grants.values()
            ],
        }
