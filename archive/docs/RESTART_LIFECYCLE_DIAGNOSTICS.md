# Restart lifecycle diagnostics (observer 0.5.0-dev, default OFF)

Change: `openspec/changes/restart-authority-diagnostics/`. These records explain
which existing lifecycle branch ran around a bridge restart dispatch. They are
bridge facts only. They cannot attest engine cause, manual input or physical
input release, and they grant no authority.

## Enabling

`Config.lifecycle_diagnostics` in `mod/observer/main.lua`. Only the literal
`true` enables it; any other value, including the shipped `false`, emits nothing.
There is no wire field, environment switch or approval field for it. It is
independent of `callback_trace` (10 seconds, per-frame), which would exhaust its
budget before a restart window.

## Limits (per mod load, nonrenewable)

| Limit | Value | Behavior |
|---|---|---|
| Window | 20 minutes (`1200000` ms) from the first diagnostic event | The first event at or after the deadline becomes `event=stop reason=deadline` |
| Attempts | 256, including failed attempts | Attempt 256 is always `event=stop reason=count` |
| Line | 768 bytes per complete record | An oversized record is replaced by an identity-only `event=stop reason=line_limit` |

Close, disconnect, reconnect, new `hello` and new game epochs do not reset any
limit. After `stop`, a fault or reentrancy, diagnostics stay off until the mod
is reloaded. Diagnostic state never changes approval, leases, restart attempts,
deadlines, `restart.disabled`, wire output, input results or cleanup.

## Record format

One `Isaac.DebugString` line (local `log.txt`), space-separated `key=value`
tokens, each matching `^[a-z_]+=-?[A-Za-z0-9_]+$`:

```text
[Isaac Future Lifecycle] id=7 event=approval_drop time_ms=... frame=... session=<32 hex|none> epoch=2 room=1 phase=closed active=1 live=0 approval=1 loaded=1 mode=training auth=ok eligible=1 lease_ms=... expires_s=... act_armed=1 rs_armed=1 rs_disabled=0 attempts=1 limit=3 budget_ms=... awaiting=1 await_ms=... pending=na
```

Booleans are `1`/`0`; `na` means unavailable or absent. Event-specific fields
follow `time_ms` and precede the common facts.

| Field | Meaning |
|---|---|
| `id` | Monotonic attempt number for this mod load (1..256) |
| `time_ms` | `Isaac.GetTime()` (monotonic); must be an integer or diagnostics stop |
| `frame` | `Game():GetFrameCount()`; a read error stops diagnostics |
| `session`, `epoch`, `room`, `phase` | Bridge session ID (validated hex), game epoch, room visit, transport phase |
| `active`, `live` | `state.active`; live loop negotiated (`live.on`) |
| `approval`, `loaded`, `mode` | In-memory approval present; load attempted successfully; profile mode label (`training`, `isolated`, `ordinary_profile_exception`, `other`, `none`) |
| `auth`, `eligible` | `eligible` is the real `action_authorized()` result. `auth` explains it: `ok`, `none` (no approval in memory), `inactive`, `expired` (wall clock), `lease` (monotonic action lease elapsed), `other_validation` (any remaining predicate failure). Checked in this order. |
| `lease_ms`, `expires_s` | Remaining monotonic action lease; remaining wall-clock approval seconds |
| `act_armed`, `rs_armed`, `rs_disabled` | Action authority armed; restart armed; restart permanently disabled |
| `attempts`, `limit`, `budget_ms` | Restart attempts used, current limit, remaining restart budget |
| `awaiting`, `await_ms`, `pending` | Epoch awaiting fresh-start confirmation and its remaining time; scheduled pending restart epoch |

Never recorded: approval evidence strings, profile/slot/runtime identifiers,
file contents, paths, raw close/error text, inputs or per-frame data. Close
reasons are mapped to `game_exit`, `peer`, `unload`, `authority`, `other` or `none`.

## Events

| Event | Location | Extra fields |
|---|---|---|
| `game_end_enter` / `game_end_exit` | `MC_POST_GAME_END` | `game_over` |
| `dispatch_before` / `dispatch_after` | Around the single `restart` command | `restart_id` (attempt counter), `ok` |
| `exit_enter` / `exit_exit` | `MC_PRE_GAME_EXIT` | `corr` |
| `restart_invalidate` | Existing normal-exit `restart.disabled = true` branch | |
| `approval_preserve` / `approval_drop` | Existing approval branch, before mutation | |
| `start_enter` / `start_exit` | `MC_POST_GAME_STARTED` | `continued`, `corr` |
| `close` | Start of `close()` | `reason` |
| `hello` | After advertisement, before capability validation | `live_req`, `live_adv` |
| `restart_arm` | After a full ack arms restart | |
| `restart_cancel`, `restart_stop`, `restart_timeout` | Existing pending-cancel, budget-exhausted and confirmation-timeout branches | |
| `stop` | Final record | `reason` |

`corr=awaiting` means a dispatch is still awaiting confirmation (only a dispatch
sets it); `corr=uncorrelated` means no awaiting dispatch. This is a label only;
it never drives a branch.

## Offline candidate sequences (simulated, not engine evidence)

`tests/test_lua_restart_diagnostics.py` scripts these orders inside one
dispatch. Existing semantics are unchanged in every case:

| Sequence | Observed existing behavior |
|---|---|
| exit, start | `approval_preserve`; start confirms; next hello `auth=ok`, live loop advertised |
| exit, start, exit, start | Second exit is `uncorrelated` with `live=0`: `restart_invalidate`, `approval_drop`; second start `uncorrelated`; hello `auth=none` |
| exit, exit, start | Second exit still `awaiting` but `live=0` after the first close: `approval_drop`; start still confirms; hello `auth=none` |
| start, exit | Start consumes `awaiting`; exit `uncorrelated`, `live=1`: `restart_invalidate`, `approval_drop`; hello `auth=none` |
| disconnect, exit, start | `close reason=peer` clears `live`; exit `approval_drop`; hello `auth=none` |
| exit, start, disconnect | `approval_preserve`; hello advertises live loop |

Several distinct orders reproduce the reported shape (one dispatch, two starts,
refused live capability). Which one, if any, occurred is unknown until a real
capture. Any behavior fix requires a separate change.

## Future operator-present capture (not executed)

Requires separate authorization and budget under the existing approval and
training limits. No forced death, enemy spawn, reset, desktop input, screen
capture, Steam Cloud, save editing, REPENTOGON or supervisor.

1. Operator exits Isaac normally; confirm no Isaac process is running.
2. Back up the installed `main.lua` locally and record source/installed SHA-256.
3. Deploy a reviewed copy that differs from source only by
   `lifecycle_diagnostics = true`; record its hash and read it back.
4. Operator launches the game, selects file 2 and Continue manually; start the
   already approved, finite run without renewing approval on reconnect.
5. Wait for a natural death restart within the predeclared budget (the window
   ends after 20 minutes regardless). If none occurs, stop and record `not_run`.
6. Verify disconnect release and manual control; operator exits normally.
7. Preserve `log.txt` privately (not in Git). Extract only `[Isaac Future
   Lifecycle]` and observer lines and correlate them with the native log.
8. Rollback while closed: restore the default-off file, verify its hash equals
   the repository source.
