## ADDED Requirements

### Requirement: Non-farmable combat reward
The reward ledger SHALL pay each reward source at most once per episode and SHALL cap enemy damage credit at the enemy's initial HP.

#### Scenario: Healed enemy HP is not paid twice
- **WHEN** an enemy is damaged to half HP, then healed, then damaged again by the same amount
- **THEN** the total damage reward equals the reward for removing its initial HP once

#### Scenario: Duplicate events are ignored
- **WHEN** the same kill or room-clear event is delivered twice
- **THEN** the reward is paid once

### Requirement: Versioned coefficients
The ledger MUST load coefficients from the versioned reward configuration and MUST reject a configuration with an unsupported version or missing keys.

#### Scenario: Unsupported version
- **WHEN** the configuration declares an unknown reward version
- **THEN** loading raises an error

### Requirement: Fixed disjoint scenario splits
The scenario pool SHALL be a bounded, immutable set with several difficulty levels, SHALL assign every scenario to exactly one of the train, validation and test splits, and MUST carry a version string that changes whenever a scenario or assignment changes.

#### Scenario: Splits never overlap
- **WHEN** the scenarios of the three splits are compared
- **THEN** no scenario id appears in more than one split and every split contains each difficulty level

#### Scenario: Pool cannot be mutated
- **WHEN** code tries to change a scenario field or the pool
- **THEN** the change is rejected

### Requirement: Labelled non-learning baselines
The project SHALL provide a random policy and a scripted heuristic policy, MUST label the scripted policy `scripted-baseline`, and MUST feed policies only the encoded policy observation vector.

#### Scenario: Scripted policy uses the observation only
- **WHEN** the scripted policy receives an observation with a nearest enemy
- **THEN** it shoots toward that enemy using only the vector contents

#### Scenario: Random policy is reproducible
- **WHEN** two random policies are reset with the same seed
- **THEN** they emit identical action sequences

### Requirement: Equal-budget evaluation report
The evaluation SHALL run the same number of episodes for every scenario and seed, SHALL evaluate one split per call, SHALL report clear rate with a Wilson 95% confidence interval, mean damage taken, mean return, timeouts and deaths, and MUST report infrastructure faults separately and exclude them from rates. The report MUST be JSON-serializable and list every episode.

#### Scenario: Report is complete and serializable
- **WHEN** a policy is evaluated on a scenario list with several seeds
- **THEN** the report round-trips through JSON and attempts equal scenarios times seeds times episodes

#### Scenario: Faults are not deaths
- **WHEN** the backend raises a transport fault in every episode
- **THEN** the report shows faults only, with zero deaths, zero clears and zero valid episodes

#### Scenario: Mixed splits are rejected
- **WHEN** scenarios from two splits are passed to one evaluation
- **THEN** evaluation raises an error
