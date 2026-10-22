# Time-budget training: offline evidence

Date2026-10-21,Europe/Amsterdam. User requested removing practical death/step
stops for long runs after the native pilot stalled at its two-restart cap.
Change time-budget-training1/2,unarchived; native sustained acceptance not_run.

## Change

`session_runner --time-budget-only` derives1billion cumulative steps and5000
restarts,forces time-dominant navigation and records nonbinding_schema_sentinels.
Explicit step/restart CLI flags conflict with this mode. Diagnostics still require
both counts. Supported duration60s..4h; larger windows fail rather than letting
the existing5000 approval schema ceiling bind. Native4second restart pacing
bounds possible restarts below3601 in4h; even30 decisions/second is far below the
step sentinel from t7680. These finite schema values are not literal infinity.

Preflight rejects a smaller config total-timestep or shorter wall ceiling before
approval/game. No hidden cap migration,model initialization or learning/reward/
observation change. Fixed deadline,resource/lineage/focus/transport,no-progress,
zero-infrastructure-fault and owned cleanup guards remain. Existing conservative-v2
overnight config stays byte-identical. No new game or experiment was launched.

## Bounded checks

Base HEAD416e4b2ac9972341932b3a92e41c3474f9a7364a,with reviewed uncommitted
menu replacement and time-budget source. One fresh gpt-6-luna/high worker per
assignment; commands only,no source/test/config edits,installs,Git,runtime,
approvals,nested agents or retries. Synthetic test-temp writes allowed only in
named output. Primary retains implementation/acceptance.

Final sole command:
`.venv/Scripts/python.exe reports/local/run_time_budget_checks_2.py`.
Private exact plan: reports/local/time-budget-checks-plan-2.json.
Start-before1792570536.574205,absolute stop-by1792570776.574205,240s global,
512MiB output/temp,zero native decisions/deaths/restarts/faults/retries. Only owned
offline child trees could be terminated on caps. PYTHONPATH used existing Lua test
runtime under C:/Users/<user>/Documents/Codex/2026-10-17/work-on-isaac-threrisaifuture-in-the/work/lua-test-runtime;
ISAAC_JSON_LUA used installed game resources/scripts/json.lua; TEMP/TMP were
D:/isaac/reports/local/time-budget-checks-2/temp. No environment installation.

| Sequential command | Exit | Result |
|---|---|---|
| `.venv/Scripts/python.exe -m ruff check src tests scripts/smoke_rl.py` | 0 | Passed |
| `.venv/Scripts/python.exe -m mypy` | 0 | 55 source files,no issues |
| `.venv/Scripts/python.exe -m pytest tests/test_menu_entry.py tests/test_session_runner.py -q` | 0 | 90 passed,zero failed/skipped |
| `pwsh.exe -NoProfile -File D:/isaac/scripts/Check.ps1` | 0 | 2190 passed,zero failed/skipped;131 formatted;pip consistent;OpenSpec46/46 |

Runtime57.36s,peak94728320 bytes. Logs/result:reports/local/time-budget-checks-2/
(lint/types/targeted/gate.txt,result.json). Primary independently rehashed406
frozen files with zero mismatches,confirmed HEAD and actual logs/exits before
final documentation/task edits; tested production source/tests stayed unchanged.
Earlier snapshot:lint/mypy passed,targeted86 passed/4 failed,full gate not_run.
The actual approval-writer test omitted its fake observer-mod directory. Primary
verified406 unchanged hashes,created the fixture directory and kept production
approval safety checks unchanged. No native approval was written by offline tests.

## OpenSpec verification and self-review

| Dimension | Assessment |
|---|---|
| Completeness | 1/2 tasks; native sustained task2.1 not verified |
| Correctness | 1/1 added requirement,2 scenarios covered offline; actual long-mode gameplay not verified |
| Coherence | Explicit SessionPlan/CLI mode,strict preflight,existing approval/deadline/cleanup design retained |

SessionPlan/main implement count selection/contradiction checks,NativeRuntime
preflight rejects hidden config limits,and plan.json retains mode and numbers.
Tests exercise actual approval serialization and pacing/rate nonbinding bounds
at5min/30min/1h/4h,conflicting/unsupported mode/config rejection before identity,
approval or process creation,and CLI execution through a mocked supervisor.
Existing supervisor deadline/stop/cleanup regressions passed. This is primary
self-review,not independent review. Zero offline warnings/suggestions. Critical
archive blocker: native several-death continuation with further saved updates and
timer/owned cleanup in this new mode; no fresh finite experiment was executed.

The preceding native pilot is reported separately in
2026-10-21-thirty-minute-qualification-results.md: t7424->t7680,256 saved steps,
62 unsaved,three deaths/two restarts,35.75s combat in a five-minute timer window.
It was not30minutes of learning. No improved-play claim. Latest t7680 and immutable
t7424/t6912 remain intact. No active game/listener/approval after primary readback.
Next: a new recorded finite time-budget experiment from t7680,with game-entry and
any replacement authorization explicit; do not reopen old assignments automatically.
