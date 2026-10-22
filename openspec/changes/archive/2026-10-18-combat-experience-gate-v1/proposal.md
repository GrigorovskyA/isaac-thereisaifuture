## Why

The 4096-step live continuation (reports/2026-10-18-training-4096.md) passed
mechanically, but only two of seven completed segments had enemies. After a natural
death/restart, five minute-long segments ran in empty rooms, and the frozen t4096
policy chose down/down on 256/256 decisions. Most collected experience therefore
carried no combat signal. That is not proof of a reward bug or of improved play, and
it must not be "fixed" by longer runs, exploration rewards, forced enemies/resets or
scripted navigation.

## What Changes

- Add an opt-in combat-experience gate (`live --combat-gate`). The learner acts and
  collects training samples only during observed eligible combat.
- Between encounters the gate releases input and enters a bounded operator handoff.
  The operator navigates manually, then confirms readiness with a local, private,
  provenance-bound token (`combat-ready --session-dir ...`).
- Eligibility is management metadata derived from the existing live oracle block.
  It never enters the encoder, policy, recurrent state, normalizer or reward.
- The handoff wait happens inside the environment reset. SB3 auto-reset therefore keeps
  terminal rewards and recurrent episode boundaries while wait frames never become
  rollout samples.
- One absolute run deadline covers the waits. A finite per-handoff operator-wait cap
  stops the run safely; there is no renewal, resume, launch or forced reset.
- Logs report wait exposure, readiness requests/accepts/rejects, combat decisions,
  terminal outcomes and unsaved partial rollout steps.

## Capabilities

### New Capabilities

- `combat-experience-gate`: opt-in operator-gated combat experience for live runs.

### Modified Capabilities

None. Default random/train/eval/observe behavior is unchanged.

## Scope and non-goals

In scope: `combat_gate.py`, minimal opt-in wiring in `live.py`/`cli.py`, offline
tests, operator documentation.

Non-goals: reward or coefficient changes, new Lua/wire API, entity encoding,
checkpoint format or migration, curriculum, automatic navigation, desktop input, game
launch, real training, approval creation, eval-live gating.

## Risks

- Operator latency adds wall time; bounded by the wait cap and run deadline.
- `IsActiveEnemy(false)` may list enemies that cannot be damaged or that never
  clear the room; such rooms behave like combat and end by timeout.
- Eligibility comes from approximate oracle frames; overflow/unknown states are
  conservatively ineligible.
- A global stop mid-rollout loses unsaved partial samples; this is reported, not hidden.

## Dependencies

Existing live loop (`live-training-loop`), `LiveBackend` transport, reward-v1 ledger,
SB3 RecurrentPPO training and checkpoints. No new packages.

## Acceptance

Offline (executor): strict OpenSpec validation; behavioral tests for
the empty start, clear handoff, restart wait, no implicit resume, valid/stale/replayed/
cross-epoch/cross-room/predating/invalid readiness, wait cap, global deadline,
disconnect, fault cleanup, no wait normalization/reward, and a real synthetic
RecurrentPPO update plus checkpoint across several handoffs. Full macOS precheck.

Primary-owned (pending): Windows Check.ps1, and a bounded real-game gated run
on file 2 with recorded handoffs.
