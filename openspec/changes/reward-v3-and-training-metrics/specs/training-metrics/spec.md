## ADDED Requirements

### Requirement: Per-update training statistics
Training SHALL append one row per optimizer update cycle to `metrics/train.csv`
with the SB3 train statistics and the rollout action mix per head. A write failure
MUST NOT stop or slow training beyond the failed write.

#### Scenario: Update completed
- **WHEN** a rollout is collected and the model is optimized
- **THEN** a row with timesteps, losses, entropy, explained variance and action shares summing to 1 per head is appended

#### Scenario: Unwritable metrics file
- **WHEN** the metrics file cannot be written
- **THEN** training continues and the error is logged

### Requirement: Episode action and exit facts
Each episode summary SHALL include use presses per kind, half-hearts lost, and the
steps to the first room exit and first enemy damage (empty when absent).

#### Scenario: Never leaves the start room
- **WHEN** an episode ends without a room change
- **THEN** `steps_to_first_exit` is empty and `rooms_visited` is 1
