## ADDED Requirements

### Requirement: Kills and damage sources
Each live episode row SHALL include enemies killed and player hits by source (enemy,
projectile, own bomb, explosion, spikes, fire, creep, other), counted by the observer.
These counts MUST NOT enter the observation, normalizer, reward or recurrent state.

#### Scenario: Own bomb
- **WHEN** the player is hurt by the explosion of a bomb they placed
- **THEN** the episode row counts one `hits_own_bomb`
