# Evidence: asynchronous restart training primary review, feedback 1

- Task ID: async-restart-training-regression-20261019-01.
- Date: 2026-10-19, Europe/Amsterdam.
- Baseline: 9d14744; executor test/doc/report diff uncommitted; errors.txt preserved.
- Trigger: fresh matching ready_for_review at 2026-10-19T06:37:29Z.
- Monitor isaac-remote-handoff paused before review; no runtime actions performed.
- Scope: offline source/report inspection, Windows gate and isolated IPC reproduction.

## Results

| Check | Command/scenario | Exit code | Status | Evidence |
|---|---|---|---|---|
| Task/status identity | subagent.md, agent-status.json, named report | 0 | passed | Matching fresh task |
| Windows quality gate | scripts/Check.ps1 | 1 | failed | 1431 passed, 1 failed, zero skips; Ruff/99 formatting/mypy 42 sources passed |
| Strict validation | scripts/OpenSpec.ps1 validate --all --strict | 0 | passed | 29 passed, zero failed |
| Isolated Windows IPC | Production _write_atomic while request.json is open for reading in a disposable reports/local directory | 0 | passed | WinError 5 reproduced; identical write succeeds after reader closes |
| Complete Lua/socket/gate/learner chain | Inspect Stage 3 fixtures and training factory | N/A | failed | Learner uses AsyncWorld; loop_game is exercised in a separate non-learning test |
| Real game, deployment, approval, training | Not attempted | N/A | not_run | Monitor/task grants offline work only |

## Finding 1: Windows IPC replacement fails during overlapping read

The Windows gate fails in
test_loopback_async_restart_through_the_real_gate_pipeline during env.reset.
ScriptedOperator.request reads request.json while production _write_atomic uses
os.replace(request.json.tmp, request.json). The replace raises PermissionError,
WinError 5; reset's exception cleanup then invokes _stop, which attempts the
same failing replacement and masks the first error. This is not the historical
pytest-directory cleanup junction problem and must not be bypassed by elevation.

Minimal isolated reproduction used the existing production function, no game:
create a disposable request.json; keep p.open('rb') active; call _write_atomic;
observe winerror=5; close reader; identical _write_atomic succeeds. The integration
failure has an ordinary short concurrent reader, establishing relevance to the
operator's real file channel. The reproduction is a Windows sharing race; it
does not establish that every read causes a failure or explain the old double start.

Do not add retry-to-pass to tests, disable the operator, serialize away the real
overlap, widen runtime deadlines or weaken cleanup checks. A production remedy
requires scope outside this tests-only executor assignment. Preserve a small
reproducer and clearly mark dependent integration acceptance blocked. Scope and
design for a bounded IPC solution belong to a separate primary decision.

## Finding 2: combined learner integration not delivered

The task explicitly requires real CPU RecurrentPPO on top of the production Lua,
loopback LiveClient, LiveBackend and CombatGateEnv harness. Instead,
test_tiny_recurrent_ppo_spans_an_async_death_and_resumes_with_lineage constructs
async_factory -> AsyncWorld (a scripted World client), while
test_loopback_async_restart_through_the_real_gate_pipeline tests the real Lua
bridge separately. Both are useful component tests, but together they do not
prove a rollout/checkpoint across the complete assigned chain.

Keep these tests and add the missing combined test within allowed paths, or mark
it blocked with the exact cause. Do not declare Stage 3 complete. Instrument
actual policy/recurrent calls, normalization and updates through handoff waits;
command-count equality alone is not direct evidence of no policy calls while
waiting. Retain parent/reload/partial-rollout assertions and disposable models.
Use guaranteed env/client/thread cleanup, including failure paths and bounded
joins with explicit thread-termination checks. No production or real-game access.

## Evidence corrections and outcome

The report claims finished 06:40Z although the ready status was published at
06:37:29Z and this review started before 06:40Z. Correct the timestamp to actual
evidence; do not infer completion time. The real two-start failure remains unknown.

Primary review, not independent review: not accepted; no implementation commit,
push, archive, real experiment, approval or successor assignment. Monitor stays
paused. Same task's feedback 1 identifies the IPC blocker and missing coupled
learner evidence. Allowed executor writes remain test/documentation/status only.
Further runtime preparation and a production IPC fix need a separate decision.

## Feedback 1 follow-up inspection

Fresh matching needs_input status at 2026-10-19T06:56:30Z and feedback-1 report
read. The executor added the coupled production-Lua/socket/gate/CPU learner test,
direct policy/value/normalizer/update instrumentation, checkpoint/resume lineage
and a coupled interrupted-rollout test. The original component tests remain.
Production files are unchanged. A Windows-only strict xfail marks the isolated
IPC reproducer; that is an expected failure, not acceptance or a passed check.

Primary reran the complete new test file on Windows, with existing Lua runtime,
installed json.lua and the documented private temporary directory:

`python -m pytest -q tests/test_async_restart_training.py` -> exit 1,
31 passed, 2 failed, 1 xfailed in 12.00 seconds. The two failures are the original
loopback test and the new coupled CPU learner, both at production _write_atomic
with WinError 5. The interrupted coupled test passed in this invocation, which
does not eliminate the concurrent replacement race.

The missing coupled learner coverage is now implemented and inspected, but its
Windows acceptance is BLOCKED by the reproduced IPC defect. No repeated full
quality gate is warranted before that production blocker is addressed. No
commit/push or runtime work. Monitor remains paused. Executor asks for bounded
production IPC scope; current assignment authorizes only tests/documentation.

Cleanup review note for the next edit: thread joins are now in harness finally,
but the `assert not alive` and thread-error assertions sit after the context's
with block and can be bypassed when the test body raises. Keep termination checks
inside guaranteed cleanup while preserving/chaining the primary test failure.

## Primary Windows remediation and acceptance

The user explicitly asked the primary Windows agent to implement the required
remedy instead of assigning production writes to the executor. Executor writes
were closed. OpenSpec windows-gate-ipc defines bounded sharing recovery and
failure cleanup; reports/2026-10-19-windows-gate-ipc.md contains implementation
and OS-level evidence. The failed/blocked reviews above remain historical.

Final scripts/Check.ps1 exit 0: 1451 passed in 42.85 seconds, zero skips/xfails,
Ruff, 100 formatted files, mypy 42 sources, pip consistency, strict OpenSpec
30/30. Both formerly failing loopback/coupled CPU learner tests now pass, and
the strict xfail is replaced by asserted transient success/persistent bounded
failure. Harness termination assertions run in finally. The full delivered
four-stage regression coverage is accepted OFFLINE after primary remediation.

No real game or real training took place. No historical failed episode is
discarded, no model improvement is claimed and the original two-start cause is
still unknown. Monitor remains paused, no successor task or runtime authority
is created, and the draft training recheck requires a separate operator decision.
