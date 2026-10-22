## ADDED Requirements

### Requirement: Exploit-free resource shaping
The resource ledger SHALL pay bounded shaping once per entity identity and once per item per
episode, and MUST NOT pay for spending, ability use, or healing beyond maximum hearts.

#### Scenario: Drop and re-pick
- **WHEN** an item is picked up, dropped and picked up again
- **THEN** only the first pickup is rewarded

#### Scenario: Repeated pickup of one entity
- **WHEN** the same entity identity is picked up more than once
- **THEN** it is rewarded once

#### Scenario: Empty ability use
- **WHEN** an ability is used with no effect
- **THEN** no reward is paid and the empty use is counted

#### Scenario: Healed HP reuse
- **WHEN** a heart is picked up at full health
- **THEN** no reward is paid

### Requirement: Bounded and session-bound shaping
The ledger SHALL cap total shaping per episode and MUST reject events from another session.

#### Scenario: Farming loop
- **WHEN** many distinct pickups exceed the episode cap
- **THEN** total shaping does not exceed the cap

### Requirement: Build decision and counterfactual evaluation
The package SHALL expose a build-chooser protocol with a random baseline, and builds MUST be
evaluated on fixed scenarios through an evaluation callable outside any live episode.

#### Scenario: Fixed build evaluation
- **WHEN** a build is evaluated on a list of scenarios
- **THEN** the callable receives the same build for each scenario and results are per scenario
