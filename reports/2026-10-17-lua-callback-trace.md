# Evidence: lua-callback-trace-01

- Date/time and timezone: 2026-10-17, Mac executor (offline authoring only)
- Git revision and dirty status: working tree on top of d4671e1, uncommitted
- Change scope and acceptance criteria: instrumentation only. Bounded opt-in callback
  trace in `mod/observer/main.lua` per `episode-lifecycle` design ("bounded opt-in
  callback trace") and spec "Bounded callback diagnostics".
- Game/mod/bridge versions: observer source 0.4.1-dev; the installed observer remains 0.4.0
  and was not touched.
- Python/package versions and configuration hash: not applicable (no Python dependencies on
  the Mac).
- Scenario, split, seeds, budget, and stop conditions: not applicable.

## Behavior implemented

- `Config.callback_trace = false` by default; only the literal `true` enables it.
- The window starts only on the first accepted authorized `action` command. Hello,
  heartbeat, release, and rejected commands never start it.
- Hard bounds: 512 write attempts (the last one is reserved for a `stop` record), 10000 ms,
  300 characters per line.
- Records carry id, event, time_ms, frame, update, session, epoch, room, and action sequence.
  Input records carry hook, button, and returned value; `MC_INPUT_ACTION` returns the
  original result unchanged.
- Every write is wrapped in `pcall`; any failure ends the trace without affecting inputs,
  release, or cleanup.
- Normal hold release and room transitions are traced and do not end the window; it ends
  only on disconnect/close, game exit, the record or time budget, or a logger failure.
  A reconnect cannot renew it.
- Trace data is log-only and never enters wire messages.
- `mod_version` in `hello_ack` and in notes changed to `0.4.1-dev` (metadata, not behavior).

## Results

| Check/requirement | Command/scenario | Exit code | Status | Evidence |
|---|---|---|---|---|
| Lua syntax | `luac -p mod/observer/main.lua` | 0 | passed | Mac luac |
| Python syntax | `ast.parse` on both Lua test files | 0 | passed | Mac python3 |
| Line length of new lines | scan for >100 characters | 0 | passed | the only long line, `main.lua:436`, predates this change |
| Lua stub tests (Windows, revision 01) | targeted pytest of the three Lua test files | - | failed | 128 passed, 1 failed: `test_reconnect_cannot_renew_the_window` expected held input after a room transition (test bug; transition correctly releases) |
| Lua stub tests (revision 02) | same command | - | not_run | pending re-run on Windows; adds DebugString success/failure tests |
| ruff/format/strict mypy (revision 01) | Windows | - | passed | reported by orchestrator |
| Final gates (revision 02) | `./scripts/Check.ps1` | - | not_run | pending on Windows |
| Task 4 probes | in-game | - | not_run | requires authorized game run |

## Real game

Not run. The trace is untested in Isaac; the installed observer was not changed.

## Limitations and continuation

- Revision 02 tests have not been executed. Default stubs lack `Isaac.DebugString`, so most
  tests use the `print` fallback; two tests install a DebugString logger (success and
  trace-only failure).
- The test file overrides `test_lua_observer.ROOT` through monkeypatch for the literal-`true`
  test; adjust if the helper resolves the source differently.
- Next action: run the Lua tests and `Check.ps1` on Windows, then deploy 0.4.1-dev under
  explicit authorization for the Task 4 probes.


## Primary Windows verification and self-review

- Reviewed at 96430ac plus the batch, 2026-10-17 Europe/Amsterdam; Python
  3.12.14, pytest 9.1.1. Dependencies unchanged.
- Targeted `.venv/Scripts/python.exe -m pytest tests/test_lua_callback_trace.py
  tests/test_lua_observer.py tests/test_lua_actions.py -q`: exit 0, 131 passed
  after revision 02 (17 trace cases plus 114 existing observer/action cases).
- `./scripts/Check.ps1`: exit 0, 746 passed, zero skips; Ruff, 77 formatted
  files, strict mypy (36 source files), pip consistency and OpenSpec strict 24/24.
  Existing process-local Lua runtime/json.lua and ignored temp directory reused.
- Self-review: default false and literal-true gate, start only after validated
  authorized action, fixed-size state, 512 attempts including final stop, ten-second
  window, 300-character clipping, no restart on reconnect. Trace logger failures
  disable diagnostics; source input values are preserved. No wire/policy fields,
  combined capability or relaxed input/restart limits were introduced.
- DebugString success and trace-only failure paths passed, as did print fallback.
  The initial failed transition test was corrected, preserving room-release rules.
- Source hashes: main.lua
  669918a74910fdbd7c34cb0caf8b3649e29c5836510b688e6d885ff83cb21634;
  metadata.xml a066751aa5bc96dba8be581ad712d61e47e63fa8fdd3c331c2524036fca12131.
- Installed 0.4.0 hashes remain the accepted d4d406... and 3a7749... artifacts
  (full hashes in item-04 evidence). Source and installed versions now intentionally
  differ; source trace is default-off. No game file was written or process stopped.
- A separate ignored reports/local/callback-trace-0.4.1-dev diagnostic bundle
  enables only callback_trace for a later reviewed bounded probe, with hashes in
  its local manifest. It is prepared, not deployed. Release source remains false.
- Real task-4 probes remain not_run. isaac-ng PID 39624 was running at preparation;
  manual normal exit is required before replacing the installed mod. Do not
  interrupt the run. Future launch/save selection stay manual, and a fresh slot/
  epoch/current-instance check is required before bounded actions. Ordinary-profile
  bounded-action permission is standing; repeated training remains unauthorized.
- This accepts offline instrumentation only, not Lua native step/event export or
  exact input completion. Task 3.6 and runtime acceptance stay unfinished.
