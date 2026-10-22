## ADDED Requirements

### Requirement: Schema 3 game facts
The observer SHALL emit `entity_frame` schema 3 with pickup `variant`, `subtype` and
`price`, an `inventory` block, a bounded sorted `collectibles` list and a `room`
block as defined in the design. Values outside their declared ranges MUST fail
validation as a protocol error, never be silently clipped into a valid frame.

#### Scenario: Valid schema 3 frame
- **WHEN** a frame carries in-range pickup, inventory, collectible and room fields
- **THEN** it decodes and encodes to a vector of exactly 1837 finite values

#### Scenario: Malformed facts
- **WHEN** a frame has an unknown field, a negative counter, an unsorted or duplicate collectible list, or more than 256 collectibles without overflow accounting
- **THEN** decoding fails with a protocol error

### Requirement: Facts without advice
The policy vector MUST contain only observed game facts. It MUST NOT contain clear
line, in-range, target choice, reachable position or any derived recommendation.
The oracle `room_index` MUST NOT enter the policy vector, normalizer or recurrent
state.

#### Scenario: Oracle change only
- **WHEN** two frames differ only in oracle fields
- **THEN** their encoded policy vectors are identical

### Requirement: Bounded collectible capture
Lua SHALL recompute the collectible list only on game start, room change and every
30 frames, and SHALL cap it at 256 IDs in 1..1024 with an overflow count.

#### Scenario: Collectible pickup
- **WHEN** the player gains a collectible between recomputations
- **THEN** the list includes it no later than 30 frames or the next room change
