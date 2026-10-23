## ADDED Requirements

### Requirement: Kill credit
Reward v6 SHALL pay the remaining HP credit of an enemy the observer listed when the game
reports that enemy killed and it is no longer listed, at most once per enemy, so a kill
pays the same as damaging the enemy to zero HP. All reward v5 coefficients SHALL stay
unchanged.

#### Scenario: One-shot kill
- **WHEN** a listed enemy with full HP dies between two snapshots
- **THEN** one `enemy_damaged` event pays its max HP and the stall clock resets

#### Scenario: Repeated kill report
- **WHEN** the same killed identity arrives in later snapshots
- **THEN** no further damage is paid

#### Scenario: Unseen enemy
- **WHEN** the game reports a kill of an enemy the observer never listed
- **THEN** no damage is paid
