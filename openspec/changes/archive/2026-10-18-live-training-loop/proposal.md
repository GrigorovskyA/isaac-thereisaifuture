## Why

The project has accepted real observation, entity export and bounded native actions,
but no path from those pieces to a running learning loop. The remaining work on exact
engine-step semantics (episode-lifecycle 3.x) does not shorten the time to a first
live run. On 2026-10-18 the user decided to launch as early as possible with a
pragmatic loop and recorded three explicit decisions:

1. **Approximate reward labels**: derive oracle events from frame deltas of a separate
   oracle block instead of waiting for an exact engine event oracle.
2. **Autonomous death restart**: the mod restarts after death inside a bounded training
   approval, so episodes continue without operator input.
3. **Training on save file 2 is accepted** by the operator, including the risk that
   training runs affect progression on that file.

These decisions supersede, for this change only, the earlier rules that entity
observation, actions and death restart are mutually exclusive, that action approval is
bound to one game epoch, and that death restart is limited to 3 attempts / 10 minutes.

## What Changes

- Lua observer 0.5.0-dev: new capability `live_loop_v1` that combines
  `entity_observation_v1`, `safe_actions_v1` and `death_restart_v1` in one session.
- New approval profile mode `training`: not epoch-bound, expiry at most 8 hours,
  explicit `max_restarts` (1..5000); the lease equals the approval expiry.
- Separate `oracle` block in live snapshots (room clear, player dead, enemy HP per
  entity ID, overflow count). It never enters the policy-visible `entity_frame`.
- Live-mode command handling: stale or unavailable-state commands receive a
  `rejected` acknowledgement instead of closing the session; a missed heartbeat
  releases input instead of closing; restarts keep the training approval.
- Python `live.py`: wire models, `LiveClient` with a reader thread, `EventDeriver`,
  `LiveBackend` (a `GameBackend`), `FaultTolerantEnv`, approval writer.
- CLI `approve-training` and `live` (random policy or PPO training with budgets),
  `configs/training-live-v1.yaml`, `Start-Live.cmd`.

## Scope and non-goals

- In scope: protocol, Lua mode, Python backend, CLI, offline tests (lupa Lua harness,
  real-socket end-to-end with simulated game), documentation, Windows check list.
- Non-goals: exact engine events, exploration/new-room reward (reward-v2), pausing
  the game during PPO updates, automatic file-2 selection, achievement eligibility,
  unattended supervisor or automatic game relaunch.

## Dependencies

- Accepted: game-observation, native-player-actions, post-death-restart, entity export,
  episode-lifecycle controller (`EpisodeController`, `GameBackend`).
- Unknown game APIs needing real evidence: `Entity.HitPoints`/`MaxHitPoints` values,
  `Room:IsClear()` timing, `EntityPlayer:IsDead()` during the death animation, whether
  frequent `restart` commands are stable.

## Acceptance criteria

- Offline: `scripts/check.sh` (macOS) and `./scripts/Check.ps1` (Windows) pass; the
  OpenSpec change validates strictly.
- Offline end-to-end: real `main.lua` in lupa and real `LiveClient` over loopback
  complete episodes including a death, an autonomous restart and a reconnect.
- Windows/game: after closed-game deployment and `approve-training`, a random-policy
  `live` run of at least 2000 steps records episodes with movement, enemy damage
  events and at least one death followed by an autonomous restart, with zero
  protocol errors. Then a short budgeted `live --mode train` run saves a checkpoint.
