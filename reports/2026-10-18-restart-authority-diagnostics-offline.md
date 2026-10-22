# Evidence: restart-authority-diagnostics (offline implementation)

- Task ID: `restart-authority-diagnostics-20261018-01` (external macOS executor).
- Date/time and timezone: 2026-10-19, UTC.
- Git revision and dirty status: baseline HEAD `2c1595b` (parent `f0ff10a`). The working tree is dirty with this task's diff only, plus the preserved untracked `errors.txt`. Nothing was committed, pushed or archived.
- Change scope and acceptance criteria: `openspec/changes/restart-authority-diagnostics/` (proposal, design and `live-training-loop` delta). This report covers offline tasks 1.1-1.5, 2.2 and 2.3.
- Game/mod/bridge versions:
  - Observer remains `0.5.0-dev`.
  - No protocol, schema, version or dependency change.
  - No game was involved.
- Python/package versions: the macOS executor venv (Python 3.12) and test-only `lupa.lua53` with the pinned `json.lua`. No installs.
- Scenario/budget: offline fake-clock production-Lua scenarios only. Real game: none.

## Files changed

| File | Change |
|---|---|
| `mod/observer/main.lua` | `Config.lifecycle_diagnostics = false` (literal-`true` opt-in) plus a private `life` state. Records only at rare lifecycle points. Existing branches are expanded into equivalent `if` blocks to record the branch actually taken. `MC_POST_GAME_END` body moved to a local `game_end()` (same early returns). `restart_budget` forward-declared. |
| `tests/test_lua_observer.py` | Backward-compatible `build_lua(lifecycle_diagnostics=, source_changes=)`; optional `DISPATCH_EVENTS` scripted order executed inside the stub `restart` dispatch (`AUTO_START` unchanged). |
| `tests/test_lua_live_loop.py` | `build_live(lifecycle_diagnostics=, source_changes=)`; autonomous-restart and normal-exit tests parametrized with diagnostics off/on. |
| `tests/test_lua_restart_diagnostics.py` (new) | 34 production-Lua scenarios. |
| `docs/RESTART_LIFECYCLE_DIAGNOSTICS.md` (new) | Fields, events, limits, simulated-order table, future capture/rollback procedure. |
| `openspec/changes/restart-authority-diagnostics/tasks.md` | 1.1-1.5, 2.2 and 2.3 are checked. 2.1 (Windows) and all of section 3 stay unchecked. |

## Record format and limits

Each record is one `Isaac.DebugString` line:

`[Isaac Future Lifecycle] id=<n> event=<label> time_ms=<int> [event fields] frame session epoch room phase active live approval loaded mode auth eligible lease_ms expires_s act_armed rs_armed rs_disabled attempts limit budget_ms awaiting await_ms pending`

**Token rules:**
- Every token matches `^[a-z_]+=-?[A-Za-z0-9_]+$`.
- Values are fixed labels, booleans (`1`/`0`), integers or `na`.
- A non-label string or non-integer number asserts inside the guard and disables diagnostics.

**Recorded events:**
- callbacks: `game_end_enter`/`game_end_exit`, `exit_enter`/`exit_exit`, `start_enter`/`start_exit`;
- dispatch: `dispatch_before`/`dispatch_after` (with `restart_id`, `ok`);
- branches: `restart_invalidate`, `approval_preserve`/`approval_drop` at the existing branch before mutation;
- connection: `close` (mapped reason), `hello` (after advertisement, before capability validation: `live_req`, `live_adv`), `restart_arm`;
- restart outcomes: `restart_cancel`/`restart_stop`/`restart_timeout`;
- `stop`.

**Correlation label `corr`:** `awaiting` if a dispatch awaits confirmation, otherwise `uncorrelated`. It is a label only and drives no branch.

**`auth` field:**
- `eligible` is the real `action_authorized()` result.
- `auth` explains it, checked in this order: `none`, `ok`, `inactive`, `expired`, `lease`, `other_validation`.
- It never replaces the predicate.

**Limits:**
- 256 attempts per mod load, counted before any read, so failures count. Attempt 256 is `stop reason=count`.
- A 20-minute monotonic window from the first event. The first event after it becomes `stop reason=deadline`.
- 768 bytes per record. An oversized record is replaced by an identity-only `stop reason=line_limit`.
- Limits never reset on close, reconnect, hello or epoch.

**Fault isolation:**
- The whole emission runs under `pcall` with a `busy` reentrancy latch.
- Any sink, clock, frame or format error, or any reentry, permanently disables only diagnostics.

**Diagnostics never:**
- write files, read approval files or touch the wire;
- change actions, restart state, deadlines or cleanup.

## Results

| Check/requirement | Command/scenario | Exit code | Status | Evidence |
|---|---|---|---|---|
| Existing Lua behavior, default off | `pytest tests/test_lua_observer.py tests/test_lua_live_loop.py tests/test_lua_callback_trace.py tests/test_lua_entities.py` (after the Lua change, before new tests) | 0 | passed | 102 passed |
| New diagnostics scenarios | `ISAAC_JSON_LUA=~/.cache/isaac-json/json.lua python -m pytest -q tests/test_lua_restart_diagnostics.py` | 0 | passed | 34 passed |
| Full POSIX gate | `ISAAC_JSON_LUA=~/.cache/isaac-json/json.lua ./scripts/check.sh` (ruff, format, mypy, pytest, pip check, OpenSpec) | 0 | passed | 1398 passed, 0 skipped (baseline 1362 + 36); OpenSpec `validate --all --strict` 29 passed, 0 failed |
| Change strict validation | `openspec validate restart-authority-diagnostics --strict` (pinned local CLI) | 0 | passed | "Change 'restart-authority-diagnostics' is valid" |
| Mutation discrimination | `/tmp` script; temporary edit of `main.lua`, pytest, then byte restore | n/a | passed | 12/12 caught (see below) |
| Windows `scripts/Check.ps1`, `scripts/OpenSpec.ps1 validate --all --strict` (task 2.1) | not available on macOS | n/a | not_run | Primary must run on Windows; POSIX results are not Windows proof |
| Real-game deployment/capture (3.1-3.3) | n/a | n/a | not_run | Requires separate authorization |
| Root-cause confirmation | n/a | n/a | not_run | Only simulated candidate orders exist |
| Learning evaluation | n/a | n/a | not_run | Out of scope |

### Mutations, all caught

- diagnostics enabled by default;
- `approval_drop`/`approval_preserve` labels swapped;
- no disable after a guarded failure;
- reentrancy not latched;
- window renewed on close;
- count limit removed;
- `lease` reason lost;
- diagnostic file read (`io.open` on the approval path);
- diagnostic perturbs restart attempts;
- `corr` always `awaiting`.

The tree was restored byte-identically after each mutation.

An earlier "reload approval" mutation was ineffective: it called a function declared later. It was replaced by a direct `io.open`, which was caught.

## Simulated sequences and observed existing behavior

All of these are SIMULATED orders scripted inside the single `restart` dispatch. They are candidate traces, not engine evidence. Every sequence issued exactly one `restart`, and the enabled/disabled transcripts are identical.

| Sequence | Records and existing behavior |
|---|---|
| exit, start | `exit_enter corr=awaiting live=1` → `approval_preserve` → `close reason=game_exit` → `start_enter corr=awaiting continued=0` → `dispatch_after ok=1`. The next hello has `auth=ok live_adv=1 epoch=2`; the live loop is advertised. |
| exit, start, exit, start | The second `exit_enter` is `corr=uncorrelated` with `live=0`, giving `restart_invalidate` and `approval_drop` (pre-mutation `approval=1`, `awaiting=na`). The second `start_enter` is `corr=uncorrelated`. The hello has `auth=none`; `safe_actions_v1` is not advertised. |
| exit, exit, start | The second exit still has `awaiting=1`, but `live=0` because the first exit closed the session, so `approval_drop`. The start then still confirms (`rs_disabled=0`). The hello has `auth=none`. |
| start, exit | The start consumes `awaiting` (confirms). The exit has `live=1`, `awaiting=na`, giving `restart_invalidate` and `approval_drop`, and `exit_exit rs_disabled=1`. The hello has `auth=none`. |
| disconnect, exit, start | `close reason=peer` clears `live`, so the exit gives `approval_drop` (`awaiting=1`). The start confirms. The hello has `auth=none`. |
| exit, start, disconnect | `approval_preserve`; the live loop is advertised after reconnect. |

**Observation:** four distinct simulated orders reproduce the reported shape (one dispatch, two native starts or a disconnect, then refused live capability). Each one shows the drop decision at the actual `MC_PRE_GAME_EXIT` branch.

Which order, if any, happened in the real run is unknown. In particular, "duplicate exit before confirmation" and "disconnect before exit" drop approval even without a second start.

No guard was changed. Any fix belongs in a separate change after real evidence (design non-goal; assignment item 7).

## Authority, timeout and budget scenarios

**Hello refusal explanations:**

| `auth` value | Scenario |
|---|---|
| `none` | No approval; `loaded=0`, `live_req=1`, `live_adv=0`, then `close reason=other` |
| `inactive` | Approval present, no game started |
| `expired` | Past `expires_at`; `expires_s` negative |
| `lease` | Monotonic action lease elapsed while `expires_s` is still positive |
| `other_validation` | `slot=3` |

**Restart scenarios:**
- **Confirmation timeout:** a `restart_timeout` record with `rs_disabled=1`; still exactly one dispatch.
- **Exhausted attempts** (`max_restarts=1`): `restart_arm rs_armed=0 attempts=1 limit=1`, and no second dispatch.
- **Legacy 600-second lease:** a `restart_stop` record, and no dispatch after it.
- **Normal exit** (live and legacy, diagnostics on): training approval is still dropped; existing tests pass with diagnostics on and off.

**Budgets:**
- 150 epochs plus 6 reconnects give exactly 256 records, IDs 1..256, with the last being `stop reason=count`. Nothing follows, even after exit/start.
- The deadline stop happens at +20 min and nothing follows after a reconnect.
- A close and reconnect at +16.7 min do not extend the window.
- With a test-only `LINE_MAX=80` source substitution, the first record is `stop reason=line_limit` and nothing follows.

## Failure injection and parity

- Enabled/disabled parity was compared for all six sequences:
  - wire output (first session and reconnect);
  - action ack status and held input value;
  - dispatched commands;
  - `CLOSED`;
  - all non-diagnostic log lines.
- A transient sink fault and a fractional clock each keep the run identical to the disabled run under the same fault, with no diagnostic line after the fault.
- A frame read fault inside `MC_PRE_GAME_EXIT` stops diagnostics after `dispatch_before`. Approval is still preserved, the session still closes, and the restart is confirmed.
- A recursive sink re-entering `MC_POST_GAME_END` disables diagnostics without escaping; dispatch and approval are unaffected.
- `io.open` call counts are identical with diagnostics on and off, with and without in-memory approval. Diagnostics never read or reload approval.

## Privacy review

- Records contain no approval evidence strings, profile/slot/runtime identifiers, paths or file contents.
- There is no raw close/error text: close reasons map to fixed labels.
- No inputs and no per-frame data are recorded.
- The session ID is the bridge's validated 32-hex identifier, which `callback_trace` already logs.
- A test asserts that the approval values (`offline-only`, `simulated`) and the `/` character never appear.
- No private logs, saves or model data were read or copied.

## Real game

None. No game launch, deployment, approval write, save access, forced death, Steam Cloud, REPENTOGON or supervisor. Real-game capture, deployment, root-cause confirmation and learning evaluation: not_run (they need separate authorization). The future procedure is documented in `docs/RESTART_LIFECYCLE_DIAGNOSTICS.md` but was not executed.

## Limitations and continuation

**Self-review against the delta spec:**
- Default off: tested.
- Nonrenewable 20 min / 256 / 768 limits across reconnect and epochs: tested.
- Nothing reaches wire, policy, reward or checkpoints: no wire code touched, parity tested.
- Ordered entry/exit, dispatch, close and hello facts: present.
- Preserve/drop recorded at the actual branch: present.
- Missing/inactive/expired/lease/other explained without reload: tested.
- Faults and reentrancy disable only diagnostics: tested.
- Unchanged:
  - normal-exit invalidation;
  - expiry;
  - the three-attempt/ten-minute legacy limit and the 120-second action lease;
  - training `max_restarts`;
  - the confirmation timeout;
  - cleanup.

**Residual risks:**
- `trace_num` requires integer `Isaac.GetTime()`. A non-integer engine clock would disable diagnostics, safely but silently, apart from the absence of records.
- The `auth` order is a documented precedence, not a full predicate breakdown.

**Unresolved questions:**
- What emitted the second native start, and which real order invalidated approval?
- Does the bridge disconnect before the engine's `MC_PRE_GAME_EXIT` in practice?

**Next action (primary):**
1. Review the diff.
2. Run Windows `scripts/Check.ps1` and `scripts/OpenSpec.ps1 validate --all --strict` (task 2.1).
3. Decide on a separately authorized capture (section 3).

## Feedback 1 response (2026-10-19)

Same task ID and allowed writes. Changed only `tests/test_lua_restart_diagnostics.py`, this report, `subagent_report.md` and `agent-status.json`. Production Lua, serialization and authority behavior are unchanged since the first delivery: the `main.lua` diff stat is identical at 144 insertions and 5 deletions.

**1. Portable parity**
- The `first_outgoing`/`outgoing` transcript fields are now compared through `wire()`, which splits on newlines, decodes each message in order and keeps any undelimited tail verbatim.
- `typed()` tags every value with its JSON type. Only object key order is ignored. Message count and order, array order, keys, values and types (bool vs int, int vs float, null) are all kept.
- The remaining transcript fields are still compared exactly: ack status, held input, capabilities, commands, `CLOSED` and non-diagnostic logs.
- Wall time is frozen in every parity run: the approval is created at `WALL + 3600` from one module-level wall second, and Lua `os.time` returns `WALL` before the first hello.
- New `test_wire_comparison_ignores_key_order_only`: a key permutation (nested object included) compares equal. These comparisons differ:
  - a changed value;
  - `1` vs `true`;
  - `1` vs `1.0`;
  - reversed array order;
  - a missing key;
  - swapped message order;
  - an added partial tail.

**2. Delayed second exit, as a persistent SIMULATED scenario** (candidate only, not the confirmed engine cause)
- Sequence: one death restart (exit and start inside the dispatch, confirmed), then a live reconnect with a second session. The reconnect advertises `live_loop_v1` and rearms; an action is accepted and held (`1.0`).
- After that, `exit` then `start` occur without another dispatch, followed by a read-only hello.
- Observed with diagnostics on:
  - exactly one `restart`;
  - exactly one `approval_preserve`, from the first exit;
  - the single `approval_drop` comes right after `restart_invalidate`, with `live=1 awaiting=na approval=1`, the second session ID and `epoch=2`;
  - the preceding `exit_enter` and the last `start_enter` both have `corr=uncorrelated`;
  - held input is `nil` after the exit;
  - the final hello has `auth=none approval=0 live_adv=0`, and `safe_actions_v1` is absent.
- `test_delayed_second_exit_parity`: the enabled and disabled transcripts are equal under the portable comparison.

**Checks (macOS executor host)**

| Check | Command | Exit code | Status | Result |
|---|---|---|---|---|
| Focused | `ISAAC_JSON_LUA=~/.cache/isaac-json/json.lua python -m pytest -q tests/test_lua_restart_diagnostics.py` | 0 | passed | 37 passed |
| Full POSIX gate | `ISAAC_JSON_LUA=~/.cache/isaac-json/json.lua ./scripts/check.sh` | 0 | passed | ruff, format, mypy; 1401 passed, 0 skipped; OpenSpec all strict 29/29 |
| Change strict | pinned `openspec validate restart-authority-diagnostics --strict` | 0 | passed | valid |
| Mutations | temporary `main.lua` edit, then byte restore (diff stat rechecked) | n/a | passed | 4/4 caught, listed below |
| Windows `Check.ps1` / `OpenSpec.ps1` (task 2.1) | unavailable on host | n/a | not_run | Primary rerun required |

Mutations caught:
- a wire value that differs only when diagnostics are enabled: 11 parity tests failed;
- preserving approval whenever `live` is on: the delayed and start-before-exit tests failed;
- preserving approval when diagnostics are enabled: the delayed tests and parity failed;
- dropping the hold silently when enabled: the delayed parity test failed on logs.

**Limitations**
- Key-order nondeterminism could not be reproduced on macOS. Portability is shown by the permutation test and the primary's Windows observation; Windows confirmation is still pending.
- Task 2.1 and section 3 stay unchecked. No game, deployment, approval, commit, push or archive.
