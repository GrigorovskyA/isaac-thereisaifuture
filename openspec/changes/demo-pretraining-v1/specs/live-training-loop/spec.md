## ADDED Requirements

### Requirement: Demo recordings
`demo_recorder` SHALL store each mod session of a human game as gzip JSON lines in `runs/demos`:
a manifest line, then each validated `DemoSnapshot` with its receipt time. It SHALL flush about
once per second, start a new file on the next session after a disconnect and refuse to start
while the training port is in use. A truncated tail SHALL be readable up to the last full line.

#### Scenario: Session file
- **WHEN** the game connects in demo mode and the human plays
- **THEN** a new file holds the manifest and every snapshot with its receipt time

### Requirement: Demo gaps do not end a live peer
During demo recording a receive timeout SHALL preserve the peer and buffered bytes and retry
with the same short read deadline. One waiting message SHALL be emitted per silence gap. A
disconnect, protocol failure or 30-minute idle limit SHALL end the session. Training-mode
timeout behavior SHALL remain unchanged.

#### Scenario: Temporary loading gap
- **WHEN** an established demo peer sends no complete snapshot for five seconds and resumes
- **THEN** the recorder keeps one file and records subsequent snapshots from that peer

### Requirement: Continuation across recordings
Consecutive recordings ordered by creation time SHALL be treated as one run when the earlier last
active snapshot is alive, the gap is within the idle limit, the later first frame is at least 300
and lies between the earlier last frame minus 900 and that frame plus 30 times the gap in seconds
plus 300, and stage, stage type and character type match.

#### Scenario: A verified reconnect
- **WHEN** a later recording meets the boundary rule and continues the earlier run
- **THEN** decision vectors, labels and sequence boundaries match replaying the same unsplit stream

### Requirement: Optional seed agreement
Both known run seeds MUST match for continuation. Missing seeds do not prevent continuation.
Kills, epoch and visit IDs MUST NOT be used to reject a boundary.

#### Scenario: Different known seeds
- **WHEN** both boundary seeds are known and differ
- **THEN** the dataset keeps the recordings in separate runs

### Requirement: Preserve replay state across continuation
The replay SHALL preserve run progress, visited cells and the sequence at a stitched boundary,
resetting the watchdog and room event state. Its cache key SHALL cover all grouped recordings
and derivation rules.

#### Scenario: Room state across reconnect
- **WHEN** a verified continuation is replayed
- **THEN** run and visited-cell history remains available while the room event baseline is reset

### Requirement: Demo decision points
`demo_dataset.load_demos` SHALL place a decision at each first playable snapshot at least
`action_repeat_game_updates` frames after the previous one. A death, a new run or a window with
more than half of its masks missing SHALL end a sequence. Results SHALL be cached per verified
recording group and derivation key.

#### Scenario: Death
- **WHEN** the player dies in a recording
- **THEN** the sequence ends at the last decision before the death

### Requirement: Demo observations match live
Demo observations SHALL equal the live env's for the same snapshot stream: the stall clock is
replayed from the receipt times with the contract's limits and the visited cells are updated at
decision points only.

#### Scenario: Same observation as live
- **WHEN** one snapshot stream is fed through the live backend and env and through the dataset
- **THEN** the observation vectors match step by step

### Requirement: Demo labels
The label of a decision SHALL be the most held move and shoot direction over the updates its
action covers (ties by the faster movement axis, then fixed order) and a triggered use press
(bomb, then active, then pill/card), else none.

#### Scenario: Diagonal
- **WHEN** left and up are held for the whole window and the player moves faster vertically
- **THEN** the move label is up

### Requirement: Behaviour cloning pretraining
With contract `pretraining: demo_bc_v1` (absent means `none` and is left out of the hash) the
config SHALL have a `demo` section. A fresh lineage SHALL fit the observation normalizer on the
demos, train the policy on the NLL of the demo actions for `pretrain_steps`, write
`pretraining.json` and publish a checkpoint at step 0 before the first rollout.

#### Scenario: Fresh lineage
- **WHEN** `--initialize` starts a `demo_bc_v1` lineage with enough recordings
- **THEN** the first checkpoint is the pretrained policy at step 0 and RL resumes from it

### Requirement: Demo character filter
The demo dataset SHALL record the player's `character_type` at every decision point, and training
SHALL use only the decision points whose character is listed in `demo.characters` (default:
characters that play like Isaac). A decision point of another character, or without a player,
SHALL split its sequence; a switch between two listed characters SHALL NOT. The filter SHALL run
after the cache, so the cache holds every character and the list is not part of its key.

#### Scenario: Mixed characters
- **WHEN** a recorded run switches from Isaac to a character outside the list and back
- **THEN** the Isaac stretches become separate sequences and the other steps are not used

#### Scenario: Same run, two listed characters
- **WHEN** Lazarus (8) dies and rises as Lazarus risen (11)
- **THEN** the steps stay in one sequence

### Requirement: Minimum demo size
Training of a `demo_bc_v1` lineage SHALL refuse recordings with fewer than `demo.min_steps`
decision steps before the game is used.

#### Scenario: Not enough demos
- **WHEN** the recordings hold fewer steps than `demo.min_steps`
- **THEN** training stops with a configuration error

### Requirement: Decaying BC regulariser
During RL of a `demo_bc_v1` lineage, after each PPO update the learner SHALL run `bc_steps` BC
steps with step size `bc_coef` times the current learning rate, decayed linearly to 0 at
`bc_decay_timesteps`, and log its loss, weight and the KL it caused. At weight 0 it SHALL skip.

#### Scenario: Decay
- **WHEN** the lineage passes `bc_decay_timesteps`
- **THEN** no BC phase runs and the update is plain PPO with the contract's phases
