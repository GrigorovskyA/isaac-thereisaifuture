## 1. Implementation

- [x] 1.1 Wire frame schema 6: `interactable` kind and class, new obstacle classes, `DoorFacts`
  in `RoomFacts.doors`, `ENTITY_CAPS`, 131072-byte messages; validation tests.
- [x] 1.2 Encoder (observation schema 8): equal capacities, door slots, room classes for doors and
  minimap, interactable block, `EncodedObservation.counts`; layout and encoding tests.
- [x] 1.3 Lua observer: caps, 131072 bytes, grid classes by name with the floor-feature collision
  exemption, interactables, door facts with the hidden secret door rule, frame schema 6; Lua tests
  for classes, interactables, doors, caps, nearest-first and worst-case bytes; a test that the
  Lua and Python caps and classes match.
- [x] 1.4 Metrics: `max_<kind>` and `overflow_<kind>` per episode in `episodes.csv`.
- [x] 1.5 Contract: `training-pure-v4.yaml` schema 8; schema 7 refused (new hash); docs
  (RL_DESIGN, ENTITY_OBSERVATION_PROTOCOL, OBSERVATION_PROTOCOL, RUNTIME_AUTHORITY, README).

- [x] 1.6 Enemy identity: Lua `enemy_facts` (type, variant, max HP, boss, champion, flying,
  invulnerable; every call wrapped), strict optional wire fields on enemies, encoder identity block
  (64 hashed buckets) and the `enemy_kinds` metric; Lua, wire, bucket and layout tests.

## 2. Verification

- [x] 2.1 Full offline gate and strict OpenSpec validation.
- [ ] 2.2 Windows `scripts/Check.ps1`; redeploy the observer mod (`main.lua` and `metadata.xml` to
  the game mods folder; the preflight compares SHA-256); rename `runs\pure-v4` to
  `runs\pure-v4-reward-v9-schema7`; one-hour native session with `--initialize`; check that
  snapshots validate, the maximum snapshot bytes stay below 131072, a trapdoor, door classes
  and interactables appear at least once when encountered, door facts match what the room shows
  (a closed secret wall is absent), and the `max_*` and `overflow_*` columns are filled.
  Also: the share of rejected (stale) commands and the steps per second stay close to the
  schema 7 hour (the observer sends 32 KB per pump, so large frames leave in a few frames);
  every Isaac API name listed as unverified in the proposal reads real values, not fallbacks.
- [ ] 2.3 Acceptance: the first 8 h session against `runs/pure-v4-reward-v9-schema7` at equal steps
  (`rooms_visited` mean, `max_stage`, boss-room visits), then the frozen evaluation against
  `random-prior` with the per-1k criterion.
