## ADDED Requirements

### Requirement: Fail-closed eligible campaign runs
The campaign controller SHALL evaluate eligibility before each run and after it, and MUST stop
without starting a run, or without ledgering its evidence, when eligibility is denied or unknown.

#### Scenario: Ineligible before a run
- **WHEN** the eligibility evidence is denied before a run
- **THEN** no run is started, the denial is recorded and the stop reason is ineligible

#### Scenario: Eligibility lost during a run
- **WHEN** eligibility is denied after the run returns
- **THEN** the run's evidence is not appended to the ledger and the campaign stops

### Requirement: Observed evidence only
The controller MUST append to the ledger only goals reported with source observed_in_game and SHALL
stop on goals absent from the unlock graph.

#### Scenario: Non-observed source
- **WHEN** a run reports evidence from manual_note or inferred
- **THEN** the ledger stays unchanged

#### Scenario: Unknown goal
- **WHEN** a run reports a goal not in the graph
- **THEN** the campaign stops with reason invalid_report

### Requirement: Bounded and resumable campaign
The controller SHALL enforce max_runs across resumes and max_wall_seconds per call with an injected
clock, SHALL persist its state, and MUST NOT silently restart from a corrupt or interrupted state.

#### Scenario: Budget exhausted across resume
- **WHEN** a resumed campaign has already used max_runs runs
- **THEN** it stops with max_runs without calling run_once

#### Scenario: Corrupt state
- **WHEN** the state file is malformed
- **THEN** construction raises CampaignStateError

#### Scenario: Interrupted run
- **WHEN** the state shows a run in flight
- **THEN** it is counted as an interrupted run and not replayed

### Requirement: Dead God verification
The verification SHALL report verified only if the ledger verifies, contains observed_in_game
evidence of the target, every observed event belongs to a run whose eligibility audits were all
allowed, and no run was interrupted; otherwise it MUST report unverified or blocked, and SHALL
count autonomous and user-assisted runs separately.

#### Scenario: Manual note of the target
- **WHEN** the ledger has only a manual_note for the target
- **THEN** the status is unverified

#### Scenario: Missing allowed audit
- **WHEN** a run behind the target evidence has a denied or absent audit
- **THEN** the status is unverified

#### Scenario: Tampered ledger
- **WHEN** the ledger fails hash-chain verification
- **THEN** the status is blocked
