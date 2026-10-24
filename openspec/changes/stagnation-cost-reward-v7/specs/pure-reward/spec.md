## ADDED Requirements

### Requirement: Stagnation cost
Reward v7 SHALL charge `stagnation.per_second` for every second of stall watchdog idle
time past `stagnation.grace_seconds`, in the step that adds that idle time. A step whose
idle clock went down (new progress) SHALL pay no stagnation cost. A dead player and a
run without a stall watchdog SHALL pay none. The cost SHALL appear in its own
`stagnation` reward column and SHALL NOT count as progress for the stall clock.

#### Scenario: Idle inside the grace period
- **WHEN** the idle clock moves from 5 s to 15 s with a 20 s grace
- **THEN** the stagnation column is zero

#### Scenario: Idle past the grace period
- **WHEN** the idle clock moves from 18 s to 25 s with a 20 s grace and -0.1 per second
- **THEN** the stagnation column is -0.5

#### Scenario: Progress resets the clock
- **WHEN** the idle clock moves from 60 s to 2 s
- **THEN** the stagnation column is zero

#### Scenario: Full stall
- **WHEN** an episode idles from 0 s to the 90 s stall limit and is truncated
- **THEN** the stagnation columns sum to -7.0 and the stall column is -5

### Requirement: Run-wide stagnation bound
The accumulated cost SHALL be capped for the entire episode/run at
`per_second * max(0, stall_seconds - grace_seconds)` (-7.0 with the shipped config).
New progress and same-run resets SHALL NOT replenish this allowance; snapshot
overshoot SHALL NOT exceed it.

#### Scenario: Multiple idle periods and overshoot
- **WHEN** an episode idles to 80 s, makes new progress, then idles to 90.2 s
- **THEN** its total stagnation cost is -7.0, not -13.02
- **AND** only a new game epoch restores the allowance

### Requirement: Reward v7 coefficients
Reward v7 SHALL equal reward v6 except `outcome.stall_restart: -5`,
`outcome.player_damage_half_heart: -0.5` and the new `stagnation` section. A death from
full health (death plus six half-hearts lost) SHALL NOT pay more than a full stall
(stall restart plus the largest stagnation cost for the configured stall limit).

#### Scenario: Suicide never pays better than a stall
- **WHEN** the reward v7 config and the training config stall limit are loaded
- **THEN** `stall_restart + per_second * (stall_seconds - grace_seconds)` is at least
  `death + 6 * player_damage_half_heart`

#### Scenario: Old checkpoints refused
- **WHEN** a pure-v6 checkpoint is resumed with reward contract `pure-v7`
- **THEN** the resume is refused
