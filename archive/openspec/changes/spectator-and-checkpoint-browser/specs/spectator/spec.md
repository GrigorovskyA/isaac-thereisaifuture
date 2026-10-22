## ADDED Requirements

### Requirement: Checkpoint browser
The browser SHALL list every checkpoint directory with a manifest, showing id, timesteps, seed,
parent and evaluation metrics when a report exists, and MUST flag incompatible or corrupt
checkpoints instead of hiding them.

#### Scenario: Incompatible checkpoint listed
- **WHEN** a manifest has a different observation schema version
- **THEN** it is listed as incompatible with the reason

#### Scenario: Incompatible checkpoint selected
- **WHEN** the user asks to watch an incompatible checkpoint
- **THEN** the request is rejected and no policy is loaded

### Requirement: Deterministic terminal spectating
The spectator SHALL play a fixed scenario with a fixed seed and emit text lines with frame id,
action, reward and outcome, and MUST NOT train, capture the monitor or inject desktop input.

#### Scenario: Same seed
- **WHEN** the same mode, scenario and seed are watched twice
- **THEN** the output lines are identical

#### Scenario: Stop
- **WHEN** the step limit is reached or the run is interrupted
- **THEN** the backend is released and the summary reports outcome stopped

### Requirement: No oracle data in spectator outputs
Spectator output and replay recordings MUST contain policy-visible data only.

#### Scenario: Recording
- **WHEN** a watch run writes a replay
- **THEN** the file is a policy_frames stream and the printed lines contain no oracle data

### Requirement: Explicit control of a real game
The spectator MUST refuse to control a real game unless a real backend is explicitly injected,
and SHALL label the synthetic simulator in its output.

#### Scenario: Game requested without backend
- **WHEN** `watch --game` runs with no injected backend
- **THEN** the command fails with a non-zero exit code
