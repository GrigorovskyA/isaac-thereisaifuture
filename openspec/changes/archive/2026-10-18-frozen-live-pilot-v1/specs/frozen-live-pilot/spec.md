## ADDED Requirements

### Requirement: Attach-only inference runner
The `eval-live` runner SHALL run exactly one explicitly selected policy, either a frozen checkpoint
named by its directory with a required expected config hash or the random baseline, over the
existing live transport and environment. It MUST NOT launch the game, learn, save checkpoints,
resume, follow the latest pointer, write approvals, force restarts or bypass the Lua live-loop
approval, and it SHALL require the manual `--confirmed-save-slot 2` confirmation.

#### Scenario: Frozen checkpoint is not trained or saved
- **WHEN** a frozen checkpoint is evaluated for several decisions
- **THEN** the model is never trained, nothing is saved and the normalizer statistics are unchanged

#### Scenario: Checkpoint without expected config hash
- **WHEN** the checkpoint policy is selected without an expected config hash
- **THEN** the CLI rejects the invocation before listening

### Requirement: Validation before listening
The runner SHALL reject non-finite, non-positive or over-cap step, minute and accept-timeout
budgets, a negative fault budget and an incompatible or unreadable checkpoint, and SHALL verify
the loaded artifact identity, before it opens the listening socket.

#### Scenario: Incompatible checkpoint
- **WHEN** the expected config hash differs from the checkpoint manifest
- **THEN** the run fails without listening and without creating a session log

#### Scenario: Non-finite budget
- **WHEN** minutes is NaN or infinite
- **THEN** the options are rejected before listening

### Requirement: One absolute deadline and decision cap
One monotonic deadline computed before listening SHALL bound accept, initial reset, paused waits,
steps and reconnects, and retries MUST NOT renew it. The runner MUST NOT send another action once
the decision cap or the deadline is reached, and SHALL count attempted and completed decisions
separately. Default caps are 2000 decisions, 6 minutes and zero tolerated infrastructure faults.

#### Scenario: Cap reached
- **WHEN** the configured number of decisions has been attempted
- **THEN** no further step is sent and the stop reason is `step_cap`

#### Scenario: Deadline during decision
- **WHEN** the deadline passes while the policy is choosing an action
- **THEN** the action is not sent and the stop reason is `deadline`

### Requirement: Policy state reset at every segment
The runner SHALL call the policy reset after every environment reset, including after a death
followed by the reconnect to the restarted run, a timeout and a fault-truncated step, so that no
recurrent state is reused across segments. Only encoded policy observations SHALL reach the policy.

#### Scenario: Death and reconnect
- **WHEN** a segment ends in death and the next segment starts on a new session
- **THEN** the policy was reset again before its first action in the new segment

### Requirement: Cleanup and identity on every exit path
The runner SHALL release input and close sockets on cap, deadline, interruption, fault, invalid
model output, identity failure, environment creation failure and ordinary exit, and SHALL re-verify
the checkpoint artifact hashes after the run; changed artifacts MUST mark the result invalid even if
gameplay already happened.

#### Scenario: Environment reset fails
- **WHEN** the initial reset raises
- **THEN** the listening socket is closed and a final summary with a failure status is logged

#### Scenario: Model replaced during the run
- **WHEN** the model file changes while the run is in progress
- **THEN** the final status is `invalid` and the exit code is non-zero

### Requirement: Private session logs
The runner SHALL write a private `live.jsonl` with the policy kind and identity, schema versions,
action repeat, every hello, segment summaries including the final partial segment, faults and a
final summary with stop reason, status and attempted/completed counts on every exit path, plus a
separate private `oracle.jsonl`. Unavailable game, room or build provenance SHALL be `unknown`.

#### Scenario: Final partial segment
- **WHEN** the run stops at the cap in the middle of a segment
- **THEN** that segment is logged as `stopped` with its completed steps

#### Scenario: Oracle separation
- **WHEN** approximate oracle events are derived during the run
- **THEN** they are written only to `oracle.jsonl` and never to `live.jsonl` or the policy

### Requirement: Honest outcomes
A fault or exception MUST NOT be reported as success; any recorded infrastructure fault SHALL
make the final status `failed` with a non-zero exit code.

#### Scenario: Tolerated fault
- **WHEN** a fault occurs within a nonzero fault budget and the run then reaches its cap
- **THEN** the final status is `failed` and the exit code is non-zero

### Requirement: Declared operator assistance
The runner SHALL accept an operator-assistance label `assisted`, `unassisted` or `unknown`
(default `unknown`) for the whole session and record it; it MUST NOT claim automatic detection of
physical input or mark segments autonomous without evidence.

#### Scenario: Default label
- **WHEN** no label is given
- **THEN** the session is recorded as `unknown`
