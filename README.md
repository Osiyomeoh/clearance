# Clearance

**The Switch room that decides whether anyone may flip the switch.**

Two line crews, one feeder, and an agent that only the system operator can instruct. Of 112 broken switching orders, 11 put a crew or a ground on a live section when nothing checks them. With Clearance, 0. (`python3 -m clearance.evaluate`)

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
| Who may instruct the gate? | **Switch.** `gate` has `addressing: owner`, so only the operator's message is an instruction. Anyone else gets a refusal in the room. An agent can't widen its own policy |
| Is this step safe? | **The kernel**, in order of (m)(3) |

Agents: `gate` (`addressing: owner`) issues clearances and orders switching. `desk` (`addressing: anyone`) logs crew reports.
Channel: one room, `clearance-control`, with the operator, the crews and both agents.

## Run it in Switch
1. Install Switch Console and a signed-in coding agent.
2. Clone this repo. Import `templates/clearance-room.template.yaml` and give it the clone's absolute path. You, the deployer, are the operator.
3. Invite a second account as the crew lead, then try the prompts below.

## Limits
- One small simulated feeder; the eval covers single-step omissions and adjacent swaps only.
- The key separating `gate` from `desk` is a file on one machine, not a sandbox. Production would run `gate` on its own host.
- `desk` takes the crew name from chat when logging `release`.
- No hosted demo: Switch runs locally. Use sample mode and the video.

## Tests
`python3 -m unittest discover -s tests -t .`

Built on [Switch](https://github.com/sandbox-quantum/switch), used as a dependency, with its template format.
