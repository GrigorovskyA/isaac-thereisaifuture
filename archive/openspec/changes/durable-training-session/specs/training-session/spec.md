## Purpose

Provide finite, owned training startup and durable progress evidence without
confusing process uptime, navigation or checkpoint updates with learned success.

## ADDED Requirements

### Requirement: Strict finite startup
The runner SHALL require an exact compatible parent, explicit finite budgets and
Continue on file 2. It MUST refuse foreign game processes, approvals, mismatched
deployment and failed focus guards without fallback, retries or New Run.

#### Scenario: Invalid parent or foreign owner
- **WHEN** the parent is missing or incompatible, or another game or approval exists
- **THEN** startup stops before gameplay and records the refusal

#### Scenario: Menu focus refused
- **WHEN** the existing guarded menu adapter refuses focus or identity
- **THEN** the session records a fault and cleans up only owned resources

### Requirement: Single fixed deadline
The runner SHALL fix one monotonic deadline before startup and share it with the
learner. It MUST derive approval expiry from that deadline and one explicit paired
clock sample, round down, and refuse insufficient remaining time without renewal.

#### Scenario: Fractional clock and delayed startup
- **WHEN** startup consumes time or the wall clock contains a fractional second
- **THEN** lease expiry does not exceed the mapped fixed deadline and the learner receives no renewed duration

### Requirement: Evidence based durable status
The runner SHALL persist startup, waiting, combat learning, navigation,
checkpointing and terminal states with the last observed activity time, combat
decision count, completed checkpoint and update time, and phase durations.
Stale telemetry MUST be shown as waiting. Final status MUST survive optional
metrics failure and distinguish early_stop, fault, completed and user_cancelled.

#### Scenario: Clean navigation budget exit
- **WHEN** the learner exits cleanly before the deadline due to a navigation limit
- **THEN** final status is early_stop with that exact reason, never duration completion

#### Scenario: Process alive without new evidence
- **WHEN** the learner process remains alive but progress is stale
- **THEN** status reports waiting with the last observation timestamp

#### Scenario: Optional metrics fails
- **WHEN** optional metrics cannot be read
- **THEN** the durable terminal result still includes stop reason and cleanup outcomes

### Requirement: Owned cleanup on every stop
Cancellation and wall expiry SHALL release input, request normal close of only
the owned game, remove only the unchanged owned approval and release temporary
sleep prevention. Cleanup failures MUST be recorded and prevent success claims.
The runner MUST NOT relaunch or force-kill a game.

#### Scenario: User stop or deadline
- **WHEN** the user cancels or the fixed deadline expires
- **THEN** cooperative learner shutdown and bounded owned cleanup run once without relaunch

#### Scenario: Approval replaced during session
- **WHEN** the approval content changes after creation
- **THEN** cleanup refuses to delete the changed approval and records a cleanup fault
