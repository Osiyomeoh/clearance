"""Run every single-step omission and adjacent swap of the valid orders, with and without the kernel.

Unsafe = a crew or ground on a live section at any step. An unchecked run executes all steps.
Mutations that happen to stay safe are counted as such, not as catches.
"""
from __future__ import annotations
import json
import random
from itertools import combinations
from .kernel import Kernel, Refused
from .scenarios import Step, VALID_ORDERS


def run(steps: list[Step], enforce: bool) -> tuple[bool, bool]:
    """Return (unsafe_state_reached, a_step_was_refused). Refused steps are skipped, then the crew continues."""
    k = Kernel(enforce=enforce)
    refused = unsafe = False
    for method, args in steps:
        try:
            getattr(k, method)(*args)
        except Refused:
            refused = True
        unsafe = unsafe or bool(k.violations())
    return unsafe, refused


def mutants(steps: list[Step]) -> list[list[Step]]:
    out = [steps[:i] + steps[i + 1:] for i in range(len(steps))]
    for i in range(len(steps) - 1):
        if steps[i] != steps[i + 1]:
            out.append(steps[:i] + [steps[i + 1], steps[i]] + steps[i + 2:])
    return out


def evaluate() -> dict[str, int]:
    r = dict(valid_orders=0, valid_refused=0, valid_unsafe=0, mutants=0,
             unsafe_without_kernel=0, unsafe_with_kernel=0, refused_with_kernel=0)
    for steps in VALID_ORDERS.values():
        r["valid_orders"] += 1
        unsafe, refused = run(steps, enforce=True)
        r["valid_refused"] += refused
        r["valid_unsafe"] += unsafe
        for m in mutants(steps):
            r["mutants"] += 1
            r["unsafe_without_kernel"] += run(m, enforce=False)[0]
            unsafe, refused = run(m, enforce=True)
            r["unsafe_with_kernel"] += unsafe
            r["refused_with_kernel"] += refused
    return r


def hostile(steps: list[Step], rng: random.Random) -> list[Step]:
    """A broken order: reordered in places, steps dropped, and switches closed at random moments."""
    out = list(steps)
    for _ in range(rng.randint(0, 3)):
        out.pop(rng.randrange(len(out)))
    for _ in range(rng.randint(0, 3)):
        i = rng.randrange(len(out) - 1)
        out[i], out[i + 1] = out[i + 1], out[i]
    for _ in range(rng.randint(1, 3)):
        out.insert(rng.randrange(len(out) + 1), ("close_switch", (rng.choice(("S1", "S2", "S3", "TIE", "DG_SW")),)))
    return out


def stress(samples: int = 20000, seed: int = 269) -> dict[str, int]:
    """Every pair of omissions, plus seeded random hostile orders. Same unsafe test as evaluate()."""
    r = dict(cases=0, unsafe_without_kernel=0, unsafe_with_kernel=0)
    rng = random.Random(seed)
    orders = list(VALID_ORDERS.values())
    cases = [[s for k, s in enumerate(o) if k not in pair] for o in orders for pair in combinations(range(len(o)), 2)]
    cases += [hostile(rng.choice(orders), rng) for _ in range(samples)]
    for steps in cases:
        r["cases"] += 1
        r["unsafe_without_kernel"] += run(steps, enforce=False)[0]
        r["unsafe_with_kernel"] += run(steps, enforce=True)[0]
    return r


if __name__ == "__main__":
    print(json.dumps({**evaluate(), "stress": stress()}, indent=2))
