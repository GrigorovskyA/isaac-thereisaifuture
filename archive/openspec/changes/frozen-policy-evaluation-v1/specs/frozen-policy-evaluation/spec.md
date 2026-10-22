## ADDED Requirements

### Requirement: Explicit frozen checkpoint identity
The frozen policy SHALL load exactly one explicitly named checkpoint directory and MUST refuse the
moving latest pointer. It SHALL expose a serializable immutable identity containing the checkpoint
id, algorithm, config hash, training seed, timesteps, schema versions and SHA-256 hashes of the
manifest, model and normalizer, and SHALL detect any later change to those artifacts on request.

#### Scenario: Latest pointer refused
- **WHEN** the checkpoint root containing `latest.txt`, or the pointer file itself, is given
- **THEN** loading fails with a checkpoint error

#### Scenario: Artifact changed after loading
- **WHEN** the model file differs from the hash recorded at load time
- **THEN** the unchanged-artifact check fails with a checkpoint error

### Requirement: Compatible and intact checkpoints only
Loading MUST reject a checkpoint whose schema versions, config hash or requested seed do not
match, whose algorithm is not RecurrentPPO, whose manifest id differs from its directory name, whose
model or normalizer shapes differ from the current observation and action spaces, or whose
artifacts are missing or unreadable.

#### Scenario: Different training configuration
- **WHEN** the expected config hash differs from the manifest
- **THEN** a checkpoint error is raised and no model is used

#### Scenario: Corrupt normalizer
- **WHEN** the normalizer file is not a readable VecNormalize state
- **THEN** a checkpoint error is raised

#### Scenario: Corrupt normalization statistics
- **WHEN** the saved observation mean or variance has the wrong shape or a non-finite value, the
  variance is negative, the statistics count is not a finite positive number, or epsilon or the
  clip limit is not finite and positive
- **THEN** construction fails with a checkpoint error before any inference, and the state is not
  repaired or clamped

#### Scenario: Zero variance is valid
- **WHEN** a saved observation variance is zero and epsilon is positive
- **THEN** the checkpoint loads and normalization yields finite values

### Requirement: Frozen deterministic inference
The frozen policy SHALL apply the saved observation statistics exactly once per decision, MUST
NOT update those statistics, MUST NOT normalize rewards, learn, call an optimizer or write any
checkpoint artifact, and SHALL request deterministic actions. A policy reset seed MUST NOT be
treated as a reproducible game seed.

#### Scenario: Statistics unchanged
- **WHEN** many observations are acted on
- **THEN** the observation mean, variance and count are unchanged and each model input equals
  one clipped normalization of the raw observation

#### Scenario: Repeated episode
- **WHEN** the policy is reset and given the same observation sequence twice
- **THEN** it returns the same actions

### Requirement: Recurrent state lifecycle
The frozen policy SHALL carry recurrent state between decisions of one episode and SHALL clear it
and mark an episode start on reset.

#### Scenario: Reset clears state
- **WHEN** the policy acts, then is reset and acts again
- **THEN** the first decision after reset receives no prior state and an episode-start flag

### Requirement: Validated policy boundary
Only encoded policy observations SHALL enter the frozen policy. It MUST reject observations that
are non-numeric, of the wrong shape or non-finite, and model outputs that are not integer actions
of shape two within `MultiDiscrete([5, 5])`; a rejected decision MUST NOT advance recurrent state.

#### Scenario: Non-finite observation
- **WHEN** an observation contains NaN or infinity
- **THEN** a value error is raised and the recurrent state is unchanged

#### Scenario: Non-finite normalized input
- **WHEN** normalization produces a non-finite value
- **THEN** a checkpoint error is raised, the model is not called and recurrent state is unchanged

#### Scenario: Out-of-range model action
- **WHEN** the model returns an action component of 5 or -1
- **THEN** an invalid-output error is raised

### Requirement: Predeclared live evaluation plan
The project SHALL keep a predeclared live evaluation plan that separates a descriptive
exploratory pilot from a confirmatory comparison, keeps the confirmatory comparison blocked until
comparable supported scenarios and train/validation/test separation exist, and MUST NOT promise
matched game seeds the live backend cannot provide. The plan grants no game, training, reset or
approval authority.

#### Scenario: Manual intervention in a pilot
- **WHEN** an operator intervenes during a pilot segment
- **THEN** the plan requires the intervention to be recorded and the segment excluded from
  autonomous-performance attribution
