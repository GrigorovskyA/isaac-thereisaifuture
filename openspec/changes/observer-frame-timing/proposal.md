## Why

A native `pure` hour (29 rollouts) showed the bridge waiting 205 ms per env step for
game snapshots: 91.6% of rollout time, against 11 ms for commands and 8 ms for Python
itself. One step is about 7.3 game updates and about 4.3 snapshots arrive per step, so
the game runs near 32 updates/s instead of 60. We cannot tell whether the mod's own
per-frame work (entity `capture()`, `json.encode`, socket send in `MC_POST_RENDER`,
`action_guard` in `MC_POST_UPDATE`) slows the game, or whether the game itself runs
slow (frame limiter, focus, rendering).

## What Changes

- `mod/observer/main.lua` keeps cheap cumulative counters from `Isaac.GetTime()`:
  update and render callback counts and time, snapshot count, `capture()` time and
  snapshot `json.encode` time. About every 10 s of wall time, while streaming, it
  writes one log line and resets the window:
  `Observer perf window_ms=10003 updates=321 renders=598 snapshots=290 update_ms=12 render_ms=4100 capture_ms=3000 encode_ms=800`
  (key=value integers, fixed key order).
- `scripts/lua_perf.py` reads a `log.txt` offline and prints updates/s, renders/s,
  snapshots/s, the wall-time share of each callback, capture and encode, and mean ms
  per snapshot.

## Capabilities

### Modified Capabilities

- `game-observation`

## Non-goals

- No protocol, snapshot, capability, handshake or command change.
- No observation, reward or policy input change; the numbers are for people only.
- No attempt yet to speed the game up; this only tells us where the time goes.

## Acceptance

A native one-hour session's `log.txt` yields perf windows, and
`python scripts/lua_perf.py <log.txt>` reports updates/s and the capture/encode share
of wall time.

## Impact

`mod/observer/main.lua` (needs a redeploy; `launcher.preflight` compares file hashes),
`scripts/lua_perf.py`, `scripts/check.sh`, `scripts/Check.ps1` and tests.
