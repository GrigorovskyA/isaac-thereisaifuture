## ADDED Requirements

### Requirement: Run seed report
With the opt-in capability `seeded_restart_v1`, allowed only together with the live loop, the
observer SHALL report the run's start seed string as oracle `run_seed`, read once per game epoch,
and null when unreadable or not in the seed alphabet. Without the capability the snapshot MUST be
unchanged.

#### Scenario: Seed reported
- **WHEN** the capability is negotiated and the game reports `AAAA BBBB`
- **THEN** every oracle block of that epoch carries `run_seed` `AAAA BBBB` and the entity frame
  carries no seed

#### Scenario: Capability without the live loop
- **WHEN** a hello requires `seeded_restart_v1` without `live_loop_v1`
- **THEN** the observer closes the session without an acknowledgement

### Requirement: Validated seeds on restart commands
The observer SHALL accept an optional `seed` only on `restart` and `next_seed` commands after the
capability. A seed MUST match `XXXX XXXX` over A-Z and 0-9 without I, O, U and 5; any other seed,
or a seed on another kind or without the capability, MUST close the session and MUST NOT reach the
console.

#### Scenario: Malformed seed
- **WHEN** a command carries `t1mm ay48`, `IIII AAAA` or a seed with extra characters
- **THEN** the session closes and nothing is dispatched

### Requirement: Seeded dispatch through the guarded restart path
A seeded restart SHALL issue exactly `seed XXXX XXXX` instead of `restart` through the same
guarded dispatch, pacing, budget and fresh game-start confirmation. `next_seed` SHALL arm the seed
of the mod's own death restart for the current game epoch only; a game start or disconnect MUST
clear it, and it MUST be refused while a restart is pending or awaiting confirmation.

#### Scenario: Seeded stall restart
- **WHEN** an accepted `restart` command carries `T1MM AY48`
- **THEN** the mod dispatches exactly `seed T1MM AY48` once and the next run reports that seed

#### Scenario: Armed death restart
- **WHEN** `next_seed` armed `T1MM AY48` and the player dies in that epoch
- **THEN** the delayed death restart dispatches `seed T1MM AY48`, and the following death restart
  of the next epoch is a plain `restart`

#### Scenario: Plain restart unchanged
- **WHEN** a `restart` command carries no seed
- **THEN** the mod dispatches `restart` exactly as before, with or without the capability
