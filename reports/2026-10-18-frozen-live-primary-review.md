# Evidence: frozen-live-runner primary Windows review

- Date: 2026-10-18, Europe/Amsterdam.
- Baseline: 1788515 plus matching executor changes; errors.txt preserved.
- Task: frozen-live-runner-20261018-01, ready_for_review.
- Scope: offline runner, CLI integration, documentation and synthetic checks.
- Game/mod runtime: not exercised; existing installed files unchanged.
- Environment: existing Windows Python 3.12.14 and pinned dependencies.
- Scenario: fake peers/clocks and synthetic Lua room; no actual game connection.

## Results

| Requirement | Command/scenario | Exit | Status | Evidence |
|---|---|---|---|---|
| Windows quality gate | scripts/Check.ps1 | 0 | passed | 1329 tests, zero skips; Ruff, 95 formatted files, mypy 41 sources, pip consistency |
| Pinned strict validation | Included in Check.ps1 | 0 | passed | 27/27 |
| Runner acceptance | Actual source, CLI diff, tests and spec review | — | passed | Deadline, cap, reset, cleanup, identity invalidation and honest status cases |
| Real frozen-model pilot | Not started | — | not_run | Task 4.3 remains pending |

## Review

This is primary self-review, not independent review. The report's matching task
ID and actual allowed diff were checked. The new module reuses LiveClient and
make_live_env, does not replace the wire/reset implementation, and preserves
the existing CLI branches. Policy loading/compatibility checks precede listening;
reset/step use the shared deadline. The post-act deadline prevents an action
after inference crosses the budget. Final partial segments are retained, faults
produce failed results, and artifact changes invalidate results. The synthetic
Lua/socket case is not real-game acceptance. No new blocking finding was found.

The initial identity may be loaded before the run deadline starts; the deadline
is explicitly for listening and gameplay, not a bound on arbitrary model loading.
In-flight bounded I/O can finish after expiry. Physical manual input is not
detected; assistance labels are operator declarations and default to unknown.
Checkpoint action repeat is absent from old manifests: the runner records its
fixed repeat of 3, so compatibility with a different training repeat is not
attested. Room/build provenance is unknown when unavailable. These limits are
retained in the guide and do not establish comparable scenarios or learning.

## Continuation

Offline scope is accepted and executor authority closed. No archive until the
pending runtime gate is resolved. A future game pilot needs current slot/profile,
effective approval and a concrete budget. No approval was written/renewed, no
game launched/attached, no model evaluated in Isaac and no training started in
this review. Preserve raw logs, model binaries and approvals outside Git.
