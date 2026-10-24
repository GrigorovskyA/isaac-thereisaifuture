## ADDED Requirements

### Requirement: Frozen evaluation under the training protocol
An evaluation session SHALL run exactly one policy, either one exact checkpoint
directory of the configured pure lineage or the uniform random policy, in an env built
with the same action repeat, reward version, stall watchdog, consecutive fault cap,
deadline and stop file as pure training. It MUST NOT train, resume, write a
checkpoint or write under the training run root, and it SHALL write one
`metrics/episodes.csv` row per episode in the training format under its own root.

#### Scenario: Episodes are recorded and the policy restarts each episode
- **WHEN** a checkpoint is evaluated until the session deadline
- **THEN** every finished episode is a row in the evaluation root's `episodes.csv`,
  the recurrent state is cleared at each episode boundary and the run ends with a
  `budget` record and an `evaluation_result` record

#### Scenario: Training lineage untouched
- **WHEN** an evaluation session ends
- **THEN** no file under the training run root changed and the evaluation root has
  no `checkpoints` folder

#### Scenario: Idle policy still ends episodes
- **WHEN** the evaluated policy makes no progress for the stall limit
- **THEN** the episode is truncated with reason `stall` and recorded like in training

### Requirement: Frozen policy identity and sampling
A checkpoint evaluation SHALL verify the checkpoint against the config contract hash,
the config seed and the `pure-v6` reward contract before the first step, SHALL apply
the saved observation normalization without updating it, SHALL sample actions
stochastically with a fixed seed, and MUST verify at the end that the checkpoint
files are unchanged.

#### Scenario: Checkpoint of another configuration
- **WHEN** the checkpoint was produced under a different config contract
- **THEN** the session is refused before the game is entered and no episode is written

#### Scenario: Checkpoint modified during evaluation
- **WHEN** a checkpoint file differs from its loaded hash at the end
- **THEN** the session is a fault

### Requirement: Supervised evaluation session
`session_runner` SHALL offer `--evaluate checkpoint|random` with `--checkpoint` for the
single-session path only, SHALL derive seed, disk cap, unlimited restarts and
nonbinding step counts, SHALL keep the stop margin, approval, Continue entry, cleanup and
frozen source hashes of training sessions, and SHALL freeze the evaluated checkpoint
files. A normal stop at the deadline MUST end with state `completed`, and an
evaluation MUST NOT require or read checkpoint progress.

#### Scenario: Deadline stop
- **WHEN** an evaluation worker stops cooperatively for the wall-time deadline
- **THEN** the result state is `completed` with no latest checkpoint and no fault

#### Scenario: Refused flag combinations
- **WHEN** `--evaluate` is combined with `--forever`, `--evaluate checkpoint` has no
  `--checkpoint`, `--evaluate random` has `--checkpoint`, or `--checkpoint` has no
  `--evaluate`
- **THEN** the CLI exits with an error before any game access

#### Scenario: Unsafe run root
- **WHEN** the run root is the training run root, is inside it, overlaps the checkpoint
  directory, contains a `checkpoints` folder or already holds episodes
- **THEN** the session is refused before the game is launched

### Requirement: Offline comparison of evaluation roots
`scripts/compare_eval.py` SHALL read each given evaluation root's `episodes.csv`
without writing and print one row per root with the episode count, death, stall,
left-start-room and any-clear shares, mean damage fraction with its standard error,
mean kills, rooms cleared, half hearts lost and return, maximum stage and a 95%
Wilson interval for the stall share.

#### Scenario: Two roots
- **WHEN** the script is run on two roots with episodes
- **THEN** it prints a header and two rows, one per root, labelled by folder name

#### Scenario: Root without episodes file
- **WHEN** a root has no `metrics/episodes.csv`
- **THEN** the script exits with an error naming the root
