# Evidence: durable-training-session

- Date: 2026-10-21, Europe/Amsterdam.
- Git base: 85240d3; implementation is the commit containing this report.
- Scope: readiness item 1, durable finite startup/deadline/status/owned cleanup.
- Runtime: Python 3.12, CPU torch 2.14.1+cpu; existing pinned dependencies.
- Game/mod/bridge versions: no new native run or deployment; existing source unchanged.
- No training/evaluation scenario executed, no approval granted, no save/model writes.

## Results

| Check | Command/scenario | Exit | Status | Evidence |
|---|---|---:|---|---|
| Initial runner contracts | pytest test_session_runner.py | 1 | failed | 27 assertions passed but shared Windows pytest-current cleanup raised WinError 5; retained as environment failure |
| Targeted contracts and existing live/training/gate | pytest tests/test_session_runner.py tests/test_training_manifest.py tests/test_live.py tests/test_combat_gate.py --basetemp reports/local/session-targeted-temp-3 -q | 0 | passed | 103 passed before final review regressions |
| Initial full gate | ./scripts/Check.ps1 | 1 | failed | 2079 passed, one old async test used simulated live clock and real trainer clock; shared deadline correctly stopped immediately |
| Async/shared clock regression | pytest tests/test_async_restart_training.py tests/test_session_runner.py tests/test_training_manifest.py tests/test_live.py tests/test_combat_gate.py --basetemp reports/local/session-regression-temp -q | 0 | passed | 137 passed; test now shares simulated trainer clock, retains all death/reconnect/unsaved/no-checkpoint assertions |
| Final full Windows gate | ./scripts/Check.ps1 | 0 | passed | 2084 passed, zero skipped, 45.64s; Ruff/126 formatted files/mypy 53 source files/pip clean; OpenSpec 41/41 |
| RL stack | ./scripts/Smoke-RL.ps1 | 0 | passed | 16 synthetic steps, CPU save/load/predict; Isaac integration false |
| CLI inspection | python -m isaac_threrisaifuture.session_runner --help | 0 | passed | Explicit required budgets/parent/paths, no launch |
| Diff review | git diff --check and separate self-review | 0 | passed | No save/config/reward/observation/model changes; unrelated errors.txt excluded |
| Native qualification | Separately declared five-minute Continue2 resume/stop pilot | — | not_run | Suspended training remains suspended; no native acceptance or archive |

Gate environment (local commands, not application configuration):
`PYTHONPATH=C:/Users/<user>/Documents/Codex/2026-10-17/work-on-isaac-threrisaifuture-in-the/work/lua-test-runtime`,
`ISAAC_JSON_LUA=C:/Program Files (x86)/Steam/steamapps/common/The Binding of Isaac Rebirth/resources/scripts/json.lua`,
`TEMP=TMP=D:/isaac/reports/local/session-final-gate-temp`.
Full local output: `reports/local/session-final-gate.txt` (excluded from Git).

## OpenSpec verification and separate self-review

Using change `durable-training-session` (spec-driven), reviewed against proposal,
design, both delta specs, tasks, implementation and behavior tests.

| Dimension | Assessment |
|---|---|
| Completeness | 4/5 tasks; native task 2.2 not verified because no new native qualification was requested |
| Correctness | All five added requirements have implementation and offline scenario coverage; native effects not verified |
| Coherence | Design and existing adapter patterns followed; no new dependencies, New Run fallback, policy/reward/schema changes or automatic relaunch |

Requirement mapping:

- Strict finite startup: `SessionPlan`, `NativeRuntime.preflight/identity/enter`,
  existing guarded menu and deployment checks. Missing/different parent, foreign
  approval, refused startup/focus and no takeover tested in test_session_runner.py;
  existing launcher/checkpoint tests cover deployment/schema/config mismatch.
- Single fixed deadline: `SessionClock.start/lease`, shared `LiveRunOptions` and
  trainer deadline. Fractional clock, delayed startup, real approval serialization,
  exact aligned lease window and insufficient remaining time tested.
- Durable status: `Progress`, `EventTail`, `supervise`. Combat/navigation/save
  phases, stale progress, verified checkpoint versus failed concurrent read,
  malformed telemetry, optional export failure and exact early-stop reason tested.
- Owned cleanup: `supervise` finally isolates each cleanup action; native adapter
  uses existing window/PID/path/time identity, normal WM_CLOSE and approval hash.
  Cancellation, timer stop, changed approval and close failure tested offline.
- External deadline/cancellation: live backend checks and trainer progress hook.
  Gate regressions retain oracle separation and no unsaved-rollout checkpoint.
  StopAwareGameLog checks cancellation inside the guarded menu polling path.

Self-review corrected module invocation, integral lease alignment, cancellation
precedence at expiry and completion classification. Stop evidence time, rather
than time spent in cleanup, determines whether the target window was reached.
Dedicated tests prevent cleanup delay from converting an early stop to completed
and prevent a deadline stop signal from being mislabeled user cancellation.

One critical archive blocker remains: native task 2.2. Real Steam/Continue2 startup,
compatible model update, manual/timer stop input release and actual owned-game,
lease and sleep-state cleanup are not verified by fixtures. Do not archive.
No remaining offline issues were found in this self-review; this is not an
independent review or gameplay-improvement claim.

## Preserved state and continuation

Read-only end check: no Isaac process or listener on 9528, no action approval.
Latest remains `7d53f55f-s20-t7424`; model SHA256
`799614daa61a2c5cb7d0c7adb1bac891845242e4b5179ab2abdf0e65f24f5134`.
Original migrated t6912 model SHA256 remains
`9b8e7eaa8aa89cc23debc82e99f26c365a24c617f63bbd6f5676b7ed350a22f4`.
Neither saved lineage was trained or rewritten in this task.

Next offline work is readiness item 2: explicit time-dominant navigation with
observed no-progress handling. Existing navigation caps are intentionally retained
in this change. Interrupted-save publication and comparable gameplay evaluation
remain items 3/4. A new native plan must qualify five minutes, then 15–30 minutes,
then one hour before a separately requested four-hour experiment. The previous
New Run authorization was not reused and no four-hour run was launched.
