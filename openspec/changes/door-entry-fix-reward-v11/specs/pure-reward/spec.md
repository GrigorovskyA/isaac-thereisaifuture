## ADDED Requirements

### Requirement: Reward v11 blocked cost
Reward v11 SHALL equal reward v10 except `door_shaping: {coefficient: 2.0, max_hops: 5,
blocked_cost: 0.0}`. `blocked_cost` SHALL be a number >= 0, required for v11 and forbidden for
v9 and v10. A v10 config SHALL keep its potential unchanged (blocked cost 1).

#### Scenario: Loader
- **WHEN** a v11 config has a missing, negative or boolean `blocked_cost`
- **THEN** loading fails
- **AND** a v10 config with the key fails too

### Requirement: Blocked cost in the graph potential
The in-room term of a door in a room that is not calm or of a closed door, and the cost of a boss
room that is not clear or has enemies, SHALL be `blocked_cost`. Other terms SHALL be unchanged.

#### Scenario: Fighting room
- **WHEN** the room has enemies and `blocked_cost` is 0
- **THEN** the cost of a frontier door is its hop distance only

#### Scenario: Live boss room
- **WHEN** the boss room is not clear and `blocked_cost` is 0
- **THEN** the cost is 0

### Requirement: Room entry is free
Under reward v11, entering an unvisited room that has a usable door to another unvisited room
SHALL pay no door shaping at the door. Entering a dead end SHALL still lower the potential by
`coefficient * H`.

#### Scenario: Frontier room
- **WHEN** the player walks from the open door of a cleared room into the new room
- **THEN** the door shaping paid is 0 where v10 paid about `-coefficient * gamma`

#### Scenario: Dead end
- **WHEN** the new room's only door leads back to a room with an unvisited door
- **THEN** the potential falls by `coefficient * 1`

### Requirement: Shaping stays potential-based under v11
For any trajectory ending in a terminal step, the discounted sum of the door shaping under reward
v11 SHALL equal `-Phi(s0)`.

#### Scenario: Random walk
- **WHEN** a random walk over a room graph ends in a terminal step
- **THEN** the discounted sum equals `-Phi(s0)`

### Requirement: Reward v10 contracts refused
Checkpoints saved with the reward contract `pure-v10` or older SHALL be refused when the config
expects `pure-v11`.

#### Scenario: pure-v10 checkpoint
- **WHEN** a pure-v10 checkpoint is resumed with reward contract `pure-v11`
- **THEN** the resume is refused

### Requirement: A stall is terminal for learning
`IsaacCombatEnv.step` SHALL return `terminated=True, truncated=False` for a stall truncation and
use it as the reward `terminal` flag. Summaries, info and `episodes.csv` SHALL still report
truncated / stall. Other truncations SHALL stay truncated and keep the potential.

#### Scenario: Stall step
- **WHEN** the watchdog truncates the episode with reason `stall`
- **THEN** the learner sees terminated and the summary says truncated, stall
- **AND** the door shaping paid is `gamma * 0 - Phi(s)`

#### Scenario: Scenario cap
- **WHEN** an episode ends by a non-stall truncation
- **THEN** the learner sees truncated and `Phi` is not zeroed

### Requirement: Novelty counts across runs
With `novelty.cross_run` true (required for v11, forbidden before), a first visit of a
(stage, room, cell) key in a run SHALL pay `coefficient / sqrt(N)`, N the number of runs that
first visited it, this one included. Revisits in a run SHALL pay nothing. Counts SHALL persist
across runs, sessions and resumes and SHALL NOT be an observation or policy input.

#### Scenario: Start room decay
- **WHEN** four runs start in the same cell
- **THEN** the payments are 0.1, 0.0707, 0.0577 and 0.05

#### Scenario: v10 config
- **WHEN** a v10 ledger runs many times
- **THEN** it pays 0.1 each run and stores no counts

### Requirement: Novelty counts in checkpoints
Each checkpoint of a v11 lineage SHALL store the counts as `novelty_counts.npz`, listed in the
manifest with its sha256, and a resume SHALL load it; a resume without it SHALL fail. Frozen
evaluation SHALL NOT write counts.

#### Scenario: Missing file
- **WHEN** a v11 resume finds a checkpoint without a counts file
- **THEN** the resume is refused

### Requirement: Update hyperparameters
`training-pure-v4.yaml` SHALL set `n_epochs` 10, `batch_size` 128 and `target_kl` 0.03.
`target_kl` SHALL be optional, recorded per checkpoint and outside the contract hash.

#### Scenario: Contract hash
- **WHEN** only these hyperparameters change
- **THEN** the contract hash is unchanged
