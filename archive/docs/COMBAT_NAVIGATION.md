# Bounded combat navigation (opt-in)

## Explicit finite-window exploration

`--navigation-time-dominant` additionally requires `--auto-navigate`,
`--combat-gate` and diagnostic scale 1. The session runner exposes the same flag.
It uses the finite run window as its handoff cap and does not stop on cumulative
command, transition or pulse-second counters. The counters remain telemetry.
Default mode retains its original cumulative diagnostic limits.

This mode remembers directed connections only after a selected door and a fresh
observed transition. It prefers reachable unexplored exits, then confirmed routes
through visited rooms to another observed frontier. There is no hidden map access,
target-index arithmetic or assumed reverse door. Memory resets with session,
epoch, stage or stage type; ordinary combat handoffs retain it.
Remembered local reachability prevents alternating between two already measured
blocked frontiers. Actual revisits remeasure paths; changed observed doors clear
the old reachability result. Missing action acknowledgments cannot establish a
confirmed connection, including a rejected-release reconciliation race.

When no observed unexplored exits remain, it stops with
`Observed ordinary-room component exhausted`. If unexplored exits exist but the
measured first hop/known route cannot reach one, it stops with
`Observed ordinary-room frontier is unreachable`. These are local observations,
not full-floor completion. `navigation_search`, `navigation_connection` and
`navigation_no_progress` records explain the result. No New Run is dispatched.

Every measured path, <=6-frame pulse, release, <=0.8-second fresh-state wait,
health/identity/stationary check and fixed global deadline remains active. Paused,
stale or failed transport is not successful search. Navigation remains scripted
management inside reset, outside observations, normalization and learner rollouts.
Offline regression evidence does not establish native integration; qualify this
mode in a separately requested finite native pilot before longer runs.

`live --combat-gate --auto-navigate` selects a scripted management route between
combat segments. It uses the same structured connection and existing readiness
token checks. The default operator-managed gate is unchanged.

Reward accounting now uses the `live-conservative-v2` contract: absence is not a
kill and known HP floors survive software segment resets. Legacy combat-v1
checkpoints (including t8960) remain readable for frozen analysis but cannot
silently resume conservative live learning. See
[correction and compatibility](../reports/2026-10-20-live-reward-continuity.md).

The bridge must advertise `combat_navigation_v1` and `combat_navigation_grid_v2`
under a bounded live training approval. This negotiation emits `oracle.navigation`
version 2: a measured walkability grid, current room
index, stage/type, room type/shape, and at most eight open unlocked exits to ordinary
rooms, with slot and native position. EntityFrame/encoder/model schemas do not change.
The default mode prefers less-used observed room/exit pairs. This is management,
not learned navigation; none of its travel is combat training or evaluation data.

After enemy disappearance, an empty room may still have room_clear=false and no
open exit. In that specific state, management waits without action/learning for
at most two wall seconds in the current context, within the original gate/run
caps. A later clear flag or paused/frozen frame does not restart that interval;
health changes stop, and returning combat needs fresh readiness. Already-cleared
rooms with no prior settling wait still stop immediately if no ordinary exit
exists. The larger experiment observed this wait followed by an opened exit.
See [training evidence](../reports/2026-10-20-five-death-training.md).

All twelve shapes of ordinary rooms and all slots 0..7 are supported by the
planner: 1x1, IH/IV, 1x2/IIV, 2x1/IIH, 2x2, LTL/LTR/LBL/LBR. Four-neighbor BFS
uses measured safe cells, including the missing L corner, and replans each pulse.
Legacy explicit v1 peers retain version-1 telemetry; the runner requires v2 and
does not fall back to the old direct route.

Every movement pulse is two to six frames with no shooting and a release. One-frame
navigation corrections are excluded because their lease may expire before native
input sampling. Once inside the chosen open door's narrow crossing corridor, keep
moving outward; do not pull the player back to the interior approach. A safe approach
cell and the same open door remain required; blocked interior routes have no fallback.
Default global navigation limits are 256 action/release commands, 90 pulse seconds and four room transitions, additionally
bounded by the original gate/run deadlines. Three stationary pulses, damage,
missing data, rejected same-room input, unsupported geometry or no usable door stop
the run. Limits persist across handoffs and deaths. An explicit
`--navigation-budget-scale 1..5` multiplies these three cumulative limits and
requires `--auto-navigate`. Record the resulting budget before launch.
`--max-deaths 1..10` requires the combat gate and stops before another reset or
readiness request once that many terminal deaths are observed. Pair it with the
approval's restart cap; a restart resumes the learned model rather than creating
one from scratch. Neither option renews wall-time or approval limits.
Obstacles are routed around when a safe
connected route exists; they are never destroyed automatically. Special/locked/
secret doors, floor transitions and item/flight-dependent routes are excluded.

The row-major grid has measured origin/spacing, at most 1024 cells and dimensions
at most 32x32. Walkable cells must have 12-unit room-boundary clearance, no sampled
collision, no path hazard/blocking and no pit/spike/TNT grid. Cells outside an L
shape remain blocked. A blocked player/door approach or disconnected path stops
without a nearest-point teleport or straight-line fallback. Support for a shape
does not guarantee every obstacle layout is traversable within a finite budget.

A release can be rejected during a room transition before its snapshot arrives.
In that case the manager polls for at most 0.5 seconds under the original budgets,
without further movement. Only a later room visit in the same session/epoch with
unchanged health confirms the race; otherwise it stops. A rejected release never
counts as an acknowledged neutral command. Representative native crossings have
confirmed this race. An accepted release after the final outward approach can
also precede the native transition callback: management polls without movement
for at most 0.5 seconds under the same health/session/epoch and cumulative caps.
If no new visit appears, subsequent movement still requires a fresh valid grid
route; blocked cells never gain a fallback. See
[correction and experiment](../reports/2026-10-20-five-death-training.md).

Authorization is cached once per game process. A replacement on-disk approval
does not refresh that process's lease. For a new finite approval after the prior
one expires, normally close Isaac and launch through Steam with the new file
present before attaching. Do not bypass expiry or assume a successful probe
means the replacement approval loaded. See
[failed attach evidence](../reports/2026-10-20-door-correction-check.md).

Paused state waits. Menu unpause remains an external agent/operator action after
setup. Do not deploy observer changes while Isaac is running. Resume training from
the exact latest compatible model/normalizer, never initialize again silently.
After Continue/loading, the manager also waits for two consecutive frame advances
in the same context before moving or acknowledging combat. This settling wait uses
the existing deadline; a short movement timeout is logged separately from that
deadline expiring. The settling guard passed two live transitions. Later
fresh-process testing of the minimum-lease/doorway continuation fix passed
four native transitions including the long narrow room's far doorway with six
two-frame corrections. The transition cap stopped travel before combat; the fresh
combat handoff requirement was still open at that point. See
[fresh-process results](../reports/2026-10-20-fresh-door-check.md).
The subsequent bounded test accepted fresh readiness and resumed combat after
three real transitions, then repeated the handoff after one natural death restart.
Representative runtime acceptance passed. A subsequent user-prepared LTR/shape10
check passed its upper-door route and fresh combat handoff. A later LBL/shape11
check passed an upper exit and return through cleared neighbors with zero combat
decisions; immediate normal closure worked. Later LTL/shape9 completed a route
from the upper-right area to lower slot3, exit/return/second exit, with no combat.
LBR/shape12 subsequently passed lower slot3, return and second exit as well.
Observed native routes now cover all four L rotations; unobserved layouts/exits
are not implied. See [LTL check](../reports/2026-10-20-LTL-route-check.md) and
[LBR check](../reports/2026-10-20-LBR-route-check.md).
See [LBL check](../reports/2026-10-20-cleared-L-check.md).
Native2x2/shape8 later passed lower-left slot4 and upper-right slot5 routes with
return/cross-room travel through its measured obstacle mask. This covers those
observed routes, not every2x2 layout or exit. See
[2x2 check](../reports/2026-10-20-2x2-route-check.md).
Horizontal2x1/shape6 later passed a route from the left side to secondary
upper-right slot5; other exits/layouts remain unverified. See
[2x1 check](../reports/2026-10-20-2x1-route-check.md).
Vertical1x2/shape4 passed the bottom-to-upper-left slot0 route. Native remaining
shape families are2/IH,3/IV,5/IIV; observed routes do not imply every exit/layout.
See [1x2 check](../reports/2026-10-20-1x2-route-check.md).
The LTR check also exposed post-stop recovery latency: release
does not freeze enemies, and the player died before a living pause was verified.
Close normally promptly after combat-ending checks before slow evidence handling,
unless pause is already confirmed. See
[LTR check](../reports/2026-10-20-large-layout-check.md).
See [handoff evidence](../reports/2026-10-20-combat-handoff-check.md).

Example after file-2/profile preparation and a bounded approval, with a step target
chosen from the verified current checkpoint and a predeclared disk/stop budget:

```powershell
.venv/Scripts/python.exe -m isaac_threrisaifuture.cli live --mode train --config configs/training-live-v1.yaml --resume --seed 20 --steps 5376 --minutes 5 --max-faults 0 --combat-gate --auto-navigate --gate-wait-minutes 1.5 --confirmed-save-slot 2
```

This example is not an approval or evidence of gameplay quality. Runtime coverage
per shape is recorded in [the all-layout report](../reports/2026-10-20-navigation-all-layouts.md);
offline fixtures are not installed-game proof.

API provenance (documentation, not installed-build proof):
[Room](https://wofsauge.github.io/IsaacDocs/rep/Room.html),
[GridEntityDoor](https://wofsauge.github.io/IsaacDocs/rep/GridEntityDoor.html).
TargetRoomIndex is deliberately unused because its documented purpose concerns
transition animation. No hidden level layout is queried.
