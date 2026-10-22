# Design

## Principles

Rewards describe outcomes, never technique. Observations carry facts, never
advice. Exploration comes from an intrinsic bonus, not scripts. Every reward
term has an exploit test. Training reward is not evidence of better play.

## Observation schema 3

The Lua `entity_frame` keeps its existing fields and sets
`observation_schema_version=3`. New fields:

- Pickup entities gain `variant`, `subtype` (integers) and `price` (integer;
  0 = free, non-zero = shop or devil deal). Other kinds send `null` for all three.
  The pickup cap rises from 4 to 8.
- `inventory`: `coins`, `bombs`, `keys` (0..999), `active_item` (collectible ID,
  0 = none), `active_charge`, `active_max_charge` (0..24), `card`, `pill`,
  `trinket` (raw IDs, 0 = none).
- `collectibles`: sorted unique list of held collectible IDs in 1..1024, at most
  256 entries (excess counted in `collectible_overflow`). Lua recomputes it on
  game start, room change and every 30 frames, never every snapshot.
- `room`: `type` (RoomType 0..31), `stage` (0..15), `stage_type` (0..7),
  `clear` (bool), `doors` (8 booleans, open door per slot).

The oracle block gains `room_index` (level room index) for reward and novelty
keys only; it never enters the policy vector.

Encoding (`encoding.py`, size `OBSERVATION_SIZE_V3`):

| Block | Features |
| --- | --- |
| Player | 9 existing (position, velocity, health) |
| Inventory | coins/99, bombs/99, keys/99 (clipped), active present, active ID/1024, charge fraction, card present, pill present, trinket present = 9 |
| Room | type one-hot 32, stage/15, stage_type/7, clear, 8 doors = 43 |
| Enemy/projectile/obstacle slots | unchanged 8 features, capacities 16/32/24 |
| Pickup slots | 8 base + variant class one-hot 12 + subtype/1024 + shop flag = 22, capacity 8 |
| Collectibles | multi-hot 1024 |

Variant classes: heart (10), coin (20), key (30), bomb (40, 41), chest (50-60,
340, 360, 390), sack (69), pill (70), battery (90), collectible (100), card (300),
trinket (350), other. Total size: 9+9+43+128+256+192+176+1024 = 1837.

## Actions v2

`Command` gains `use`: `none | bomb | active | pillcard`, placed after `shoot` in
the canonical field order. `kind="action"` may carry any `use`; heartbeat,
release and restart require `use="none"`. The environment action space is
`MultiDiscrete([5, 5, 4])`.

Lua stores `hold.use` and `hold.use_pending=true` on accept. In
`MC_INPUT_ACTION`, for the player entity and the mapped button
(`ACTION_BOMB`, `ACTION_ITEM`, `ACTION_PILLCARD`):
`IS_ACTION_TRIGGERED` returns true once and clears `use_pending`;
`IS_ACTION_PRESSED` returns true while the hold is live; release clears both.

## Restart command and watchdog

New command `kind="restart"` (move/shoot/use `none`, frames 0). Lua accepts it only
with live training authority, pacing (`live_restart_interval_ms`) and remaining
budget; it calls the existing restart dispatch path without requiring a dead
player, bumps the epoch on game start and acknowledges `accepted` or `rejected`.

`StallWatchdog` (Python, in the live loop) tracks wall time since the last
progress event: `enemy_damaged`, `room_entered`, `room_cleared`, `pickup_gained`,
`floor_entered`. Paused or unavailable time does not count. After 90 s it ends
the step with truncation reason `stall` and sends `restart`. No snapshots for the
transport timeout is an infrastructure fault, never a stall.

Approval `max_restarts`: 1..5000 as before, or 0 meaning unlimited (pure profile
only). The consecutive-fault cap (default 5) and disk cap still stop the session.

## Reward v2 (`configs/reward-v2.yaml`)

| Term | Default | Rule |
| --- | --- | --- |
| enemy_hp_fraction_total | 2.0 | per complete enemy HP, monotonic per enemy per epoch (existing deriver) |
| room_clear_first | 3.0 | first clear of a room index per run |
| room_first_visit | 1.0 | first entry of a room index per run |
| floor_first_entered | 10.0 | first entry of a new stage per run (not the start floor) |
| player_damage_half_heart | -2.0 | red+soul decrease |
| death | -10.0 | terminal |
| time_second | -0.005 | active game time |
| coin / bomb / key | 0.05 / 0.1 / 0.1 | per unit increase; shared per-run cap 3.0 |
| collectible_new | 1.0 | per collectible ID first held in this run |
| heal_half_heart | 0.5 | only up to half-hearts lost earlier in this run |
| novelty | 0.02 | 1/sqrt(n) per (room index, 40-unit player cell) per run, separate ledger column |

Counter decreases (spending, dropping) earn nothing and do not reset caps or
"first" sets. Ledgers reset only at a new run (epoch). No reward for using items.
Old kill reward is dropped (no reliable kill channel).

## Episodes

One episode is one run. Death terminates. Stall truncates. Room clear and room
change do not end the episode. The 60 s segment cap is removed; the deadline,
pause limit and fault handling stay.

## Continuous training

`configs/training-pure-v1.yaml` has two sections:

- `contract`: seed, algorithm, lstm_hidden_size, action_repeat_game_updates,
  observation/action/reward versions. Its hash is the lineage `config_hash`.
- `hyperparameters`: learning_rate, ent_coef, clip_range, n_epochs, batch_size,
  gamma, gae_lambda, n_steps. They may change between sessions; on resume they
  are applied to the loaded model and recorded in each checkpoint manifest.

Resume always loads `latest`; a missing or incompatible contract stops. Retention
keeps the 5 newest checkpoints plus every 50th rollout; deletion never touches
`latest` or its parent. Each finished episode appends a row to
`metrics/episodes.csv` (return, damage, rooms visited/cleared, floor reached,
pickups, deaths, truncation reason, timesteps).

`session_runner --forever` runs bounded sessions back to back (each within the
8 h Lua lease), resuming `latest`, until a stop file, Ctrl+C, disk cap or the
consecutive-fault cap.

## Compatibility

New lineage `pure-v1` from a fresh model. Schema 1/2 checkpoints are refused, not
migrated. The old command shape (without `use`) is rejected by the new Lua mod.
