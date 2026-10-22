## Why

The hinted direction (scripted setup, combat gate, geometry features and firing
shaping) did not improve native play: v4/v5 pilots spent 97%+ of decisions at a
corner or wall, and the offline wall-stagnation diagnosis found an inherited
directional prior plus near-flat shaping rather than a pipeline defect. The user
decided on 2026-10-22 to switch to pure self-learning: one RecurrentPPO model,
trained from scratch and continuously, on raw facts and outcome rewards only
(`docs/UPDATE_DECISION.md`).

## What Changes

- Hint, diagnostic, native-episode and roadmap modules, tests, configs, docs and
  all open OpenSpec changes move to `archive/` (history only, not imported).
- The Lua observer drops trace, probe, tear/target-phase, firing, boundary and
  policy-geometry features.
- Observation schema 3: raw entities plus pickup variant/subtype/price,
  inventory (coins, bombs, keys, active item and charge, card/pill/trinket held),
  room facts (type, stage, clear flag, open doors) and a multi-hot of held
  collectibles. Facts only, no advice features.
- Action v2: `MultiDiscrete([5, 5, 4])`; the third head is none, bomb, active
  item or pill/card, injected as a one-shot press.
- Reward v2: outcome terms only (enemy damage, first room clear, first room visit,
  first floor entry, health lost, death, time), pickup terms bounded against
  farming and cycling, heal capped by health lost, and a small episodic
  count-based novelty bonus.
- An episode is one run: death terminates it; the stall watchdog truncates it.
- Continuous training of one lineage: contract fields bind the lineage, tunable
  hyperparameters may change between sessions, weights/Adam/normalizer/RNG always
  resume from `latest`; checkpoint retention bounds disk use.
- Stall watchdog: 90 s without progress sends a new `restart` command (New Run).
  Death restarts are unlimited for the pure profile; consecutive infrastructure
  faults and disk stop the session.
- A forever supervisor runs back-to-back bounded sessions until a stop file,
  Ctrl+C, disk cap or fault cap.

## Capabilities

### New Capabilities

- `pure-observation`: observation schema 3 facts and encoding.
- `pure-actions`: use-item action head and restart command.
- `pure-reward`: outcome reward v2, exploit bounds and novelty.
- `continuous-training`: one lineage, tunable hyperparameters, retention, supervisor.
- `stall-watchdog`: stall detection, truncation and restart.

### Modified Capabilities

- `post-death-restart`: unlimited restarts for the pure training approval.
- `native-player-actions`: firing diagnostic requirements removed.

## Non-goals

- Scripted positioning, action masks, imitation, curriculum or reward terms that
  describe technique.
- Paired causal evaluation or claims of improved play from training reward.
- Save/Cloud edits, unlocks or third-party mods.
- Migrating old 649/723-input checkpoints; they stay preserved under `runs/`.

## Impact

Python package, Lua observer, tests, configs, docs and runtime authority. Old
checkpoint lineages are incompatible and untouched. Native Lua APIs used for new
facts and one-shot presses (`GetNumCoins`, `GetActiveItem`, `GetActiveCharge`,
`HasCollectible`, `Price`, `IS_ACTION_TRIGGERED` for `ACTION_BOMB`/`ACTION_ITEM`/
`ACTION_PILLCARD`, `ExecuteCommand("restart")` while alive) are unverified in the
real game until the Windows acceptance tasks run.

Acceptance: offline gate green with Lua suites; synthetic and Lua-socket training
across death and watchdog restart; checkpoint resume with a hyperparameter change
keeps the lineage; exploit tests pass. Native acceptance needs one bounded Windows
session showing schema 3 frames, an accepted use-item press, a stall restart, a
death restart, and a reloadable checkpoint.
