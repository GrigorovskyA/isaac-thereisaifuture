## ADDED Requirements

### Requirement: Outcome-only reward
Reward v2 SHALL pay only the outcome terms in `configs/reward-v2.yaml`: enemy HP
damage, first room clear, first room visit, first floor entry, health lost, death,
active time, pickups, new collectibles, bounded healing and novelty. It MUST NOT
contain terms about positions relative to enemies, walls, lines of fire or item use.

#### Scenario: Term accounting
- **WHEN** a transition contains damage dealt, a first clear and a new collectible
- **THEN** the ledger reports each term separately and their sum equals the reward

### Requirement: Exploit bounds
"First" terms SHALL be keyed per run and MUST NOT repeat within a run. Consumable
pickups SHALL share a per-run cap. Healing SHALL pay only up to half-hearts lost
earlier in the run. Counter decreases MUST earn nothing and MUST NOT reset any set or cap.

#### Scenario: Drop and re-pickup
- **WHEN** a collectible or consumable is dropped and picked up again in the same run
- **THEN** no additional reward is paid

#### Scenario: Damage then heal
- **WHEN** the player loses two half-hearts and then heals four
- **THEN** the healing term pays for at most two half-hearts

#### Scenario: Repeated room entry
- **WHEN** the player leaves and re-enters an already visited or cleared room
- **THEN** no visit or clear reward is paid again

#### Scenario: New run
- **WHEN** a restart starts a new epoch
- **THEN** all per-run sets and caps reset

### Requirement: Episodic novelty
The novelty term SHALL pay coefficient/sqrt(n) for the n-th visit of a (room index,
40-unit cell) key in the current run, reported in its own ledger column.

#### Scenario: Standing still
- **WHEN** the player stays in one cell for many steps
- **THEN** the per-step novelty decreases monotonically toward zero
