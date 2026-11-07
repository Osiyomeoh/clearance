"""Valid orders, written as (method, args) steps. Used by the eval, sample and tests."""
from __future__ import annotations

Step = tuple[str, tuple[str, ...]]


def isolate(cid: str, crew: str) -> list[Step]:
    steps: list[Step] = [("request", (cid, crew, "SEC_2"))]
    for sw in ("S2", "S3", "DG_SW"):
        steps += [("open_switch", (sw,)), ("tag", (cid, sw))]
    return steps + [("issue", (cid,)), ("test_dead", (cid,)), ("ground", (cid,)), ("start_work", (cid,))]


def finish(cid: str, crew: str) -> list[Step]:
    return [("clear_line", (cid,)), ("remove_ground", (cid,)), ("release", (cid, crew))] + [
        ("untag", (cid, sw)) for sw in ("S2", "S3", "DG_SW")
    ]


RESTORE: list[Step] = [("close_switch", (s,)) for s in ("S2", "S3", "DG_SW")]

ONE_CREW = isolate("C-A", "crew-a") + finish("C-A", "crew-a") + RESTORE
# Crew B tags the switches already open; opening an open switch is harmless.
TWO_CREWS = isolate("C-A", "crew-a") + isolate("C-B", "crew-b") + finish("C-A", "crew-a") \
    + finish("C-B", "crew-b") + RESTORE
VALID_ORDERS: dict[str, list[Step]] = {"one_crew": ONE_CREW, "two_crews": TWO_CREWS}
