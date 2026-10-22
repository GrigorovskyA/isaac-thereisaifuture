## ADDED Requirements

### Requirement: Deterministic bounded timing harness
The benchmark SHALL read all time from an injectable clock, MUST stop at the configured step or
duration bound, and MUST reject unbounded or out-of-range configurations.

#### Scenario: Fake clock timing
- **WHEN** a benchmark runs with a clock advancing a fixed tick per call
- **THEN** backend latency, encode cost and steps per second equal the exact expected values

#### Scenario: Duration bound
- **WHEN** the clock passes the maximum duration before the step bound
- **THEN** the run stops and reports the steps completed

#### Scenario: Invalid bounds
- **WHEN** action repeat, steps or duration are outside their allowed ranges
- **THEN** configuration construction raises an error

### Requirement: Host-independent report
The JSON report SHALL separate fields that depend only on configuration and seed from timing and
host information, and MUST label the backend and mark real-game throughput as blocked.

#### Scenario: Different clocks
- **WHEN** the same configuration runs under two different clocks
- **THEN** the deterministic sections are identical and the timing sections differ

### Requirement: Synthetic action-repeat comparison
The comparison MUST vary only action repeat, MUST label its results synthetic and MUST NOT require
CUDA, Docker or multiple game instances.

#### Scenario: Repeat comparison
- **WHEN** two action repeats are compared
- **THEN** each run reports its own game updates and the report states it is synthetic-only

### Requirement: Evidence-backed non-applying proposals
Configuration change proposals SHALL include the supporting measurements and a re-validation
caveat, MUST be marked not applied, and MUST be withheld unless throughput gains without
quality or failure-rate regression and with sufficient episodes.

#### Scenario: Clear win
- **WHEN** a candidate gains throughput with equal quality and no extra faults
- **THEN** a proposal with evidence and `applied` false is returned

#### Scenario: No clear win
- **WHEN** the gain is small, quality drops, faults increase or episodes are too few
- **THEN** no proposal is returned
