## MODIFIED Requirements

### Requirement: Finite budget and observable outcome
Without live training authority, the mode MUST allow at most three attempts within
ten minutes per mod load; reconnect SHALL NOT replenish these limits. With live
training authority, the approval `max_restarts` SHALL bound restarts, and the value
0 SHALL mean unlimited restarts for the pure training profile. Restart pacing
SHALL still apply. The mode SHALL log dispatch and confirm a fresh non-continued
game-start with increasing epoch within five seconds. Errors or missing
confirmation MUST disable further restarts for that mod load without retry.
Offline simulation MUST NOT be reported as game verification.

#### Scenario: Confirmed transition
- **WHEN** a dispatched restart produces a fresh game-start event
- **THEN** diagnostics identify the old and new epochs and snapshots expose the new epoch

#### Scenario: Unlimited pure approval
- **WHEN** the training approval has `max_restarts` 0 and many deaths occur
- **THEN** each confirmed death is restarted subject to pacing, without a count limit

#### Scenario: Uncertain result or exhausted budget
- **WHEN** dispatch fails, confirmation times out, or a finite budget is exhausted
- **THEN** further automatic restarts stop and diagnostics explain why
