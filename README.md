# Clearance

**The Switch room that decides whether anyone may flip the switch.**

Two line crews, one feeder, and an agent that only the system operator can instruct. Of 112 broken switching orders, 11 put a crew or a ground on a live section when nothing checks them. With Clearance, 0. (`python3 -m clearance.evaluate`)

![Crew lead tells the gate agent to issue a clearance in a Mattermost channel; Switch refuses](docs/gallery/1-crew-lead-refused.jpg)

> SIMULATED network. It never connects to or operates real equipment, and doesn't replace a utility's procedures.

## See it in 60 seconds, with no keys
Python 3.10+, no dependencies.
```sh
git clone <this repo> && cd <this repo>
bin/clearance sample
```
You'll see the kernel refuse a clearance because a generator can backfeed the section, then refuse to reenergize because Crew B is still on it.

## Why this exists
A duty system operator runs crews over chat and a paper log. [29 CFR 1910.269(m)(3)(xiii)](https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.269) forbids reenergizing until "all crews working on the lines or equipment release their clearances". Nigeria's regulator [counted 17 sector fatalities in Q1 2026](https://nerc.gov.ng/media/nerc-pushes-for-operation-zero-as-nesi-safety-performance-shows-q1-2026-improvement/), from all causes, not only switching.

## How Switch is used
Two checks, and the project needs both.

| Question | Answered by |
|---|---|
| Who may instruct the gate? | **Switch.** `gate` has an owner-only addressing policy, so only the operator's message is an instruction. Anyone else gets a refusal in the room. An agent can't widen its own policy |
| Is this step safe? | **The kernel**, in order of (m)(3) |

Agents: `gate` (owner only) issues clearances and orders switching. `desk` (anyone) logs crew reports.
Channel: one room with the operator, the crew lead and both agents, in Mattermost through Switch's bridge, or as a Switch chat.

## What happened in a real room
Measured on a local Switch stack. Full transcripts: [Gateway chat](docs/live-run.txt), [Mattermost channel](docs/live-mattermost.txt).

| Attempt | Stopped by | Reply |
|---|---|---|
| Crew lead `@gate issue C-A` | Switch addressing | "You're not permitted to direct messages to me in this room…" |
| Crew lead `@desk issue C-A` | CLI key | `REFUSED: issue is for the gate agent only` |
| Operator `@gate issue C-A`, generator connected | Kernel | `REFUSED: cannot issue C-A: SEC_2 is still live via DG-DG_SW-SEC_2` |
| Operator `@gate close S2`, Crew B still tagged | Kernel | `REFUSED: cannot close S2: tagged under C-B (crew-b)` |
| `gate` tries to widen its own policy | Switch | HTTP 403 "An agent can't change its own settings, permissions or services…" |

In the Gateway run the crew lead is a known user who isn't the owner. In the Mattermost run the crew lead's account isn't linked to a Switch user, so Switch's refusal says that instead. The operator's bridged account is the owner.

![The kernel refuses to issue while a generator can backfeed, then allows it after the fix](docs/gallery/2-generator-refused.jpg)
![The kernel refuses to close S2 while Crew B holds a tag](docs/gallery/3-close-s2-refused.jpg)

## Run it live
Needs Docker and Python 3.10+. This starts Switch's published local stack on ports 8000, 3000 and 8065.
```sh
git clone <this repo> clearance && cd clearance
python3 -m venv .venv && .venv/bin/pip install -r live/requirements.txt

mkdir -p .stack
R=https://raw.githubusercontent.com/sandbox-quantum/switch/main
curl -fsSL $R/deploy/local/standalone-docker-compose.yml -o .stack/compose.yml
curl -fsSL $R/deploy/local/generate-env-secrets.sh -o .stack/generate-env-secrets.sh
curl -fsSL $R/.env.example -o .stack/.env
bash .stack/generate-env-secrets.sh .stack/.env local && chmod 600 .stack/.env
docker compose -f .stack/compose.yml --env-file .stack/.env -p clearance --profile collab --profile gateway up -d

set -a; . .stack/.env; set +a
.venv/bin/python -m live.run_mattermost
```
Then open http://localhost:8065, sign in with `MATTERMOST_USER` from `.stack/.env`, and read the channel. `PACE=4` slows it for watching. For the Gateway chat version, `SWITCH_EMAIL=$GATEWAY_ADMIN_EMAIL SWITCH_PASSWORD=$GATEWAY_ADMIN_PASSWORD .venv/bin/python live/run_room.py`. The script creates its own local users. No model key is needed.

The agents in these runs are deterministic: [`live/room_agent.py`](live/room_agent.py) implements Switch's agent protocol, and runs the words after the mention as a `bin/clearance` command, with no LLM. That makes the refusals repeatable.

## Run it with coding agents
[`templates/clearance-room.template.yaml`](templates/clearance-room.template.yaml) defines the same room with Claude, Codex or OpenCode as the agents. Switch's validator accepts it with 0 errors and 0 warnings, and it can be saved to the Gateway.
1. Install Switch Console and a signed-in coding agent.
2. Import the template and give it the clone's absolute path. You, the deployer, are the operator.
3. Invite a second account as the crew lead, then have them try `@clearance-gate issue C-A`.

## Limits
- One small simulated feeder; the eval covers single-step omissions and adjacent swaps only.
- The key separating `gate` from `desk` is a file on one machine, not a sandbox. Production would run `gate` on its own host.
- `desk` takes the crew name from chat when logging `release`.
- No hosted demo: Switch runs locally. Use sample mode and the video.

## Tests
`python3 -m unittest discover -s tests -t .`

Built on [Switch](https://github.com/sandbox-quantum/switch), used as a dependency, with its template format.
