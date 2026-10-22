# Evidence: restart-authority-diagnostics planning

- Date/time and timezone: 2026-10-18, Europe/Amsterdam.
- Git revision and dirty status: 1d2d3f3; unrelated untracked errors.txt preserved.
- Change scope and acceptance criteria: offline investigation and proposal,
  specifications, design and tasks; implementation and runtime acceptance pending.
- Game/mod/bridge versions: preserved failure uses observer 0.5.0-dev; no new game
  connection, launch, control, deployment or authorization change in this work.
- Python/package versions: quality gate uses Python 3.12.14 and existing lock;
  no dependency or training configuration change.
- Scenario, split, seeds, budget and stop conditions: read preserved failure
  evidence and source/tests only; no learning, checkpoint changes or new episodes.

## Results

| Check/requirement | Command/scenario | Exit code | Status | Evidence |
|---|---|---|---|---|
| Failure sequence | Read preserved native log and existing experiment report | 0 | passed | One dispatch, first exit, new start, confirmation/rearm, second exit/new start, capability refusal |
| Existing test model | Inspect tests/test_lua_observer.py and tests/test_lua_live_loop.py | 0 | passed | AUTO_START models synchronous exit then start; no second automatic exit/start in the accepted restart case |
| Plan validation | scripts/OpenSpec.ps1 validate restart-authority-diagnostics --strict | 0 | passed | Complete proposal/design/delta/tasks, no implementation tasks checked |
| Windows baseline gate | scripts/Check.ps1 | 0 | passed | 1362 tests, zero skips; Ruff, 97 formatted files, mypy 42 sources, pip consistency |
| All OpenSpec items | scripts/OpenSpec.ps1 validate --all --strict (inside Check.ps1) | 0 | passed | 29 passed, zero failed |
| Diagnostic implementation | Planned lifecycle records and ordering scenarios | N/A | not_run | No source/test changes |
| Native cause identification | Ordered callback/authority capture | N/A | blocked | Existing native log lacks callback-entry and approval-decision facts |

## Source findings and limits

1. There is one restart command call site. It clears pending and sets awaiting
   before dispatch. A second native start alone does not prove a second command.
2. PRE_GAME_EXIT preserves approval only while live.on and awaiting are present.
   close clears live.on, and POST_GAME_STARTED consumes awaiting. Extra exits or
   reordered callbacks can therefore remove approval under existing rules.
   This is a candidate mechanism, not a reproduction of the actual engine trace.
3. Hello advertises live actions only while action_authorized returns true. Its
   generic Too many capabilities message does not distinguish missing approval,
   inactive game, expired approval or action lease from other validation failures.
4. The operator explicitly denied menu/New Run/Continue activity after death.
   The second start must not be attributed to manual input. No conflicting mod
   or duplicate dispatcher has been established.
5. The existing short callback trace cannot reliably cover the operator handoff.
   Planned lifecycle diagnostics use rare events and separate hard limits.

## Real game

No new real-game run occurred. The failed session remains preserved privately at
runs/live/sessions/20261018-211337-172319, including its native-log copy; no raw
logs, approvals, seeds, saves or models are added to Git. Prior operator-confirmed
cleanup remains documented in the original experiment report.

## RL evaluation

Not applicable to planning. The failed attempt did not complete an update; t4096
remains the previous checkpoint. No new model or improvement is claimed here.

## Limitations and continuation

Primary self-review, not independent review: the plan adds diagnostic requirements
to the existing live-training-loop capability and leaves its approval/restart
requirements intact. Required runtime evidence and all implementation tasks stay
unchecked; the change is unarchived. Do not reload approvals or widen guards as
a speculative fix. Next apply this plan, verify offline, then request the needed
closed-game deployment and separately budgeted operator-present capture.

The OpenSpec Propose skill used for this plan requires: "Do not start implementation
in the same response" and "Wait for a new user request after the artifacts are
presented". This planning boundary, rather than a game permission failure, is why
this turn leaves code unchanged. No file executor task or heartbeat was activated.
