## ADDED Requirements

### Requirement: Prioritized level replay over run seeds
With contract `level_replay: plr_v1` the pure training SHALL keep a bank of run seeds with scores
and SHALL decide at the start of each run whether the next New Run replays a scored bank seed,
with probability `plr_replay_probability`, drawn from (1 - `plr_staleness`) P_score +
`plr_staleness` P_staleness with rank prioritization at temperature `plr_temperature`. Otherwise
the next run SHALL be unseeded and its seed SHALL join the bank.

#### Scenario: Rank prioritization and staleness
- **WHEN** three scored seeds have scores 0.1, 3.0 and 1.0 at temperature 1 and staleness 0
- **THEN** their replay probabilities are proportional to 1/3, 1 and 1/2

### Requirement: Bounded seed bank
The bank SHALL hold at most `plr_bank_size` seeds and SHALL evict the lowest score, oldest first,
keeping unscored seeds. Unscored seeds MUST NOT be replayed.

#### Scenario: Eviction
- **WHEN** a new seed enters a full bank
- **THEN** the scored seed with the lowest score is removed, the oldest of equal scores first,
  and unscored seeds stay

### Requirement: Level replay is metadata and training only
The run seed MUST NOT enter the observation, the normalizer or the recurrent state, and frozen
evaluation MUST NOT use level replay.

#### Scenario: Encoding without the seed
- **WHEN** two snapshots differ only in the oracle `run_seed`
- **THEN** their encoded observations are identical

#### Scenario: Level replay off
- **WHEN** the contract has `level_replay: none` or no `level_replay` field
- **THEN** no bank exists, no seed is sent, the contract hash equals the hash without the field
  and the PLR hyperparameters are not recorded

### Requirement: Level replay scores from the agent's learning signal
The pure learner SHALL attribute each step of a rollout to the run it belongs to and SHALL score a
seed with the mean absolute GAE advantage, before any advantage normalization, over all trained
steps of its latest run, accumulated across rollouts.

#### Scenario: A run spans two rollouts
- **WHEN** a run has two steps in one rollout and two in the next
- **THEN** its seed's score after the second update is the mean of the four absolute advantages

### Requirement: Seed bank checkpoint state
Under `plr_v1` each checkpoint SHALL save the seed bank as `level_replay.json` with its sha256 in
the manifest, and resume SHALL restore it; a checkpoint without the bank MUST be refused. A bank
MUST be refused for a contract without level replay.

#### Scenario: Round trip
- **WHEN** a `plr_v1` lineage is checkpointed and resumed
- **THEN** the resumed bank has the saved seeds, scores and run counter

#### Scenario: Missing bank
- **WHEN** a `plr_v1` resume finds a checkpoint without `level_replay.json`
- **THEN** training stops with a checkpoint error before any rollout

### Requirement: Level replay episode metrics
`episodes.csv` SHALL carry `run_seed` and `seed_replayed` (1 when the run's seed was in the bank
when the run started), empty without level replay; a file with the previous header MUST be
upgraded once.

#### Scenario: Upgrade
- **WHEN** an `episodes.csv` with the header before these columns is opened
- **THEN** it is rewritten once with empty cells for its old rows
