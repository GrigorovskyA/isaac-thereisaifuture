## ADDED Requirements

### Requirement: Prior-matched random baseline
An evaluation session MAY run a `random-prior` policy: move and shoot uniform, the use
head none with the training config's `contract.use_head_initial_none_probability` and
the rest split evenly. It MUST be deterministic per seed, stateless and checkpoint-free,
and the `evaluation` record SHALL name it `random-prior`.

#### Scenario: Use head follows the configured prior
- **WHEN** `random-prior` is sampled many times with a fixed seed and a none
  probability of 0.85
- **THEN** the use head is none in close to 85% of draws, each other use in close to
  5%, and move and shoot are uniform

#### Scenario: Deterministic per seed
- **WHEN** two `random-prior` policies are reset with the same seed
- **THEN** they return identical action sequences

#### Scenario: Session accepts it and refuses a checkpoint
- **WHEN** `session_runner --evaluate random-prior` is run without `--checkpoint`
- **THEN** the session is planned like a `random` evaluation and its `evaluation`
  record names the policy `random-prior`
- **WHEN** `--evaluate random-prior` is combined with `--checkpoint`
- **THEN** the CLI exits with an error before any game access
