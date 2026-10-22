## ADDED Requirements

### Requirement: One continuous lineage
The lineage hash SHALL cover only the `contract` section of the training config.
Resume SHALL always load `latest` with weights, optimizer state, normalizer and RNG.
Changes to `hyperparameters` SHALL be applied on resume and recorded in each
checkpoint manifest. A contract mismatch or missing state MUST stop without
initializing a fresh model.

#### Scenario: Learning-rate change
- **WHEN** only `hyperparameters.learning_rate` changes between sessions
- **THEN** training resumes the same lineage with the new rate recorded in the next manifest

#### Scenario: Contract change
- **WHEN** the observation, action or reward version in `contract` changes
- **THEN** resume is refused

### Requirement: Bounded retention
Retention SHALL keep the 5 newest checkpoints and every 50th rollout, and MUST
never delete `latest` or its parent.

#### Scenario: Many rollouts
- **WHEN** 120 rollouts have been saved
- **THEN** exactly the 5 newest plus rollouts 50 and 100 remain

### Requirement: Episode metrics
Each finished episode SHALL append one row to `metrics/episodes.csv` with return,
damage, rooms visited and cleared, floor reached, pickups, outcome and truncation reason.

#### Scenario: Stall truncation row
- **WHEN** an episode is truncated by the watchdog
- **THEN** its row has outcome `truncated` and reason `stall`

### Requirement: Forever supervisor
`session_runner --forever` SHALL run bounded sessions back to back, resuming
`latest`, and SHALL stop on a stop file, Ctrl+C, the disk cap or the
consecutive-fault cap, releasing input and closing the game it owns.

#### Scenario: Lease end
- **WHEN** a session reaches its lease end
- **THEN** a checkpoint exists and the next session resumes it

#### Scenario: Repeated faults
- **WHEN** five consecutive sessions end in infrastructure faults
- **THEN** the supervisor stops and reports the fault cap
