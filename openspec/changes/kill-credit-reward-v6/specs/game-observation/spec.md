## ADDED Requirements

### Requirement: Killed enemy identities
The live oracle SHALL include `killed`, the identities of up to 16 most recent unfriendly
enemies killed this game epoch that the observer listed in the current room visit, oldest
first, and SHALL NOT pass them to the encoder, policy or normalizer.

#### Scenario: Kill of a listed enemy
- **WHEN** a listed enemy dies
- **THEN** the next oracle `killed` ends with its identity

#### Scenario: New game
- **WHEN** a new game epoch starts
- **THEN** `killed` is empty
