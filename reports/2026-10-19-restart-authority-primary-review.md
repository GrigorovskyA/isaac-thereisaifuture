# Evidence: restart-authority-diagnostics primary review, feedback 1

- Task ID: restart-authority-diagnostics-20261018-01.
- Date and timezone: 2026-10-19, Europe/Amsterdam.
- Git baseline: 2c1595b; matching executor diff uncommitted; errors.txt preserved.
- Scope: source/report review and Windows offline verification only.
- Runtime: no game connection, deployment, authorization change or training.
- Python: 3.12.14 on Windows; existing Lua test runtime and installed json.lua.

## Results

| Check | Command/scenario | Exit code | Status | Evidence |
|---|---|---|---|---|
| Task identity | Compare subagent.md, agent-status.json and named report | 0 | passed | Matching task; ready_for_review at 2026-10-19T05:31:40Z |
| Windows quality gate | scripts/Check.ps1 | 1 | failed | 1388 passed, 10 failed, zero skips; lint/98 formatting/mypy 42 sources passed before pytest |
| Strict specs | scripts/OpenSpec.ps1 validate --all --strict | 0 | passed | 29 passed, zero failed |
| Semantic parity investigation | Existing run helper, six orders and four injected-fault variants; parse both JSON transcripts, fix both wall clocks | 0 | passed | 10/10 semantic comparisons agree; message and list order retained |
| Delayed second exit | Single restart, live reconnect, then second exit/start | 0 for inspected facts | passed | One dispatch; approval_drop has live=1, awaiting=na, approval=1; next hello auth=none; held input absent |
| Nonliteral opt-in | Replace diagnostic flag with string true and number 1 in test-only source | 0 | passed | 2/2 emit no lifecycle records |
| Real-game root cause | New native lifecycle capture | N/A | not_run | No runtime work authorized/performed by this review |

## Blocking finding

The six test_enabled_and_disabled_runs_are_observably_identical cases and four
test_sink_and_clock_faults_disable_only_diagnostics cases compare raw JSON lines
in first_outgoing/outgoing. Lua object serialization field order differs across
instances on this Windows runtime; decoded objects agree. JSON object ordering
is not part of this wire contract. All ten failures reproduce in the full gate.

Compare decoded messages for these two fields while retaining record count/order,
array ordering, keys, values, types and all other transcript checks. Do not sort
messages, ignore fields or weaken held-input/commands/cleanup assertions. Freeze
the approval and Lua wall clocks consistently to avoid a second-boundary race.
Keep meaningful discrimination: demonstrate that changed payload values or
message ordering still fail parity, while object-key permutation does not.

The first ad-hoc delayed-exit comparison also failed when comparing raw lines;
inspection confirmed its first differing objects were semantically identical.
This is a test portability failure, not evidence that diagnostics changed actions.

## Coverage addition

Add the delayed second-exit scenario above as a persistent production-Lua test.
The native failure log showed a confirmed restart and a newly armed session
before the second exit. The executor's current multi-event schedule performs
both exits inside the original dispatch before reconnect, giving live=0 at
the second exit; the delayed case exercises live=1, awaiting=nil. Both should
record the actual invalidation branch without changing existing behavior.

## Self-review and outcome

This is primary review, not independent review. No production guard change was
found in the inspected diff. Bounded default-off diagnostics and simulated
candidate sequences are useful, but Windows acceptance fails until the tests
are corrected. No implementation acceptance, commit/push or archive; task 2.1
and all runtime tasks remain unchecked. Existing changes and errors.txt retained.

Feedback 1 is recorded in subagent.md with the same task ID and allowed writes.
The executor must append a feedback-1 response and publish fresh matching
ready_for_review status. Historical ready status alone cannot complete re-review.

## Feedback 1 re-review: offline accepted

Fresh matching status at 2026-10-19T05:37:52Z and the named feedback-1 response
were read before reviewing. The test change now decodes complete JSON lines
in order, retains the partial tail and type-tags all nested values. Its
discrimination cases distinguish changed values, types, missing keys, arrays,
message order and partial tails; object key permutation alone is ignored.
Both approval creation and Lua os.time use a fixed wall second in parity runs.
The new delayed test includes a live rearm and held action before the second
exit/start, checks its release and records the actual drop branch. Production
authorization, serialization and restart guards are unchanged by feedback.

| Check | Command/scenario | Exit code | Status | Evidence |
|---|---|---|---|---|
| Windows quality gate | scripts/Check.ps1 | 0 | passed | 1401 passed in 27.51 s, zero skips; Ruff, 98 formatted files, mypy 42 sources, pip consistency |
| All strict specs | scripts/OpenSpec.ps1 validate --all --strict, invoked by Check.ps1 | 0 | passed | 29 passed, zero failed |
| Prior ten failures | Full gate includes six order parity and four fault parity cases | 0 | passed | All pass with full-message semantics and unchanged other assertions |
| Delayed exit and discrimination | Three new persistent tests in test_lua_restart_diagnostics.py | 0 | passed | Held input release, one dispatch, live=1/awaiting=na, auth=none; parity and comparator discrimination |
| Real-game capture and root cause | Tasks 3.1-3.3 | N/A | not_run | No launch, connection, deployment, approval write or training in this review |

### OpenSpec verification scorecard

| Dimension | Status |
|---|---|
| Completeness | 8/11 tasks complete; three runtime tasks unfinished |
| Correctness | All three ADDED requirements mapped to production Lua and offline scenarios; real-game behavior not verified because no capture occurred |
| Coherence | Separate default-off rare-event state, guarded logging and fixed budgets follow design; existing action/restart predicates and cleanup retained |

Mapping: bounded lifecycle diagnostics -> life_event and count/time/line tests;
correlated authority facts -> life_facts, callback/branch instrumentation and
single/additional/delayed/hello-refusal scenarios; authority/cleanup isolation ->
guarded diagnostic reads/sinks, fault/reentrancy tests and enabled/disabled parity.
The retained initial rejection above is historical; both offline findings close.

Three incomplete tasks (3.1-3.3) block archive. Runtime scenario verification,
deployment and physical cleanup are not verified in this review because none
was performed. No additional offline warning or suggestion was found. This is
primary verification, not independent review. Accept and commit the OFFLINE
implementation only; do not archive or claim an engine root cause or learning
improvement. Executor write authority closes; no successor or monitor is started.
