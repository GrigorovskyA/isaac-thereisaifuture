## ADDED Requirements

### Requirement: Door facts
The entity frame SHALL report, for each of the 8 door slots, `null` when no door is visible, or
`open`, `locked`, `target_type` (the RoomType behind the door, null when unreadable) and
`target_visited`. A door to a secret, super secret or ultra secret room that is not open
SHALL be reported as `null`. An unreadable lock SHALL read as not locked and an unreadable
target room as not visited. A door that cannot be read SHALL be reported as `null` and SHALL
NOT make the snapshot unavailable.

#### Scenario: Locked treasure door
- **WHEN** slot 2 holds a closed, locked door to a never visited treasure room
- **THEN** slot 2 is `{open: false, locked: true, target_type: 4, target_visited: false}`

#### Scenario: Hidden secret door
- **WHEN** a slot holds a closed door to a secret room
- **THEN** that slot is `null`, and after the wall is bombed open it is reported with
  `target_type` 7

#### Scenario: Old bool doors
- **WHEN** a frame carries a list of booleans as `room.doors`
- **THEN** decoding fails with a protocol error

### Requirement: Floor features and interactables
The observer SHALL export the trapdoor, crawlspace stairs, pressure plates, key lock blocks and
teleporters as obstacles with their own class, found by GridEntityType name and without the
collision filter that drops broken rocks. It SHALL export slot machines, beggars and the heaven
light door as `interactable` entities with a class, grouped by variant. Names missing from the
game SHALL be skipped.

#### Scenario: Trapdoor after a boss
- **WHEN** a trapdoor grid entity without collision lies inside the room
- **THEN** the frame holds an obstacle of class `trapdoor` at its relative position

#### Scenario: Broken rock
- **WHEN** a rock grid entity has no collision
- **THEN** it is not exported

### Requirement: Entity caps and message bound
The observer caps per kind SHALL be enemy 32, projectile 64, obstacle 64, pickup 24, own attack
48, bomb 8 and interactable 16, nearest first, with the cut count in `source_overflow`. The
observer and Python SHALL accept messages up to 131072 bytes, and a snapshot with every kind
past its cap, 8 doors, 64 map rooms and 256 collectibles SHALL stay below that limit.

#### Scenario: More enemies than the cap
- **WHEN** a room holds 50 visible enemies
- **THEN** the 32 nearest are exported and `source_overflow.enemy` is 18

### Requirement: Enemy identity facts
Each exported enemy SHALL carry `npc_type` (EntityType), `npc_variant` (Variant), `npc_max_hp`
(MaxHitPoints) and the flags `boss`, `champion`, `flying` (GridCollisionClass is NONE or WALL)
and `invulnerable` (not vulnerable or invincible), all seven or none. Other kinds SHALL carry
none. Every API call SHALL be guarded: a missing method reads false and a missing number 0.
The current enemy HP SHALL stay unknown.

#### Scenario: Boss champion
- **WHEN** an enemy of type 23 and variant 2 answers `IsBoss()` and `IsChampion()` with true
- **THEN** the frame holds `npc_type` 23, `npc_variant` 2, `boss` true and `champion` true

#### Scenario: Missing method
- **WHEN** the enemy has no `IsVulnerableEnemy` or `IsInvincible` method
- **THEN** the snapshot is still sent and `invulnerable` is false

#### Scenario: Partial facts
- **WHEN** a frame carries `npc_type` without the other six facts, or on a projectile
- **THEN** validation rejects the frame
