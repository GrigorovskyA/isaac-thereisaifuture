# Spec Delta

## ADDED Requirements

### Requirement: Bounded recovery from file sharing conflicts
Gate file I/O SHALL recover transient Windows errors 5/32 (including the CRT
EACCES equivalent) within at most 250 ms
and 26 attempts per operation, clipped to the existing handoff/global deadline.
Other failures MUST propagate without retry. Publication MUST remain atomic and
failed reads/removals MUST NOT authorize readiness or renew any deadline.

#### Scenario: Concurrent operator read
- **WHEN** a short operator read overlaps request replacement
- **THEN** replacement succeeds after the conflict clears within budget and readers see complete old or new records

#### Scenario: Persistent sharing conflict
- **WHEN** a conflict lasts through the bounded window
- **THEN** the operation stops with the original sharing failure, without deleting or partially overwriting the target

#### Scenario: Handoff deadline expires
- **WHEN** the remaining handoff/global time is shorter than the retry window
- **THEN** no retry proceeds after that deadline and no stale readiness resumes combat

### Requirement: Stop cleanup preserves the primary failure
Gate stop SHALL release input and enter stopped state even if request publication
or token removal fails. Secondary cleanup failures MUST be recorded without
replacing the primary failure or preventing environment/client cleanup.

#### Scenario: Stop publication is locked
- **WHEN** an initial or ongoing operation fails and the stopped request cannot be published
- **THEN** input is released, the original error remains observable, secondary errors and stop summary are recorded, and close still closes the backend

#### Scenario: Cleanup after budget expiry
- **WHEN** stop follows an expired deadline
- **THEN** cleanup attempts publication and removal once without waiting or retrying, and records any failure while preserving stopped state
