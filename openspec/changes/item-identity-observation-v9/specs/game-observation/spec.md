## ADDED Requirements

### Requirement: Item catalog facts
The entity frame SHALL carry, for each pedestal collectible (pickup variant 100 with subtype above
0), `item_quality` (0-4), `item_type` (`passive`, `active`, `familiar` or `unknown`),
`item_max_charges` (0-24) and `item_tags` (a mask over 8 ItemConfig tags), all or none, and no
other entity SHALL carry them. An unreadable item SHALL read quality 0, type `unknown`, 0 charges
and no tags.

#### Scenario: Pedestal with a known item
- **WHEN** a pedestal holds a passive item of quality 3 with the GUPPY tag
- **THEN** its pickup carries quality 3, type `passive`, 0 charges and the GUPPY bit set

#### Scenario: Heart pickup
- **WHEN** a heart is in the room
- **THEN** its pickup carries no item facts, and a frame that gives it some is rejected

### Requirement: Active item and held tag facts
The inventory SHALL carry `active_quality` and `active_tags` of the active item (0 without one),
and the frame SHALL carry `tag_counts`, the number of held collectibles per tag in tag order.
Tag flags SHALL be read by name from the game; a missing name SHALL read as no tag. Facts SHALL
come from the game's ItemConfig only: no predicted effects.

#### Scenario: Missing tag name
- **WHEN** the game has no `ItemConfig.TAG_FLY`
- **THEN** the FLY bit is never set and the other tags are unaffected

#### Scenario: Held items
- **WHEN** two held collectibles have the GUPPY tag
- **THEN** the GUPPY entry of `tag_counts` is 2

### Requirement: Blind pedestal
When the game reports a pedestal as blind, the observer SHALL export subtype 0 and no item facts
for it.

#### Scenario: Curse of the blind
- **WHEN** `IsBlind()` returns true for a pedestal, or the level has the curse of the blind
- **THEN** the pickup has subtype 0 and no item facts

### Requirement: Frame schema 7
The observer SHALL send `observation_schema_version` 7 and Python SHALL refuse frames of schema 6
and older.

#### Scenario: Old frame
- **WHEN** a frame of schema 6 arrives
- **THEN** decoding fails with a protocol error
