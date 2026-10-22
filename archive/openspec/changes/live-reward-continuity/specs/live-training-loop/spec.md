## MODIFIED Requirements

### Requirement: Approximate event derivation
Live reward events SHALL remain explicitly approximate and separate from policy
data. Absence from an oracle enemy list MUST NOT imply remaining-HP damage or a
kill. Without positive verified death evidence, no enemy_killed event SHALL be
derived. Overflow or membership gaps MUST NOT award unobserved damage.

#### Scenario: Enemy damaged then vanished
- **WHEN** a damaged enemy leaves the list and the same identity returns
- **THEN** absence earns no damage or kill reward, and reappearance rebaselines without retroactive damage

#### Scenario: Room re-entry
- **WHEN** another native room visit begins
- **THEN** entry emits no room-clear or disappearance kill, and previous membership is not compared across the visit boundary

#### Scenario: Changing membership during overflow
- **WHEN** either comparison endpoint has an overflowing list
- **THEN** rebaseline known HP without crediting the uncertain interval or inferring kills

#### Scenario: No verified kill channel
- **WHEN** only current live-loop snapshots are available
- **THEN** kill bonuses are withheld, including when an identity disappears permanently
