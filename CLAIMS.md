# Claims
| Claim | Status | Reproduce |
|---|---|---|
| 112 broken orders; unchecked 11 reach an unsafe state; with kernel 0; valid refused 0 | Measured, single-step omissions and adjacent swaps only | `python3 -m clearance.evaluate` |
| Close refused while another crew holds a tag | Tested, and seen in a real room | `tests/test_kernel.py`, `docs/live-mattermost.txt` |
| Generator backfeed refused, path named | Tested, and seen in a real room | `tests/test_kernel.py`, `docs/live-mattermost.txt` |
| Desk can't run gate commands | Tested, same-machine key file, not a sandbox | `tests/test_cli.py`, `docs/live-run.txt` |
| Switch refuses a known non-owner at `gate` | Measured on a local stack, `switch-core:latest`, Nov 7 2026 | `live/run_room.py`, `docs/live-run.txt` |
| Switch refuses an unlinked Mattermost account at `gate` | Measured, same stack. Different wording from the row above | `live/run_mattermost.py`, `docs/live-mattermost.txt` |
| Agent can't widen its own addressing policy | Measured, HTTP 403 | `live/run_room.py` |
| Template valid | `POST /gateway/templates/validate`: ok, 0 errors, 0 warnings; `POST /gateway/templates`: 201 | Same stack |
| Template deploys LLM agents through Console | **NOT VERIFIED** | Needs Console and a signed-in coding agent |
| OSHA wording | Read at source | osha.gov 1910.269(m)(3) |
| NERC: 17 sector fatalities Q1 2026 | All causes, not switching-specific | nerc.gov.ng, published Jul 21 2026 |
