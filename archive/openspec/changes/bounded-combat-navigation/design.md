## Context

See proposal.md. The existing reset wait has a shared absolute deadline and owns
the only LiveClient. A private experiment proved pulse/release traversal but waited
for agent image inspection. Keep this work outside known-map policy encoding.

## Goals / Non-Goals

Enable opt-in bounded travel across ordinary empty rooms of all twelve shapes.
No full-run policy. Navigation is explicitly scripted management, not learned play.

## Decisions

- Negotiate `combat_navigation_v1` only alongside live_loop_v1. Attach version-1
  navigation metadata under the separate oracle block only for that negotiation.
  Old/default peers see the exact previous oracle fields. Missing APIs/data fail
  closed; unavailable data never implies an exit. Limit eight doors; validate
  finite coordinates and unique slots. GetDoor/IsOpen/IsLocked/TargetRoomType and
  GetDoorSlotPosition come from IsaacDocs; no hidden level layout is enumerated.
- Capture current room index, stage/type and shape, and only open/unlocked doors
  with TargetRoomType ROOM_DEFAULT. Python admits shapes 1..12 with measured v2
  grids. Door slots 0/1/2/3 mean left/up/right/down; 4..7 are their second positions.
  TargetRoomIndex is not trusted for routing: docs
  say it affects animation. Count attempts on observed current-room/exit pairs,
  reset memory on connection/epoch/floor change, prefer least-used exit.
- Subclass the gate, leaving operator/default behavior intact. Poll fresh state,
  move <=6 frames then release; follow measured walkable cells. At most
  256 action/release commands, 90 pulse wall seconds, four transitions per run.
  Three stationary pulses, damage, invalid data, no eligible exit, same-room
  rejection or deadline stop and clean up. Do not reset limits between handoffs.
  For a rejected release whose last snapshot is still in the source room, poll
  for at most 0.5 seconds under the original deadlines and cumulative pulse cap.
  Only a fresh later room visit in the same session/epoch with unchanged health
  establishes a transition race. No additional action or successful neutral ack
  is inferred. Otherwise stop. Reserve four pulse seconds before another pulse
  for bounded command/release/reconciliation time.
- On combat, use existing readiness files/token checks and fresh resume validation.
  No management env.step, reward events, observation or normalizer/LSTM updates.
  Paused state remains a wait: menu recovery is outside this module.

## Risks / Trade-offs

Obstacles can disconnect all routes -> bounded stop, no bombing/shooting.
Few exits or no fights -> bounded
stop without fabricated progress. API differences -> retain runtime pending until
installed-build evidence. This first scope trades coverage for a small tested route.

## Migration Plan

No dependency/model migration. Close Isaac before deploying observer; keep previous
artifact hashes. Default runs remain compatible. Disable the new CLI flag to roll
back navigation; restoring observer files requires another normal game closure.

## All-layout extension (user, 2026-10-20)

Negotiate combat_navigation_grid_v2 together with combat_navigation_v1/live_loop_v1.
Only v2 peers receive navigation version 2 and a grid object. V1 remains unchanged;
the production auto-navigation runner requires v2 and never silently uses the old
straight-line route. Missing/invalid grid data stops before input.

Grid: measured origin, 40-unit spacing verified against GetGridPosition samples,
width/height <=32 and at most 1024 cells, row-major binary walkability string.
Every admitted cell must be inside IsPositionInRoom with 12-unit boundary clearance,
have zero collision at center/four 12-unit corners, and GetGridPath <900. Explicit
pit/spike/on-off-spike/TNT grids are blocked. This is a grounded conservative route,
even for flying characters. No hidden rooms/contents are enumerated. Scan and wire
sizes are bounded; malformed API results make the snapshot unavailable.

Use bounded four-neighbor BFS over only admitted cells. Match the current player
cell and the measured doorway's one-cell interior approach; no nearest-node teleport
or direct fallback if either is blocked. Compress collinear path sections to a
waypoint, align within the current safe corridor and pulse toward that waypoint.
Only at the interior approach may an outward pulse cross the chosen open door.
Replan on each fresh pulse so changed obstacles revoke old paths. Try reachable
exits in least-used order; no-route is distinct from physical stall. All shapes
1..12 use the same measured mask, including concave L voids; slots use modulo 4.
Movement/release/reconciliation/health/deadline guards remain unchanged. The finite
navigation budget becomes 256 commands/90 pulse seconds so a long 2x2 detour is not
cut off at the earlier small-room budget. Four transitions and original gate/run
caps remain; the runner never renews any limit automatically.
Before management movement or automatic readiness, require two consecutive fresh
frame advances in the same context. Render snapshots during Continue/loading may
look active before game updates run. Waiting for stability spends the original
handoff budget, never extends it. A short pulse-progress timeout is a navigation
stop, not an expired operator gate unless that original deadline also expired.
Navigation correction leases are 2..6 frames. A one-frame lease can expire at the
next native input sample before producing movement. Keep the same cell alignment
tolerance and all stall/health limits; do not hide ineffective pulses by weakening
the stationary detector. Goal shape/grid and action reference/ack frames/positions
are recorded in management logs for future runtime diagnosis, never policy input.
While already crossing an observed open door, stay outward inside its narrow
approach-to-boundary corridor instead of recentering on the interior waypoint.
Require the same open door, a safe measured approach and <=8-unit perpendicular
offset; this is the explicit final crossing, not a fallback through blocked cells.

Offline matrix must cover all twelve shape masks, all four missing L corners,
secondary slots, obstacle detours, disconnected routes, dynamic blocking, malformed
grids and unchanged learning accounting. Installed-game coverage is reported per
shape; synthetic routes are never claimed as runtime proof for unobserved layouts.

Post-combat exit settling: native enemy disappearance can precede room_clear and
door opening. For empty + room_clear=false + no observed ordinary exit only,
poll without movement for <=2 wall seconds per current context, spending the
original gate/run caps. Do not renew on pause/frozen frames or door flapping.
Continue the same interval if room_clear becomes true before doors open, without
restarting its timer. Health changes stop before any readiness or movement. Cleared
rooms without eligible exits still stop immediately; missing/invalid telemetry
does not become a route. Returning combat uses fresh token/context validation.
Do not infer actual door timing from a truncated log; installed-game validation
of this correction remains required.

Explicit multi-attempt sessions add optional max_deaths1..10 to GateConfig and
LiveRunOptions, checked on reset after releasing input and before issuing another
readiness request. Count only terminal death outcomes, not truncations/faults.
Default is no death cap beyond existing approval/deadlines. Pair limit5 with
Lua approval max_restarts4 to prevent a sixth attempt. Partial PPO rollouts remain
unsaved; never force a fake terminal/sample to complete a256-step chunk.
Optional navigation_budget_scale1..5 requires auto-navigation above1 and multiplies
256/90/4 to at most1280 commands/450 pulse seconds/20 transitions, cumulative
through all restarts. Default1 and pulse/health/stall/settling/run/gate caps stay
unchanged. CLI logs both settings; no checkpoint/config hash/schema migration.
## Accepted-release doorway settling

A native run crossed after the last accepted release and the manager's next grid
replan: source frame2251 command, transition callback at2260 after the stop. Keep
the safe-cell mask and eight-unit crossing corridor unchanged. For an outward
pulse whose measured route is already at the door approach, poll without input
for <=0.5 seconds after release if the latest visit is still the source. Charge
the interval to cumulative pulse seconds and original deadlines. Reuse strict
same-session/epoch,health/death checks. A later native visit confirms transition;
otherwise return only the latest state and require a fresh valid grid before
another pulse. No nearest-cell projection, blocked-cell fallback or invented visit.
