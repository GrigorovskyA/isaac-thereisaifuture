## ADDED Requirements

### Requirement: Observation schema 9 layout
Observation schema 9 SHALL widen the inventory block to 82 floats, a pickup slot to 99 floats and
add a block of 8 held tag counts after the weapons. `OBSERVATION_SIZE` SHALL be 11691 and
checkpoints of schema 8 and older SHALL be refused.

#### Scenario: Schema 8 checkpoint
- **WHEN** a checkpoint of the schema 8 lineage is loaded under the schema 9 contract
- **THEN** loading fails with a contract or schema mismatch

### Requirement: Item identity encoding
A pedestal pickup slot SHALL append quality / 4, a passive, active, familiar one-hot, max charges
/ 12 clipped to 1, 8 tag bits and a one-hot of 64 buckets of
`(item_id * 2654435761 mod 2^32) >> 26`. The hash SHALL NOT depend on Python's `hash()` or on the
process. Other pickups and empty pedestals SHALL read zeros. The active item SHALL get quality / 4,
tag bits and the same bucket one-hot, all zero without an active item.

#### Scenario: Pedestal item
- **WHEN** a pedestal holds an active item of quality 3 with 6 charges
- **THEN** its item block has quality 0.75, the active type hot, charges 0.5 and one hot bucket

#### Scenario: Non-collectible pickup
- **WHEN** the nearest pickup is a coin
- **THEN** its item block is all zero

### Requirement: Held tag counts
The held tag block SHALL hold, per tag, the number of held collectibles with the tag divided by 3
and clipped to 1.

#### Scenario: Transformation progress
- **WHEN** two held items carry the SPIDER tag
- **THEN** the SPIDER entry is 2/3
