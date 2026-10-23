# Design

## Observation schema 5

`OBSERVATION_SCHEMA_VERSION = 5`; `EntityFrame.observation_schema_version: Literal[5]`.

### Obstacles

- `Entity.obstacle_class`: one of `rock, marked_rock, bomb_rock, block, pit, spikes,
  poop, tnt, fire, wall, other`, required for `obstacle` entities and forbidden on
  other kinds. Lua maps by enum name (no numeric assumptions):
  ROCK, ROCK_ALT, ROCK_ALT2, ROCK_SPIKED, ROCK_GOLD -> rock; ROCKT, ROCK_SS ->
  marked_rock; ROCK_BOMB -> bomb_rock; ROCKB -> block; PIT -> pit; SPIKES,
  SPIKES_ONOFF -> spikes; POOP -> poop; TNT -> tnt. Names missing from
  `GridEntityType` are skipped. Grid cells on the room's outer border
  (`room:GetGridWidth()`/`GetGridHeight()`) are not exported, and neither is any
  WALL cell: narrow and L-shaped rooms have side walls inside that ring (found natively
  in shape 3). The `wall` class stays in the one-hot, unused, so the layout is unchanged.
- Fireplaces (`EntityType.ENTITY_FIREPLACE`, alive and visible) become `obstacle`
  entities with class `fire` and their HP fraction.
- Lua obstacle cap 12 -> 24; `MAX_ENTITIES` 72 -> 84.
- Encoder: obstacle slot width `SLOT_FEATURES + 11` (class one-hot).

### Room shape

`RoomFacts.shape` (1..12, `room:GetRoomShape()`), encoded as a 12-way one-hot after
the existing room features.

### Minimap

`EntityFrame.map`: up to 64 entries `{grid_index 0..168, shape 1..12, visited, current,
room_type 0..31 | null}` from `level:GetRooms()`. An entry is exported only when the
room is visited or its `DisplayFlags` is non-zero; `room_type` only when visited or the
icon bit (4) is set. `EntityFrame.map_current_off_grid` is true when the current room's
grid index is negative (devil, angel, error rooms...). Python validates unique grid
indexes and at most one current entry.

Encoder block (13 x 13 cells x 7 channels + 1): for each entry its shape's cells
(anchor plus offsets: 1x1/IH/IV {0}; 1x2/IIV {0,13}; 2x1/IIH {0,1}; 2x2 {0,1,13,14};
LTL {1,13,14}; LTR {0,13,14}; LBL {0,1,14}; LBR {0,1,13}; cells off the 13-wide
grid are dropped) get known=1, visited, current; room type 5 -> boss, 4 -> treasure,
2 -> shop, other types except 1 -> other special. Then the off-grid flag.

The current room's map position is exposed deliberately: the in-game minimap shows
it. The oracle `room_index` stays out of the vector.

### Stall clock

`encode(frame, *, stall_fraction=0.0)` writes `min(stall_fraction, 1)` into the last
element. `IsaacCombatEnv._observe` passes `backend.stall_fraction` when the backend
has it; `LiveBackend.stall_fraction` = watchdog idle seconds / stall limit, 0 without a
watchdog. Evaluation without a watchdog always sees 0.

### Size

The vector size is computed in code and pinned by a test. Messages:
`MAX_MESSAGE_BYTES` and the Lua `max_bytes` become 49152; a worst-case frame test pins
the margin.

## Reward v5

`configs/reward-v5.yaml` = reward v4 with `stall_restart: -10.0`. The v4 ledger is
reused with version 5 accepted; `make_live_env(reward_version=5)`.

## Oracle metrics

`LiveOracle.kills` (Counter) and `LiveOracle.player_hits` (counters `enemy,
projectile, own_bomb, explosion, spikes, fire, creep, other`), cumulative per game
epoch, reset on game start. Lua:

- `MC_POST_NPC_DEATH`: count NPCs that are enemies (`IsEnemy()`, not friendly).
- `MC_ENTITY_TAKE_DMG` for `ENTITY_PLAYER` (returns nil, never alters damage):
  DAMAGE_EXPLOSION -> own_bomb when the source is a bomb spawned by a player, else
  explosion; DAMAGE_SPIKES or DAMAGE_CURSED_DOOR -> spikes; DAMAGE_FIRE -> fire;
  DAMAGE_ACID -> creep; source projectile -> projectile; source NPC -> enemy; else
  other. Both callbacks are pcall-wrapped and bounded.

`LiveBackend` records the counters at episode start and exposes the per-episode
delta; `EpisodeSummary.enemies_killed` comes from it on the live path, and episode
rows add `hits_enemy` ... `hits_other`. These counters never reach the encoder,
normalizer, reward or recurrent state.

## Lineage

`configs/training-pure-v4.yaml`: contract observation 5, action 2, reward 5, action
repeat 6, use-head prior 0.85, seed 1, LSTM 256; hyperparameters as pure-v3 with
gamma 0.995 and ent_coef 0.005. Run root `runs/pure-v4`, first session
`--initialize`. Launchers and dashboard default to it. `configs/training-pure-v3.yaml`
moves to `archive/configs/`.
