# Spec Delta

## ADDED Requirements

### Requirement: Opt-in bounded lifecycle diagnostics
The observer SHALL offer default-off local lifecycle diagnostics with a nonrenewable
20-minute window and at most 256 records of 768 bytes each per mod load. Reconnects
and game epochs MUST NOT renew these limits. Diagnostics MUST NOT enter wire
snapshots, policy inputs, rewards or checkpoints.

#### Scenario: Default execution
- **WHEN** lifecycle diagnostics are not explicitly enabled
- **THEN** no lifecycle diagnostic records are emitted and existing bridge behavior is preserved

#### Scenario: Diagnostic budget exhausted
- **WHEN** the time or record limit is reached across callbacks and reconnects
- **THEN** diagnostics stop permanently for that mod load, including any final stop record within the count limit, while ordinary cleanup and limits remain operational

### Requirement: Correlated lifecycle and authority facts
Enabled diagnostics SHALL record ordered callback entry/exit, restart dispatch
before/after, close and hello authorization facts, using monotonic event IDs,
time, session, epoch and frame when available. Records MUST identify approval
preservation/invalidation, awaiting confirmation, restart attempt and eligibility
without exposing approval evidence strings or file contents.

#### Scenario: Expected automatic restart
- **WHEN** one dispatch causes exit, start confirmation and reconnect
- **THEN** records distinguish pre-exit authority preservation, the confirmed epoch and the authority facts used by the next hello

#### Scenario: Additional exit and start
- **WHEN** a second exit/start occurs without another bridge dispatch
- **THEN** records show its ordering, missing dispatch correlation and the actual approval invalidation decision without labeling it manual input

#### Scenario: Capability refused
- **WHEN** hello cannot advertise live actions
- **THEN** diagnostic facts distinguish missing approval, inactive game, expiry and elapsed action lease from other approval validation failures without reloading or renewing authorization

### Requirement: Diagnostics cannot grant authority or obstruct cleanup
Diagnostic errors and reentrant logging SHALL disable diagnostics without escaping
into game callbacks or changing action results. Diagnostic state MUST NOT arm,
reload, renew or preserve approvals, reset attempts, issue commands or delay release.

#### Scenario: Logger or diagnostic read fails
- **WHEN** a diagnostic sink, clock or game-state read fails or recursively invokes diagnostics
- **THEN** diagnostics stop and existing input release, disconnect and normal-exit invalidation still execute

#### Scenario: Expired approval or unexpected exit
- **WHEN** approval expires or an exit falls outside the existing approved restart exception
- **THEN** live actions remain unavailable with diagnostics either enabled or disabled and no additional restart is dispatched
