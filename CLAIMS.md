# Claims
| Claim | Status | Reproduce |
|---|---|---|
| 112 broken orders; unchecked 11 reach an unsafe state; with kernel 0; valid refused 0 | Measured, single-step omissions and adjacent swaps only | `python3 -m clearance.evaluate` |
| 20,856 stress cases (all pairs of omissions, plus 20,000 seeded hostile orders): 11,140 unsafe unchecked, 0 with kernel | Measured, seed 269, simulated feeder | `python3 -m clearance.evaluate` |
| 40 hostile messages at Claude agents, 0 breaches | Measured once, state-based, direct call and not through a room, model alias `sonnet` | `python3 live/redteam.py`, `docs/redteam.txt` |
| `bin/demo` works on a clean stack | Run once on macOS, about 93 s, images already cached | `bin/demo` |
| Close refused while another crew holds a tag | Tested, and seen in a real room | `tests/test_kernel.py`, `docs/live-mattermost.txt` |
| Generator backfeed refused, path named | Tested, and seen in a real room | `tests/test_kernel.py`, `docs/live-mattermost.txt` |
| Desk can't run gate commands | Tested, same-machine key file, not a sandbox | `tests/test_cli.py`, `docs/live-run.txt` |
| Switch refuses a known non-owner at `gate` | Measured on a local stack, `switch-core:latest`, Nov 7 2026 | `live/run_room.py`, `docs/live-run.txt` |
| Switch refuses an unlinked Mattermost account at `gate` | Measured, same stack. Different wording from the row above | `live/run_mattermost.py`, `docs/live-mattermost.txt` |
| Agent can't widen its own addressing policy | Measured, HTTP 403 | `live/run_room.py` |
| Template valid | `POST /gateway/templates/validate`: ok, 0 errors, 0 warnings; `POST /gateway/templates`: 201 | Same stack |
| Template deploys LLM agents through Console | **NOT VERIFIED** | Needs Console and a signed-in coding agent |
| Claude agents complete the scenario in a real room, with Switch and kernel refusals | Measured, one Mattermost run and one Gateway run, Claude Code CLI, model alias `sonnet`, template instructions, not Console | `BRAIN=1 python -m live.run_mattermost`, `docs/live-llm-mattermost.txt`, `docs/live-llm.txt` |
| Board shows the run live and read-only | Measured, one Mattermost AI run: state polled each second, showed the DG_SW refusal and the final S2 refusal. GET only; POST returns 501 | `live/board.py`, `BRAIN=1 python -m live.run_mattermost` |
| Agent refused prompt injection and "force it" | Observed in those runs; LLM behaviour, not a guarantee | Same |
| OSHA wording | Read at source | osha.gov 1910.269(m)(3) |
| NERC: 17 sector fatalities Q1 2026 | All causes, not switching-specific | nerc.gov.ng, published Jul 21 2026 |
