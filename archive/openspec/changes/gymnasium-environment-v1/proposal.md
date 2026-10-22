## Why

Roadmap item 06: RL libraries need a Gymnasium environment with correct `reset`/`step`/`close`
semantics, fixed spaces and an explicit split between termination, truncation and faults. It
is built on the episode controller so that a real bridge backend can replace the toy simulator.

## What Changes

- Add `env.py`: `IsaacCombatEnv` with `Box` observations from the encoder and
  `MultiDiscrete([5, 5])` actions (independent move and shoot: none/left/right/up/down).
- Add an optional reward accountant seam and a separate `oracle_sink` channel.
- Add offline tests using the toy simulator and the SB3 environment checker.

## Scope and non-goals

- In scope: the adapter, action repeat, reset seeding semantics, info fields, offline tests.
- Out of scope: reward rules (item 07), training (item 08), real bridge backend, CLI for real games.
- Deviation from RL_DESIGN draft: the action space is 5x5 (cardinal), matching the verified
  safe-action protocol, not the proposed 9x5 with diagonals.

## Dependencies and risks

- Depends on observation-and-event-contract-v1 and episode-lifecycle.
- Unknown: real steps/sec, latency and fault rate; none are claimed. Game seed control is
  reported per backend through `game_seed_supported`.

## Acceptance criteria

- Offline: the SB3 environment checker passes; equal reset seeds reproduce the first observation
  on the toy backend; invalid actions raise; 10,000 toy steps never accept a stale or repeated frame.
- Offline: a transport fault raises out of `step` and is never returned as a transition.
- Pending real game: the same checks and 10,000 steps on an authorized profile, plus measured
  steps/sec, p50/p95 latency, reset time, fault rate and memory.

## Impact

New module `env.py`; depends on gymnasium/numpy (already pinned).
