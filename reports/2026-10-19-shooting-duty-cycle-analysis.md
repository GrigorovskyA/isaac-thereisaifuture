# Evidence: offline shooting duty-cycle analysis

- Date: 2026-10-19, Europe/Amsterdam. Revision 0a8d9a2.
- Scope: read-only analysis of the previous authorized v2 capture and production
  source; no new game connection, launch, approval, training or implementation.
- Source capture: private runs/live/sessions/20261019-103521-9b419f,
  native-log-private.txt and live.jsonl. English aggregate report only in Git.
- Context: observer 0.5.0-dev, seed 20, action repeat 3, t4352 -> t4864;
  exact configuration and runtime budgets in the v2 report.

## Results

| Check | Method | Exit code | Status | Evidence |
|---|---|---|---|---|
| Parse/pair actions | Session + sequence keyed accepted/release log records | 0 | passed | All 512 commands have one corresponding logged release |
| Policy choice | Accepted shoot direction counts | 0 | passed | none=117, left=95, right=105, up=108, down=87 |
| Command hold | Native release minus acceptance | 0 | passed | Median 83 ms/3 game frames; p95 99 ms; max 100 ms |
| Between-command gap | Next acceptance minus previous release, same combat segment | 0 | passed | 509 gaps; median 17 ms, p95 51 ms, max 902 ms |
| Cross-check | Gate accounting vs native counts | 0 | passed | 512 decisions/actions/releases, 127 tear log entries |
| Actual weapon cooldown / maximum firing loss | Requires FireDelay and input/tear correlation | N/A | not_run | Current capture does not contain these fields |

Analysis paired both exact sessions from the v2 report. The 40795 ms gap between
segments 1 and 2 is a manual handoff and was excluded. Reconnect between epochs
is excluded rather than bridged across session clocks. The remaining 509 gaps
are within the three known combat segments (93 + 13 + 406 commands).
Raw computed aggregates are private in shooting-analysis-private.json.

## Findings

1. Policy-selected silence: 117/512 commands (22.85%) choose shoot=none.
   Of adjacent non-none shooting commands, 229 switch direction. These choices
   can interrupt sustained aiming, but are not evidence of a broken input hook.
2. Transport/action scheduling: all but one release is expiry (511); the other
   is transition. Lua releases at the 3-game-frame bound or safety deadline;
   Python waits for the matching frame target before choosing/sending again.
   Median logged release-to-next-acceptance time is 17 ms. Of 509 gaps, 86 span
   positive Game:GetFrameCount differences; median is zero, p95 one frame.
   A zero frame difference is not proof of uninterrupted input callbacks; native
   clock/frame logging has finite resolution and callback phase matters.
3. Learner-boundary stall: epoch 2 sequence 150 releases at time_ms 70295142,
   frame 826. Sequence 151 accepts at 70296044, frame 853: 902 ms / 27 frames.
   The preceding 106 epoch-1 commands plus these 150 commands equal the first
   256-sample rollout. training.py synchronously calls model.learn and saves a
   checkpoint between chunks before collecting again. The position at that
   boundary is consistent with learner/update/checkpoint work; its exact 902 ms
   attribution among optimizer, saving and scheduling is not separately timed.
   This specific preceding command had shoot=none. It still demonstrates loss
   of action coverage during online learning, not a measured missed tear.
4. Logging is not shot suppression: the h.tears >= 4 branch only stops additional
   MC_POST_FIRE_TEAR evidence logging for one held command. It neither blocks
   native firing nor caps a weapon at four tears. The input callback returns
   pressed/value for held directions; it does not call FireTear or write stats.
5. MaxFireDelay/FireDelay are not modified by this production bridge. This capture
   does not record their values. Therefore 127 logged tears cannot determine
   whether the character reached the natural maximum rate or how many shots were
   lost. Do not call the 22.85% command fraction an equivalent fire-rate reduction.

## Source review

Reviewed mod/observer/main.lua action_guard, action command acceptance,
MC_INPUT_ACTION and MC_POST_FIRE_TEAR; src/isaac_threrisaifuture/live.py
LiveBackend.step; src/isaac_threrisaifuture/training.py train chunk/update/save.
Existing expiry, heartbeat, transition and disconnect release are intentional
safety contracts. Removing expiry or extending the last command across learning
would change behavior and authority; this analysis does not authorize that fix.
The installed character's stats remain untouched.

## Limitations and next bounded design

The user's observation is plausible and has two observed contributors: policy
silence and real command gaps. No quantified maximum-fire-rate defect is proven.
Before changing action scheduling, create a small OpenSpec change for opt-in,
bounded firing diagnostics: read-only FireDelay/MaxFireDelay plus frame and input
phase correlation, aggregated rates with logging limits, no new policy inputs,
no stats/reward changes, default diagnostics off. Offline tests should cover
missing fields, bounds and expiry/disconnect cleanup.

Then separately authorize a short neutral/fixed-direction native hold comparison
in a safe room versus frozen-policy input, under existing finite action limits.
An empty room is appropriate for firing cadence; enemy damage would confound
this diagnostic. Frozen inference avoids the online PPO update stall. Any real
check requires current slot/instance/readiness and its own finite budget.
No automatic readiness, approval, runtime test or subagent assignment follows.

Self-review: all results are tied to retained real capture; no synthetic shot
rate, no private log/model publication and no character-stat edit. No source
change, hence no redundant full Check.ps1 rerun; the unchanged implementation's
1451-pass Windows result remains prior evidence, not a new test result.

Validation: pinned scripts/OpenSpec.ps1 validate --all --strict exited 0 (30/30); git diff --check exited 0. No OpenSpec archive.
