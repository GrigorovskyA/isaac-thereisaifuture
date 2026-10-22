## Purpose
Allow bounded automatic new runs after confirmed death while preserving manual startup and default read-only observation.

## ADDED Requirements

### Requirement: Explicit lifecycle authorization
Restart mode MUST require an optional negotiated capability and explicit operator confirmation of manually selected file 2. Default observation SHALL remain read-only. Authority SHALL start only after acknowledgement transmission and end on disconnect. It MUST NOT provide arbitrary command execution or reset a live run.

#### Scenario: Ordinary observer
- **WHEN** a peer requests only read-only capabilities
- **THEN** death never causes an automatic restart

#### Scenario: Unsupported peer or unconfirmed profile
- **WHEN** the opt-in capability is absent from the acknowledgement or the operator has not confirmed file 2
- **THEN** the opt-in client refuses operation

### Requirement: Confirmed death and bounded dispatch
Only a future game-over event indicating death SHALL schedule a restart, bound to its session and epoch. It MUST wait 1500 ms, require one still-dead player, and dispatch at most once per epoch. Victory, revival, exit, new run, disconnect, expiry or more than five seconds of delay MUST cancel it. Neither health values nor transport failures SHALL trigger a restart.

#### Scenario: Natural game over
- **WHEN** an authorized solo run reaches game over and all guards remain valid
- **THEN** exactly one fixed restart is requested using the current character

#### Scenario: Invalidated pending death
- **WHEN** a guard changes before dispatch or the event is an ending
- **THEN** no restart is dispatched

### Requirement: Finite budget and observable outcome
The mode MUST allow at most three attempts within ten minutes per mod load; reconnect SHALL NOT replenish these limits. It SHALL log dispatch and confirm a fresh non-continued game-start with increasing epoch within five seconds. Errors or missing confirmation MUST disable further restarts for that mod load without retry. Offline simulation MUST NOT be reported as game verification.

#### Scenario: Confirmed transition
- **WHEN** a dispatched restart produces a fresh game-start event
- **THEN** diagnostics identify the old and new epochs and snapshots expose the new epoch

#### Scenario: Uncertain result or exhausted budget
- **WHEN** dispatch fails, confirmation times out, or a budget is exhausted
- **THEN** further automatic restarts stop and diagnostics explain why
