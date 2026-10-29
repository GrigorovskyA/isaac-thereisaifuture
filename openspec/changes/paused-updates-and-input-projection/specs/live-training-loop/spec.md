## ADDED Requirements

### Requirement: Shared input projection in the policy
The pure training profile SHALL build its RecurrentPPO policy with one shared features
extractor, `Linear(observation size, features_dim)` followed by ReLU, in front of the actor
and critic LSTMs. `features_dim` MUST be part of the hashed contract so that a checkpoint
of another width is refused on resume, frozen evaluation and checkpoint-policy loading.
Fresh models for training, resume and evaluation MUST use the same construction helper.

#### Scenario: Fresh model
- **WHEN** a fresh pure model is created with `features_dim` 512
- **THEN** both LSTMs take 512 inputs through the shared extractor
- **AND** the use-head initial prior still applies to the action head

#### Scenario: Different width
- **WHEN** a checkpoint was written with another `features_dim`
- **THEN** resume and evaluation refuse it before any environment is created

### Requirement: Game paused during optimizer updates
With `live.pause_during_updates` true, the live backend SHALL release held input, press Esc
through the guarded game keyboard and wait for a `paused` snapshot at the end of each
rollout, and SHALL press Esc and wait for an `active` snapshot at the next rollout start.
Waits MUST be bounded. The flag MUST NOT be part of the lineage hash, and the simulated and
fake backends SHALL do nothing.

#### Scenario: Update with a clean pause
- **WHEN** a rollout ends on the live backend with the flag on
- **THEN** the game is paused before the optimizer runs and resumed before the next rollout
- **AND** the `train.csv` row has `pause_seconds` and `pause_ok` 1

#### Scenario: Time while paused
- **WHEN** snapshots arrive while the game is paused
- **THEN** they add no step time, stall or stagnation time
- **AND** the first action after the resume uses a snapshot read after it

### Requirement: Pause failures never fault the session
Any pause failure (game already paused or not active, no keyboard, lost focus, key error,
timeout) SHALL be recorded once per occurrence and MUST NOT fault the session or stop
training.

#### Scenario: Pause not possible
- **WHEN** the game is already paused, loses focus or does not report `paused` in time
- **THEN** an `update_pause_skipped` event is recorded and training continues
- **AND** a game found paused at the next rollout start is resumed by the same key

### Requirement: Pause metrics
`metrics/train.csv` SHALL carry `pause_seconds` and `pause_ok` columns, empty when pausing is
off or the backend cannot pause, and files with an older header SHALL be upgraded with empty
cells for older rows.

#### Scenario: Older header
- **WHEN** training opens a `train.csv` written before the pause columns
- **THEN** the file is rewritten once with the full header and old rows keep empty cells
