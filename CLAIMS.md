# Claims
| Claim | Status | Reproduce |
|---|---|---|
| 112 broken orders; unchecked 11 reach an unsafe state; with kernel 0; valid refused 0 | Measured, single-step omissions and adjacent swaps only | `python3 -m clearance.evaluate` |
| Close refused while another crew holds a tag | Tested | `tests/test_kernel.py` |
| Generator backfeed refused, path named | Tested | `tests/test_kernel.py` |
| Desk can't run gate commands | Tested, same-machine key file, not a sandbox | `tests/test_cli.py` |
| Switch refuses the crew lead at `gate` | **NOT YET VERIFIED, needs a real room** | Spike |
| Template imports in Switch Console | **NOT YET VERIFIED**; only parsed as YAML | Spike |
| OSHA wording | Read at source | osha.gov 1910.269(m)(3) |
| NERC: 17 sector fatalities Q1 2026 | All causes, not switching-specific | nerc.gov.ng, published Jul 21 2026 |
