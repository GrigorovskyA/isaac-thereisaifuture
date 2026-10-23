## Why

The pure-v4 one-hour test (`reports/2026-10-23-pure-v4-one-hour.md`) found that a
one-shot kill pays nothing. Enemy damage reward comes from HP drops between two
snapshots. An enemy that dies between snapshots just leaves the oracle list, and the
event deriver treats a missing enemy as unknown, not dead (`live.py`). Episodes 2 and 5
killed 2 and 5 enemies and cleared the room with zero damage reward; 4 of 16 episodes
with kills had none. The stall watchdog misses these kills as well, because enemy
damage is its progress signal. Basement enemies often die in one or two tears, so this
hides the main learning signal.

## What Changes

- Lua observer: the existing `MC_POST_NPC_DEATH` callback also records the identity of
  each killed enemy that the observer has seen this room visit. The oracle gets
  `killed`: the last up to 16 such identities this game epoch, oldest first.
- Event deriver: when an identity in `killed` is no longer listed and still has HP
  credit left, it emits `enemy_damaged` for that remaining HP once and sets the credit
  to zero. So a kill pays at most the enemy's max HP, the same as damaging it to zero.
- Reward v6 (`configs/reward-v6.yaml`): the reward v5 coefficients, unchanged; the
  version marks the new event semantics. `configs/training-pure-v4.yaml` contract
  `reward_version: 6`, reward contract `pure-v6`. Reward v5 config moves to
  `archive/configs/`.
- Lineage `pure-v4` starts again with `--initialize`; the 18k-step trial directory is
  kept as `runs/pure-v4-pre` (done on Windows).

## Non-goals

- No change to reward coefficients, the observation (schema 5), actions or the policy.
- `killed` is oracle data only; it never enters the encoder, policy or normalizer.
- No credit for enemies the observer never listed (no baseline, nothing to pay).

## Impact

- `mod/observer/main.lua`, `src/isaac_threrisaifuture/{live_wire,live,rewards,training,checkpoints}.py`,
  configs, tests, docs. Requires a closed-game redeploy of the observer.
