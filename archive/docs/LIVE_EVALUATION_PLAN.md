# Live evaluation plan (predeclared)

Readiness item 4 update (2026-10-21): the bounded offline
[gameplay comparison contract](GAMEPLAY_COMPARISON.md) now defines the frozen
matrix, raw HP/clear metrics, observed-start matching and descriptive paired
report. No matched native suite or raw-log normalization adapter has been accepted.
For that pipeline, its explicit unknown/censoring denominators supersede the
older pilot denominator shorthand below. Existing pilot logs do not acquire
matched or exhaustive terminal coverage retroactively.

Status: plan. OpenSpec changes `frozen-policy-evaluation-v1` (adapter) and
`frozen-live-pilot-v1` (runner). This document grants **no** authority to launch the game,
connect, train, reset, deploy or write approvals. Every run below needs its own runtime approval
under `AGENTS.md`. The attach-only runner `python -m isaac_threrisaifuture.cli eval-live` exists
passed offline checks and one real 256-decision inference smoke pilot. The runner
change is archived as `2026-10-18-frozen-live-pilot-v1`; comparative policy quality
remains untested. See reports/2026-10-18-frozen-live-runtime.md.
Operator steps are in [FROZEN_LIVE_PILOT.md](FROZEN_LIVE_PILOT.md).

## Why two parts

The live backend continues the operator's run on file 2. It has no seeded starts or resets and
cannot force a room, character or build. Equal decision caps therefore do not make two policies
face comparable rooms. Part A is descriptive; Part B is the only comparison that may support a
claim and stays blocked until its preconditions exist.

## Policies and identity

| Policy ID | Source | Identity recorded |
| --- | --- | --- |
| `random` | `baselines.RandomPolicy` | name, label, policy RNG seed |
| `scripted` | `baselines.ScriptedPolicy` (offline only; `eval-live` does not run it) | name, label |
| `checkpoint:<id>` | `CheckpointPolicy(<explicit dir>, expected_config_hash=...)` | `PolicyIdentity.to_dict()` |

For every checkpoint record the full identity (checkpoint id, config hash, training seed,
timesteps, observation/action/reward schema versions, manifest/model/normalizer SHA-256) before
the first decision, and call `verify_unchanged()` after the last. A failed check voids the
policy's results. Never use `latest.txt`; name the directory. The current smoke checkpoint
`runs/live/seed-20/checkpoints/1f4a187e-s20-t256` (256 timesteps) is a pipeline artifact, not an
evaluation candidate or winner, and stays private.

Also record per session: game and observer versions, mod hash, `live_loop_v1` negotiation,
reward coefficient version, action repeat, and the commit of the evaluating code. `eval-live`
logs the identity, schema versions, action repeat (3), every hello and the final summary; the
mod hash and code commit are added by the operator in the evidence report.

## Part A: exploratory pilot (future, descriptive only)

- **Cap:** at most 2000 decisions **or** 6 minutes wall time per policy, whichever comes first.
  Same caps for every policy; this equalizes budget, not difficulty.
- **Order:** one `eval-live` invocation runs exactly one policy. Alternate policies by running
  several short, separately bounded invocations in a predeclared order, so drift in the
  operator's run (floor, build, health) is not confounded with a single policy. Record the order.
  There is no within-session policy switching. A new invocation does not renew the game
  approval or its restart budget, and does not make rooms comparable.
- **Provenance per segment:** the runner records episode id, session, game epoch, frames,
  decisions, reward return and end reason. It cannot observe character, floor, room type or
  build: those are logged as `unknown`. The operator may add observed provenance in the
  evidence report; anything not observed stays `unknown`, never guessed.
- **Stop conditions:** decision cap; absolute deadline; fault budget exhausted (default zero);
  any protocol error; invalid model output; operator stop (Ctrl+C); approval expiry (seen as a
  transport fault or rejection); `verify_unchanged()` failure, which marks the whole result
  `invalid`. The final partial segment is kept with its decisions.
- **Operator intervention:** the runner does **not** detect physical input and cannot record
  per-input timestamps. The operator declares the whole session `--operator-assistance
  assisted|unassisted|unknown` (default `unknown`). Stop the runner before any manual
  navigation, menu, pause or Continue; if input happened during a session, label it `assisted`.
  Only `unassisted` sessions may enter autonomous-performance attribution; `assisted` and
  `unknown` sessions are reported but excluded from it. Navigation between rooms is currently
  operator-assisted, so the pilot measures in-room combat only.
- **Output:** descriptive tables with all segments, including unfavourable ones. No ranking,
  winner or learning claim.

## Part B: confirmatory comparison (blocked)

Blocked until all of these exist and are accepted:

1. Comparable supported scenarios on the real game (controlled starts or a validated way to
   bucket rooms by type and difficulty).
2. Fixed train/validation/test separation for those scenarios; the test split held out.
3. The frozen-policy live runner (`frozen-live-pilot-v1`) accepted with runtime evidence, and a
   runtime approval for the comparison.
4. Several independently trained seeds per configuration.

Then the existing criteria apply unchanged: at least 100 valid episodes per policy on the
validation split, clear-rate improvement of at least +20 percentage points over the baseline
(`training.SelectionRule`), multi-seed reporting, and a single final test-split evaluation.
Matched game seeds are **not** promised; if they cannot be provided, comparisons stay stratified
by recorded provenance.

## Units and denominators

- **Decision:** one `act` call (one action held for `action_repeat` game updates). `eval-live`
  reports **attempted** decisions (steps started) and **completed** decisions (steps that
  returned without a fault) separately.
- **Segment:** decisions from one live episode start to its end (room clear, death, timeout,
  stop or fault).
- **Attempted** = all segments. **Fault** = segments ended by infrastructure faults (transport,
  protocol, stale frames). **Valid** = attempted − fault. **Autonomous valid** = valid segments
  from sessions declared `unassisted`.
- Clear rate uses autonomous valid segments with at least one enemy at start as denominator.
  **Empty rooms** (no enemy at start) are counted and reported separately, never as clears.
- **Partial segments** (cap/approval/operator stop mid-room) are reported as `truncated`; they
  are neither clears nor deaths.

## Metrics

Primary, reported per policy and per provenance stratum:

- room clear rate with Wilson 95% interval (`evaluation.wilson_interval`);
- damage taken (half-hearts) per segment and per 100 decisions;
- deaths and timeouts/truncations as counts and rates;
- decisions, game updates and policy updates (zero for frozen policies);
- infrastructure faults and their kinds, with their own denominator (attempted).

Secondary: episode reward under the recorded coefficient version. Reward never ranks policies
and reward growth is never presented as learning.

## Handling unequal exposure and inconclusive results

- Report exposure (segments, decisions, minutes) beside every rate. Different numbers of
  segments per policy are expected and stated, not padded or trimmed.
- If intervals overlap, or a stratum has fewer than 20 autonomous valid segments, the result is
  `inconclusive` for that stratum.
- Do not drop a policy's worst segments, rerun until favourable, or choose caps after looking.
- Any deviation from this plan is recorded in the evidence report as a deviation, with reason.

## Evidence

Use `reports/EVIDENCE_TEMPLATE.md`. Keep raw logs, oracle files and checkpoint binaries out of
Git. State explicitly which parts were `passed`, `failed`, `not_run` or `blocked`.
