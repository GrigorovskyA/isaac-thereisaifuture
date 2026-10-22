# Frozen live pilot runner (`eval-live`)

Status: accepted and archived as `2026-10-18-frozen-live-pilot-v1`, after offline
checks and a real 256-decision frozen-checkpoint pilot with unchanged artifacts,
zero faults and operator-confirmed release. See
[runtime evidence](../reports/2026-10-18-frozen-live-runtime.md). This guide grants no
authority to run one: a pilot needs its own runtime approval under `AGENTS.md` and follows
[LIVE_EVALUATION_PLAN.md](LIVE_EVALUATION_PLAN.md) Part A. Results are descriptive; they never
rank policies or show learning.

## What it does and does not do

- Runs exactly one policy per invocation: `--policy checkpoint` (a frozen RecurrentPPO
  checkpoint through `CheckpointPolicy`) or `--policy random` (`RandomPolicy`).
- Attaches to an already running game on file 2 through the existing live loop
  (`LiveClient`, `make_live_env`, `live_loop_v1`). The Lua live-loop approval is still required;
  this runner does not write, renew or bypass it.
- Never launches the game, trains, saves, resumes, follows `latest.txt`, forces a restart or
  recovers unattended. Natural death restarts stay under the existing Lua approval and its
  per-launch restart budget.

## Before the session

1. A valid, unexpired live-loop approval exists for this game launch (written separately by an
   authorized operator; see [LIVE_LOOP.md](LIVE_LOOP.md)). Expired approvals make the game side
   refuse the live loop; the runner then fails with a fault or timeout.
2. Isaac runs with `--luadebug`; the operator selected **file 2** and started or continued a
   run, and the character stands in a room. Navigation between rooms is manual.
3. For a checkpoint: name the exact checkpoint directory and its config hash. Optionally pin
   the training seed. Never use the moving `latest.txt` pointer.

## Run

```powershell
# Frozen checkpoint (defaults: 2000 decisions, 6 minutes, zero tolerated faults)
.venv\Scripts\python.exe -m isaac_threrisaifuture.cli eval-live --policy checkpoint `
  --checkpoint runs\live\seed-20\checkpoints\<checkpoint-id> `
  --expected-config-hash <sha256> --expected-training-seed 20 `
  --operator-assistance unassisted --confirmed-save-slot 2

# Random baseline with a recorded policy RNG seed
.venv\Scripts\python.exe -m isaac_threrisaifuture.cli eval-live --policy random `
  --policy-seed 1 --operator-assistance unassisted --confirmed-save-slot 2
```

Options: `--steps` (decision cap, 1..100000), `--minutes` (absolute wall-time cap, up to the
8-hour approval cap), `--accept-timeout` (also capped by the deadline), `--max-faults` (default
0), `--policy-seed`, `--out-dir` (default `runs/eval-live`). Invalid or non-finite budgets and
incompatible or unreadable checkpoints are rejected (exit 2) **before** the port is opened.

One deadline, fixed before listening, bounds waiting for the game, the first reset, paused waits,
steps and reconnects after death. In-flight I/O can overrun it by at most the existing
`LiveBackend` bounds (1 s acknowledgement, 5 s step wait). No action is sent after the cap or the
deadline.

## Operator intervention

The runner cannot detect physical input or record when it happened. Declare the whole session:

- `unassisted`: you will not touch the game while the runner is active.
- `assisted`: you navigated, paused, used menus or pressed Continue during the session.
- `unknown` (default): not declared.

**Stop before manual input.** Press Ctrl+C before any navigation, pause, menu or Continue:
input is released and the game keeps running. Then start a new bounded invocation. If you had
to touch the game while the runner was active, label the session `assisted` in the evidence
report even if it was started as `unassisted`. Only `unassisted` sessions count toward
autonomous-performance attribution.

Switching policy means a new invocation. It does not renew the game approval, its restart budget
or the evaluation budget, and does not make rooms comparable.

## Outcome and exit codes

| Status | Stop reasons | Exit |
| --- | --- | --- |
| `completed` | `step_cap`, `deadline` (no faults) | 0 |
| `interrupted` | `operator_interrupt` (Ctrl+C) | 0 |
| `failed` | any recorded fault (even tolerated), `fault`, `protocol_error`, `policy_error`, `connection_timeout`, `error` | 1 |
| `invalid` | checkpoint files changed after loading (checked again at exit) | 3 |
| not started | invalid options or incompatible checkpoint | 2 |

## Logs (private, never in Git)

`runs/eval-live/sessions/<stamp>/live.jsonl` contains:

- `configuration`: policy kind and identity (hashes), seeds, budgets, assistance label, schema
  versions, action repeat; initial room and character build are `unknown`;
- `listening`, then `hello` for every connection, including reconnects after death;
- `segment_start` and `segment` with episode id, session, epoch, frames, completed decisions,
  reward return and end (`cleared`, `death`, `timeout`, `fault`, or `stopped` for the final
  partial segment);
- `episode` and `fault` records from the shared live wrapper;
- `summary`, written on every exit path: status, stop reason, attempted and completed
  decisions, faults, segments, identity validity.

`oracle.jsonl` holds approximate oracle events, kept apart from policy inputs and from
`live.jsonl`.

## Evidence

Record the run with `reports/EVIDENCE_TEMPLATE.md`: game/mod versions, mod hash, code commit,
approval expiry, command, timestamps, the summary line and any observed provenance. Report all
sessions, including failed and interrupted ones.
