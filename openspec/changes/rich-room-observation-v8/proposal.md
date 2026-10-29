## Why

Reward v9 lineage (contract `3cb9d928`, observation schema 7): at about 200k steps the agent
leaves the start room in about 90% of episodes, kills 7-10 and clears 1.3-1.6 rooms per 1000
steps, but visits only about 2.2 rooms per episode and has never reached floor 2. To choose
between rooms it must see what the player sees. The schema 7 observation lacks:

- Door facts: per slot only an `open` bool. No door type (normal, locked, boss, treasure,
  shop, curse, secret, challenge, devil or angel...), no lock flag, nothing about the room
  behind the door.
- Minimap types: known, visited, current, boss, treasure, shop and "other"; many room types
  collapse into "other".
- Floor features: the obstacle classes have no trapdoor (the floor exit), crawlspace stairs,
  pressure plate, key lock block or teleporter.
- Interactables: slot machines, beggars, blood donation, fortune teller, restock box, crane,
  confessional and the heaven light door after a boss are not exported at all.
- Enemy kinds: an enemy slot has only presence, position, velocity and an unknown HP, so the
  policy cannot tell a fly from a charger, a shooter or a boss except by motion, and the agent
  is meant to recognize and handle each kind by itself.
- Capacity: the observer caps (enemy 12, projectile 20, obstacle 24, pickup 8, own attack 16,
  bomb 4) and the encoder capacities (16, 32, 24, 8, 16, 4) differ and are small. Bosses can
  have 100+ projectiles, a high tear rate with multishot 50+ own tears, rock-heavy rooms 60+
  obstacles, shops and post-boss rooms many pickups.

## What Changes

- Observation schema 8 on wire frame schema 6; reward v9 unchanged.
- Caps, identical in the observer (`entity_caps`) and in Python (`ENTITY_CAPS`, which is also the
  encoder capacity): enemy 32, projectile 64, obstacle 64, pickup 24, own attack 48, bomb 8, new
  kind `interactable` 16. Nearest-first selection and per-kind `source_overflow` stay. Message
  limit 49152 -> 131072 bytes (observer `max_bytes`, `MAX_MESSAGE_BYTES`, `MAX_FRAME_BYTES`).
- Obstacle classes `trapdoor` (GRID_TRAPDOOR), `crawlspace` (GRID_STAIRS), `pressure_plate`
  (GRID_PRESSURE_PLATE), `lock_block` (GRID_LOCK) and `teleporter` (GRID_TELEPORTER), found by
  GridEntityType name. The first, second, third and fifth have no collision, so the collision filter
  that drops broken rocks does not apply to them. The border ring skip is unchanged. A pressure plate's
  pressed state is not exported: the slot layout has no clean field for it.
- Entity kind `interactable` with a class (slot_machine, beggar, blood_donation, fortune_teller,
  restock_box, crane, other_slot, heaven_door) from ENTITY_SLOT by variant (SlotVariant names,
  documented numbers as fallback) and the heaven light door effect.
- Doors per slot: `RoomFacts.doors` becomes 8 entries, each `null` (no visible door) or
  `{open, locked, target_type, target_visited}`. The encoder writes exists, open, locked, target
  visited and a class one-hot (15 features per slot). A door to a secret, super secret or ultra
  secret room that is still closed is a hidden wall and reads as absent.
- Room type classes shared by doors and the minimap: normal, boss, treasure, shop, secret,
  curse, challenge, devil_angel, sacrifice, arcade, special. The minimap channels become known,
  visited, current and the class one-hot (14), keeping the visibility rule (type only for visited
  rooms or rooms whose icon is displayed).
- Enemy identity: each enemy slot carries `npc_type`, `npc_variant`, `npc_max_hp` and the flags
  `boss`, `champion`, `flying` and `invulnerable` (all or none; current enemy HP stays unknown).
  The encoder adds identity valid, the four flags, log-scaled max HP and a one-hot of 64 buckets
  of a stable hash of (type, variant), so the enemy slot grows from 8 to 78 floats. A one-hot into
  the first linear layer is a learned embedding: we only say which kind it is, the agent learns
  what each kind means.
- Metrics only: `enemy_kinds` (distinct (type, variant) pairs seen in an episode), and per kind, `max_<kind>` (most entities in one snapshot, cut ones included) and
  `overflow_<kind>` (share of observed steps in which something was dropped) in `episodes.csv`.
- `OBSERVATION_SIZE` 3863 -> 9762. `configs/training-pure-v4.yaml` pins schema 8, new contract
  hash; the reward v9 schema 7 run is kept as `runs/pure-v4-reward-v9-schema7` and its
  checkpoints are refused. Hyperparameters and `configs/reward-v9.yaml` are unchanged.

## Non-goals

- No reward change (reward v9), no action change, no hyperparameter change.
- No reachability, "best door" or priority feature: door types and room classes are facts the
  player sees; using them is learned.
- No hidden data: a closed secret door, the contents of unvisited rooms and unrevealed map
  rooms stay out. The reward-only `oracle.doors` (door shaping) is unchanged.
- No new wire capability: the facts ride in the existing entity frame.

## Acceptance

- (a) Offline gate: `scripts/check.sh` or `scripts/Check.ps1` and strict OpenSpec validation.
- (b) Native one-hour `--initialize`: snapshots validate, the maximum snapshot bytes stay below
  the 131072 cap, a trapdoor, door classes and interactables are observed at least once if
  encountered, and the per-kind `max_*` and `overflow_*` columns are reported.
- (c) After the first 8 h session against the reward v9 schema 7 lineage at equal steps: the
  `rooms_visited` mean is higher, and any `max_stage > 1` or boss-room visits are reported.
- (d) Later: frozen evaluation against `random-prior` with the per-1k criterion
  (`compare_eval.py --baseline random-prior`: `kills_1k` interval above zero, `clears_1k` point
  difference positive).

## Impact

`mod/observer/main.lua`, `src/isaac_threrisaifuture/{entities,encoding,env,episode_metrics,
observation,observer_client,sim}.py`, `configs/training-pure-v4.yaml`, tests, docs. The mod must
be redeployed with the code: Python refuses frames of schema 5. Unverified natively:
GRID_TRAPDOOR, GRID_STAIRS, GRID_PRESSURE_PLATE, GRID_LOCK and GRID_TELEPORTER names and their
collision classes, SlotVariant names, EffectVariant.HEAVEN_LIGHT_DOOR, `door.TargetRoomType`,
`door:IsLocked()`, `EntityNPC:IsChampion()`, `Entity:IsVulnerableEnemy()`, `Entity:IsInvincible()`,
the GridCollisionClass names (COLLISION_NONE, COLLISION_WALL) and that a closed secret door reads as hidden through `IsOpen()`.
