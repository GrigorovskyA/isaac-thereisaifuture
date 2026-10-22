# Evidence: episode-lifecycle / native-negotiation-02

- Date/time and timezone: 2026-10-17, Europe (+02:00)
- Git revision and dirty status: 0ddff56, dirty (uncommitted working tree, shared SMB copy)
- Change scope and acceptance criteria: task 3.1 only. `ObserverConfig.native_episode_steps`
  (default False, strict bool, incompatible with `safe_actions`, `entity_observations`,
  `restart_after_death`); hello requests base capabilities plus only `entity_action_v1`; no
  fallback; `EntitySnapshot` decoding in this mode. Revision 02 only strengthens tests and
  this report; `observer_client.py` is unchanged since revision 01.
- Game/mod/bridge versions: not applicable (simulated peers only).
- Python/package versions and configuration hash: not run on macOS.
- Scenario, split, seeds, budget, and stop conditions: not applicable.

## Results

| Check/requirement | Command/scenario | Exit code | Status | Evidence |
|---|---|---|---|---|
| Syntax | `ast.parse` on tests/test_native_negotiation.py | 0 | passed | macOS |
| Line length <= 100 | awk length scan on the test file | 0 | passed | no long lines |
| Combined hello and entity decode | `test_combined_negotiation_...` | 0 | passed | Windows targeted suite, 16 cases |
| Same-client reconnect (fresh session, counters reset) | `test_same_client_reconnect_...` | 0 | passed | Windows targeted suite, 16 cases |
| Old peer rejected, no fallback or state | `test_old_peer_is_rejected_...` | 0 | passed | Windows targeted suite, 16 cases |
| Missing nested frame rejected, peer closed | `test_missing_entity_frame_...` | 0 | passed | Windows targeted suite, 16 cases |
| Valid NativeOracleEvent / StepCompletion rejected, peer closed | `test_unsolicited_native_message_...` | 0 | passed | Windows targeted suite, 16 cases |
| Mode exclusion and bool-as-int | `test_native_mode_...`, `test_native_flag_...` | 0 | passed | Windows targeted suite, 16 cases |
| Legacy hello plus snapshot shape (default, safe_actions, restart, entity) | `test_legacy_modes_...` | 0 | passed | Windows targeted suite, 16 cases |
| pytest, Ruff, format, strict mypy, OpenSpec strict | `./scripts/Check.ps1` | - | not_run | macOS share lacks dependencies; orchestrator records Windows results |

Test notes: the `sim` fixture records peer errors and re-raises them in the test thread; every
peer thread is joined with a 3 s bound and asserted not alive in `finally`. Only
BrokenPipe/ConnectionReset/ConnectionAborted are tolerated as intentional negative closes.

## Real game

No real-game run took place. All peers are simulated localhost sockets; no Isaac, Lua, save,
or mod was touched.

## Limitations and continuation

- Nothing here proves native step execution, a native backend, or Lua support.
- Assumes `EntitySnapshot` rejects an active snapshot without `entity_frame` and that the
  base client rejects any non-snapshot record; Windows run confirms both.
- Self-review (not independent): diff limited to the three allowed files.
- Next action: orchestrator runs the primary Windows gates and records results here.

## Primary Windows verification and self-review

- Primary revision: 0ddff56 plus the reviewed negotiation diff, 2026-10-17,
  Europe/Amsterdam; Python 3.12.14, pytest 9.1.1. No dependencies changed.
- `.venv/Scripts/python.exe -m pytest tests/test_native_negotiation.py -q`:
  exit 0, 16 passed. This supersedes the first revision's 11-case result.
- `./scripts/Check.ps1`: exit 0, 590 passed, zero skips; Ruff, 71 formatted
  files, strict mypy (34 source files), pip consistency and OpenSpec 24/24 passed.
  Process-local PYTHONPATH selected the existing lua-test-runtime directory;
  ISAAC_JSON_LUA selected the installed resources/scripts/json.lua. TMP/TEMP
  selected ignored reports/local/check-native-protocol; no global settings changed.
- `./scripts/OpenSpec.ps1 validate --all --strict`: exit 0, 24/24.
- Self-review: task 3.1 matches its frozen design. Config flag is appended and
  strictly boolean; native mode is exclusive, old peers fail closed, nested state
  validates and same-listener reconnect resets counters with a new session.
  Valid unsolicited native event/completion messages fault rather than reaching
  the policy. Default and all legacy hello/state shapes are preserved.
- Executor revision 02 addressed missing same-client reconnect, actual legacy
  snapshot checks, valid unsolicited messages and surfaced thread errors.
- No CLI, command sender, Lua source, installed mod, save or action authority changed.
  There is no native GameBackend or runtime acceptance in this batch.
- Accepted offline task 3.1 only. Item 05 remains unfinished and unarchived;
  bounded native transport/filtering and unsupported-operation guards are next.
