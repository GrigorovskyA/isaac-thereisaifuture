## ADDED Requirements

### Requirement: Reward v3 balance
Reward v3 SHALL pay novelty only for the first visit of a (stage, room, 40-unit
cell) key per run, SHALL charge a stall-restart penalty once on the final step of
an episode truncated with reason `stall`, and SHALL use the coefficients in
`configs/reward-v3.yaml`. It MUST remain outcome-only.

#### Scenario: Standing still
- **WHEN** the player stays in one cell for many steps
- **THEN** novelty pays once for that cell and nothing afterwards

#### Scenario: Idle until stall
- **WHEN** a synthetic episode wanders an empty room until the watchdog truncates it
- **THEN** its return is lower than an episode that deals one full enemy kill, loses one heart and clears the room

#### Scenario: Death is not a stall
- **WHEN** an episode terminates by death
- **THEN** no stall penalty is paid
