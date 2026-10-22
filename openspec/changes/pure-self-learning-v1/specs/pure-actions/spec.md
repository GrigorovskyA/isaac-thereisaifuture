## ADDED Requirements

### Requirement: Use-item action head
Commands SHALL carry `use` (`none`, `bomb`, `active`, `pillcard`) in the canonical
order after `shoot`. Only `kind="action"` MAY carry a non-`none` use. The training
environment action space SHALL be `MultiDiscrete([5, 5, 4])`. Stale, replayed and
noncanonical commands MUST be rejected exactly as before.

#### Scenario: Accepted bomb press
- **WHEN** a fresh action command with `use="bomb"` is accepted
- **THEN** `IS_ACTION_TRIGGERED` for `ACTION_BOMB` returns true exactly once for the player and `IS_ACTION_PRESSED` stays true until the hold ends

#### Scenario: Use on a non-action command
- **WHEN** a heartbeat, release or restart command carries a use other than `none`
- **THEN** Lua refuses it as incompatible and no button is pressed

#### Scenario: Release
- **WHEN** a hold expires, is replaced or released, or the connection drops
- **THEN** all use buttons read as not pressed and not triggered

### Requirement: Restart command
`kind="restart"` SHALL be accepted only with live training authority, restart
pacing and remaining budget, and SHALL dispatch the existing restart path without
requiring a dead player. It MUST be acknowledged as `accepted` or `rejected`.

#### Scenario: Authorized stall restart
- **WHEN** an authorized live session sends restart while alive and paced
- **THEN** exactly one restart is dispatched and the next game start has a higher epoch

#### Scenario: Unauthorized or paced-out restart
- **WHEN** authority is absent, pacing has not elapsed or the budget is exhausted
- **THEN** the command is rejected and no restart is dispatched
