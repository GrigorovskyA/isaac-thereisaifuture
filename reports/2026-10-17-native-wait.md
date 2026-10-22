# Evidence: episode-lifecycle / native-wait-01

- Date/time and timezone: 2026-10-17, Europe (+02:00)
- Git revision and dirty status: bb4105a base, dirty (uncommitted working tree, shared SMB copy)
- Change scope and acceptance criteria: tasks 3.4/3.5 only. `NativeStepClient` in
  `native_client.py`: explicit `native_episode_steps=True` required; `receive_active()` with one
  monotonic `message_timeout` deadline per call (checked each iteration and before return);
  paused/unavailable snapshots skipped; active frame must strictly increase; first active
  snapshot fixes epoch/room, a later crossing faults; failures close the peer and raise
  `EpisodeFault` with the cause kept; `release()` is idempotent; `start_episode`, `reset`, `step`
  raise `UnsupportedNativeOperation` after closing the peer and send no bytes.
- Game/mod/bridge versions: not applicable (simulated peers only).
- Python/package versions and configuration hash: not run on macOS.
- Scenario, split, seeds, budget, and stop conditions: not applicable.

## Results

| Check/requirement | Command/scenario | Exit code | Status | Evidence |
|---|---|---|---|---|
| Syntax | `ast.parse` on both new files | 0 | passed | macOS |
| Line length <= 100 | awk scan on both new files | 0 | passed | no long lines |
| Pause/unavailable skipped, active resumes | `test_paused_and_unavailable_...` | 0 | passed | Windows targeted suite, 16 cases |
| Absolute deadline under frequent pause traffic | `test_absolute_deadline_...` | 0 | passed | Windows targeted suite, 16 cases |
| Stale/equal active frame rejected | `test_active_frame_must_strictly_advance` | 0 | passed | Windows targeted suite, 16 cases |
| Epoch/room crossing faults | `test_epoch_or_room_crossing_...` | 0 | passed | Windows targeted suite, 16 cases |
| Reconnect clears active state (same listener) | `test_first_active_may_be_any_epoch_...` | 0 | passed | Windows targeted suite, 16 cases |
| Malformed, disconnect, release idempotence | `test_malformed_...`, `test_disconnect_...`, `test_release_...` | 0 | passed | Windows targeted suite, 16 cases |
| Unsupported ops: EOF, zero command bytes | `test_unsupported_operations_...` | 0 | passed | Windows targeted suite, 16 cases |
| pytest, Ruff, format, strict mypy, OpenSpec strict | `./scripts/Check.ps1` | - | not_run | macOS share lacks dependencies; orchestrator records Windows results |

Test notes: peers reuse `SimulatedPeers` (errors re-raised in the test thread, 3 s bounded join,
asserted not alive). The flood peer stops after 2 s at most.

## Real game

No real-game run took place. All peers are simulated localhost sockets; no Isaac, Lua, save or
mod was touched.

## Limitations and continuation

- Not physical native step execution; no command is ever sent; no GameBackend or outcome
  inference. Server-side disconnect/deadline cleanup for the new mode remains unverified.
- The deadline test uses wall-clock bounds (0.4 s <= elapsed < 1.5 s) and may need loosening on
  a loaded Windows host.
- `test_unsupported_operations_*` runs the same assertions for all three names; the `peer` EOF
  check proves zero bytes only through the peer thread's `recv == b""` assertion.
- Self-review (not independent): diff limited to the four allowed files.
- Next action: orchestrator runs the primary Windows gates and records results here.

## Primary Windows verification and self-review

- Reviewed at bb4105a plus the three new executor artifacts; Python 3.12.14,
  pytest 9.1.1, Europe/Amsterdam, 2026-10-17. Dependencies unchanged.
- `.venv/Scripts/python.exe -m pytest tests/test_native_client.py -q`: exit 0,
  16 passed. Deadline flood, pause/unavailable resume, stale active/context faults,
  reconnect and EOF/no-command unsupported-operation checks all passed.
- `./scripts/Check.ps1`: exit 0, 606 passed, zero skips, Ruff, 73 formatted
  files, strict mypy (35 source files), pip consistency, OpenSpec strict 24/24.
  Process-local PYTHONPATH used the existing lua-test-runtime directory and
  ISAAC_JSON_LUA the installed resources/scripts/json.lua; TMP/TEMP selected
  ignored reports/local/check-native-protocol. No global settings changed.
- Self-review: one deadline is checked before each bounded read and before
  returning active state; buffered pause lines cannot renew the timeout.
  Existing sequence/session/update checks remain, active frames strictly advance,
  epoch/room crossing faults and close/reconnect clears fixed-size active state.
  BaseException closes the peer; infrastructure errors retain their cause.
  Unsupported operations close without writing; release is idempotent.
- Task 3.4 and task 3.5 accepted offline. General start/reset and physical step
  execution remain unsupported. No installed Lua, save, Cloud or runtime authority
  changed. Native disconnect cleanup still needs real integration evidence.
- Next: inspect current Lua callback/action/export paths and freeze bounded native
  completion/event ordering before assigning implementation. Item 05 stays open.
