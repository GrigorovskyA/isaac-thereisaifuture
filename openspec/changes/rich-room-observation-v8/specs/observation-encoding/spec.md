## ADDED Requirements

### Requirement: Observation schema 8 layout
Observation schema 8 SHALL use the observer caps as encoder capacities (enemy 32, projectile 64,
obstacle 64, pickup 24, own attack 48, bomb 8, interactable 16), obstacle slots with 16 classes
and interactable slots with an 8 class one-hot. `OBSERVATION_SIZE` SHALL be 9762 and checkpoints
of schema 7 and older SHALL be refused.

#### Scenario: Schema 7 checkpoint
- **WHEN** a checkpoint from the reward v9 schema 7 lineage is loaded under the schema 8 contract
- **THEN** loading fails with a contract or schema mismatch

#### Scenario: Interactable slot
- **WHEN** a beggar is the nearest interactable
- **THEN** the first interactable slot is present with its relative position and the `beggar`
  class hot

### Requirement: Door and minimap encoding
The room block SHALL hold 15 features per door slot (exists, open, locked, target visited, 11 room
class one-hot) and the minimap SHALL hold 14 channels per cell (known, visited, current, 11 room
class one-hot). A room whose type is hidden SHALL have no class channel.

#### Scenario: Door slot encoding
- **WHEN** slot 3 holds a closed, locked door to an unvisited treasure room
- **THEN** its features are exists 1, open 0, locked 1, visited 0 and the `treasure` class hot
- **AND** an empty slot is all zero

#### Scenario: Minimap class
- **WHEN** a visited room is a devil room
- **THEN** its cell carries the `devil_angel` class; a displayed room with a hidden type has none

### Requirement: Room classes
Room types SHALL be grouped as normal (1), boss (5), treasure (4), shop (2), secret (7, 8, 29),
curse (10), challenge (11, 17), devil_angel (14, 15), sacrifice (13), arcade (9) and special
(every other type). Doors and the minimap SHALL use the same grouping.

#### Scenario: Unlisted type
- **WHEN** a door leads to a planetarium
- **THEN** its class is `special`

### Requirement: Cap metrics
Each episode row SHALL carry, per entity kind, `max_<kind>` (the most entities of the kind in one
observed snapshot, counting those the observer or the encoder dropped) and `overflow_<kind>` (the
share of observed snapshots in which any were dropped). These values MUST NOT enter the
observation, normalizer, reward or recurrent state.

#### Scenario: Overflow share
- **WHEN** 2 of 4 observed snapshots of an episode drop enemies and the largest holds 42
- **THEN** the row has `max_enemy` 42 and `overflow_enemy` 0.5

### Requirement: Enemy identity encoding
An enemy slot SHALL be 78 floats: the 8 slot features, identity valid, boss, champion, flying,
invulnerable, `log1p(max HP) / log1p(10000)` clipped to [0, 1], and a one-hot of 64 buckets of
`((type * 4096 + variant) * 2654435761 mod 2^32) >> 26`. The hash SHALL NOT depend on Python's
`hash()` or on the process. Distinct kinds MAY share a bucket. An enemy without identity facts
SHALL read zeros, with identity valid 0.

#### Scenario: Same kind
- **WHEN** two enemies have the same type and variant
- **THEN** their identity one-hots are equal, in any process

#### Scenario: Unknown identity
- **WHEN** an enemy frame has no identity facts
- **THEN** its identity block is all zeros

#### Scenario: Enemy kinds metric
- **WHEN** an episode shows enemies of 2 distinct (type, variant) pairs
- **THEN** `enemy_kinds` in `episodes.csv` is 2
