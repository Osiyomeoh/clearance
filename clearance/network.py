"""A small simulated feeder. Not a model of any real network."""
from __future__ import annotations
from collections import deque
from dataclasses import dataclass


@dataclass(frozen=True)
class Switch:
    name: str
    a: str
    b: str


SOURCES = ("SUB_A", "SUB_B", "DG")
SECTIONS = ("SEC_1", "SEC_2", "SEC_3")
SWITCHES = (
    Switch("S1", "SUB_A", "SEC_1"),
    Switch("S2", "SEC_1", "SEC_2"),
    Switch("S3", "SEC_2", "SEC_3"),
    Switch("TIE", "SEC_3", "SUB_B"),   # normally open; closing it backfeeds from feeder B
    Switch("DG_SW", "DG", "SEC_2"),    # customer generator; a backfeed source many forget
)
NORMALLY_OPEN = frozenset({"TIE"})
BY_NAME = {s.name: s for s in SWITCHES}


def live_path(section: str, open_switches: frozenset[str] | set[str]) -> list[str] | None:
    """Return the path from a source to `section`, as node and switch names, or None if dead."""
    parent: dict[str, tuple[str, str] | None] = {src: None for src in SOURCES}
    queue = deque(SOURCES)
    while queue:
        node = queue.popleft()
        if node == section:
            path = [node]
            step = parent[node]
            while step is not None:
                path += [step[1], step[0]]
                step = parent[step[0]]
            return list(reversed(path))
        for sw in SWITCHES:
            if sw.name in open_switches or node not in (sw.a, sw.b):
                continue
            nxt = sw.b if node == sw.a else sw.a
            if nxt not in parent:
                parent[nxt] = (node, sw.name)
                queue.append(nxt)
    return None
