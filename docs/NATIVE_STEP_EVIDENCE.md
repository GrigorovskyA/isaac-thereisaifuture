# Native step evidence hooks (offline, source 0.4.6-dev)

Producer-side diagnostics for a future native step probe. They live inside the existing
default-false `callback_trace` window (10 s, 512 log attempts including the reserved stop,
300 bytes per line, one nonrenewable window per mod load). They are never sent on the wire,
never feed the lifecycle reducer and prove nothing about engine behavior.

## Records

All values are scalars. Common fields: `id`, `time_ms`, `frame`, `update`, `session`,
`epoch`, `room`, and `seq` (the latest accepted command sequence; heartbeats move it).

| Event | Hook phase | Extra fields |
| --- | --- | --- |
| `action_accepted` | after canonical validation and hold assignment (not wire-ack delivery) | `move`, `shoot`, `frames`, `until` (hold end frame), `deadline_ms` (wall deadline) |
| `hold_update` | MC_POST_UPDATE after `action_guard`, at most once per frame while the hold is live | `hold_seq`, `left` (frames to `until`), `upd_since` (bridge updates since acceptance) |
| `release` | immediately after `actions.hold` is cleared | `reason` (<=40 chars), `hold_seq` (from the cleared hold), `frame_due`, `wall_due`, `left` |
| `release_update` | first later post-update after a clear | `hold_seq`, `hold=absent`, `upd_since` |
| `release_input` | first later player movement/shoot input query answered with nil | `hold_seq`, `hook`, `button`, `override=nil` |

## What each record establishes

- `action_accepted` establishes that this bridge passed validation and assigned a hold;
  it is not proof the game consumed any input or that an acknowledgement reached Python.
- `hold_update` establishes that the observer's post-update callback ran while its hold
  remained live. `upd_since` is the bridge counter; it is not an input-consumption count.
- `release` establishes that the bridge cleared its hold.
- `release_update` establishes that a later observer post-update saw no bridge hold.
- `release_input` establishes that one queried hook/button returned no override from this
  bridge. It does not report the final value contributed by the game, the user or other mods.

No combination of these records establishes exact consumed engine updates, final neutral
input, or that all outcome/event callbacks for an endpoint have completed. Frame deltas are
elapsed game-frame observations, not by themselves proof that the requested input interval
was consumed. A future producer must supply independent, build-verified interval-consumption,
bridge-control-clear and event-seal evidence before a local reducer candidate can be used
as live step completion.

`frame_due`/`wall_due` are the observed expiry conditions at clearing time (both 1 cannot be
attributed to one cause; neither 1 means a guard, command or context release). There is at
most one pending release, with no queue or retry. It is discarded by an accepted action, a
session/epoch/room change, game start/end, new level, room, disconnect, exit, unload, stop or
any trace fault. A line over 300 bytes stops the trace (`reason=line_limit`) instead of being
truncated. Logger/read failure or re-entry stops and clears diagnostics only.

## Evidence limits

- Bridge-side clearing is not physical neutrality; `override=nil` is not a neutral engine input
  (manual input and other mods still apply).
- A post-update or input query is not a consumed engine update; a frame delta alone does not prove
  the requested input interval was consumed. No READY, seal or watermark exists.
- Heartbeat/release do not alter the original hold identity (`hold_seq`).
- Source is 0.4.6-dev; the installed mod stays 0.4.5-dev. Live acceptance needs a reviewed
  closed-game deploy and a separate preflight. No approval file is created here.

## Future bounded probe (not run)

One short action, release and cleanup on the approved profile with `callback_trace=true`:
record the acceptance, `hold_update`, `release`, `release_update` and `release_input` lines.
Explicitly record which independent consumption/bridge-control-clear/event barriers remain missing;
raw records alone cannot satisfy those barriers. Do not force death, reset or restart to
fit the trace budget; if the budget ends first, report the stop record. All runtime checks are
`not_run`.
