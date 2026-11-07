"""Replay the room's scenario with no Switch, no agent and no keys. The kernel's refusals are real;
the addressing refusal is printed as a label because only a Switch server can produce it."""
from __future__ import annotations
from .evaluate import evaluate
from .kernel import Kernel, Refused
from .scenarios import finish, isolate


def say(who: str, text: str) -> None:
    print(f"{who:>10} | {text}")


def attempt(k: Kernel, who: str, label: str, method: str, *args: str) -> None:
    say(who, label)
    try:
        getattr(k, method)(*args)
        say("kernel", "OK")
    except Refused as e:
        say("kernel", f"REFUSED: {e}")


def main() -> None:
    print("SIMULATED network. Never connects to or operates real equipment.\n")
    k = Kernel()
    say("switch", "[only in a real room] crew-a's 'approve' to @gate: refused by Switch's addressing policy")
    k.request("C-A", "crew-a", "SEC_2")
    k.open_switch("S2"); k.tag("C-A", "S2")
    k.open_switch("S3"); k.tag("C-A", "S3")
    attempt(k, "operator", "issue C-A (the customer generator was left out of the order)", "issue", "C-A")
    k.open_switch("DG_SW"); k.tag("C-A", "DG_SW")
    attempt(k, "operator", "issue C-A after opening and tagging DG_SW", "issue", "C-A")
    for m, a in isolate("C-A", "crew-a")[-3:]:
        if m != "issue":
            getattr(k, m)(*a)
    for m, a in isolate("C-B", "crew-b"):
        getattr(k, m)(*a)
    say("kernel", "crew-a and crew-b both working SEC_2, tested dead and grounded")
    for m, a in finish("C-A", "crew-a"):
        getattr(k, m)(*a)
    say("crew-a", "we're done and released. Reenergize")
    attempt(k, "operator", "close S2", "close_switch", "S2")
    say("kernel", f"violations: {k.violations() or 'none'}")
    r = evaluate()
    print(f"\nEval: {r['mutants']} broken orders. Unchecked, {r['unsafe_without_kernel']} put a crew or ground on a "
          f"live section. With the kernel, {r['unsafe_with_kernel']}. Valid orders refused: {r['valid_refused']}.")


if __name__ == "__main__":
    main()
