## ADDED Requirements

### Requirement: Reward v13 values
Reward v13 SHALL equal reward v12 except a new key `stall.calm_seconds` 15 and
`stagnation.grace_seconds` 3. `stall.seconds` SHALL stay 30.

#### Scenario: Config values
- **WHEN** `configs/reward-v13.yaml` is loaded
- **THEN** the coefficients equal v12 with grace 3 and a calm limit of 15

### Requirement: Calm stall limit in the reward contract
`stall.calm_seconds` SHALL be required for v13 and forbidden for v12. It SHALL be a number above
`stagnation.grace_seconds` and at most `stall.seconds`.

#### Scenario: Loader
- **WHEN** a v13 config has no `calm_seconds`, or one that is boolean, not a number, not above the
  grace period or above `stall.seconds`
- **THEN** loading fails
- **AND** a v12 config with `calm_seconds` fails too

### Requirement: The stagnation floor is sized for the calm limit
Under reward v13 the run-wide stagnation floor SHALL be `per_second * (calm_seconds - grace)`, so
a stall costs `stall_restart` plus that floor in any room, and a death with 1 or 6 half hearts of
damage taken SHALL cost more than a stall.

#### Scenario: Cost order
- **WHEN** the shipped v13 config is evaluated
- **THEN** a stall costs -8.68 after 15 s and after 30 s, and a death costs -11.5 or -14.0

### Requirement: Calm rooms stall after the calm limit
With reward v13 the live env SHALL truncate an episode with reason `stall` after `calm_seconds`
of idle time while the room is calm (oracle `room_clear`, no enemy, no overflow), and after
`stall.seconds` otherwise. The stall-clock observation SHALL be idle time over the current limit.

#### Scenario: Calm room
- **WHEN** the room is clear and has no enemy and nothing counts as progress for 15 s
- **THEN** the episode is truncated with reason `stall` and one restart is sent

#### Scenario: Live enemy
- **WHEN** an enemy is alive and is never damaged
- **THEN** the episode runs until 30 s of idle time

### Requirement: Reward v12 contracts refused
The pure training config SHALL name reward version 13, and a contract with an older reward
version SHALL be refused.

#### Scenario: Older contract
- **WHEN** a pure training config names reward version 12
- **THEN** loading it fails
