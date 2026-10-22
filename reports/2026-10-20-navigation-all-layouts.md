# Evidence: navigation across all native room layouts

Follow-up settling check crossed two doors (room 81 -> 80 -> 81), then stopped on
three stationary one-frame corrections at the narrow room's far-door approach.
All 36 releases were accepted and health stayed unchanged. Added offline minimum
two-frame corrections and explicit open-door crossing continuation; these changes
still need a new bounded runtime check. Task 2.2 remains open because combat was
not reached. See [settling recheck](2026-10-20-layout-settling-check.md). Earlier
startup failure and per-shape coverage below describe the preceding invocation.

## Scope

User explicitly requested ordinary 1x1, long/narrow, 2x2 and all rotated L layouts.
Amended the existing bounded-combat-navigation change; no delegation or commits.
All twelve native shape IDs and eight door slots use measured geometry, not
per-shape guessed movement. Collision/path-aware grounded routing is scripted
management and remains outside the combat policy/normalizer/reward/checkpoint.
Special/locked/secret exits and item/flight-dependent routes remain excluded.

Protocol compatibility: an additional combat_navigation_grid_v2 capability
requires v1/live_loop capabilities, emits navigation version 2 with a bounded
binary mask, and is required by the auto-navigation runner. Explicit legacy v1
peers still receive unchanged version-1 telemetry. Default peers receive neither.
No observation/action/reward/checkpoint schema/config changes.

## Sources and geometry contract

Primary API documentation:
[Room](https://wofsauge.github.io/IsaacDocs/rep/Room.html),
[RoomShape](https://wofsauge.github.io/IsaacDocs/rep/enums/RoomShape.html),
[DoorSlot](https://wofsauge.github.io/IsaacDocs/rep/enums/DoorSlot.html).
GetGridPosition/GetGridWidth/GetGridSize define the measured lattice;
IsPositionInRoom with 12-unit margin excludes concave voids; collision samples,
GetGridPath and explicit hazard types conservatively block unsafe cells. API
documentation alone is not evidence for this installed build.

Mask capped at 1024 cells/32x32, finite positions, exact 40-unit regular spacing;
four-neighbor BFS visits at most all cells, rejects row wraps, compresses straight
segments and replans each pulse. Door approach must match the measured lattice.
No direct fallback on blocked/disconnected data. Existing health/session/frame,
release reconciliation, stall and deadline guards remain. Navigation limit changed
to 256 commands/90 pulse seconds, four transitions, to cover larger routes.

## Offline evidence

- Initial production-Lua matrix found a genuine strict-JSON mismatch: Lua division
  emitted height 9.0/16.0, rejected by strict Python integer fields. Fixed producer
  with integral floor conversion; validator was not weakened. Initial failed
  invocation: 13 failed/53 passed.
- Follow-up targeted suite: 66 passed, then 80 passed in 2.70s after adding steering
  simulation and unreachable-exit checks. Includes all twelve topology and Lua
  capture shapes, all four rotated L voids, all eight outward slots, obstacle
  detours/dynamic disconnection, strict mask validation and real-wrapper learning
  accounting/cleanup regression tests.
- First full gate stopped on lint (import order and explicit zip strict flag).
  These were corrected. Full gate passed: 1882 tests, zero skips, 45.06 seconds,
  Ruff/format/mypy/pip and strict OpenSpec 31/31. After the live startup finding,
  two additional regressions passed (82 targeted, 2.61 seconds); final full gate
  for the settling/classification correction passed: 1884 tests, zero skips,
  44.76 seconds, exit 0; Ruff/format/mypy/pip and strict OpenSpec 31/31 passed.

## Recorded live-check budget

After offline gates only: one Steam launch after closed-game backup/deployment,
file 2/Continue via menus, one random-policy seed-21 attach invocation, <=512 combat
decisions, three minutes, 90-second gate cap, zero tolerated infrastructure faults,
one natural-death restart, 512 MiB training-tree cap. At most 256 management
commands/90 pulse seconds/four transitions; three stationary pulses stop. Startup
has a separate 120-second cap before attachment; no automatic second invocation
or budget renewal. No forced layouts, debug teleport/spawn/reset or save changes.
Close normally/remove exact temporary approval and fully reload unchanged t5120.
Unseen shape coverage remains pending even if a representative runtime check passes.

## Runtime results

| Check | Result | Evidence |
| --- | --- | --- |
| Deployment/launch | passed | Source backup/hash and normal process absence before deployment. One Steam launch, PID 15472/v1.9.7.17, explicit visible FILE 2 selection and Continue; no Steam/Cloud setting edits |
| Capability | passed | Actual Lua 5.3 observer 0.5.0-dev advertised/accepted combat_navigation_grid_v2; session `f61a0829211043cc94accdd2adc3b634`, log `runs/live/sessions/20261020-081036-efba22/` |
| Path selection | partial | Starting room index 81, ordinary shape 7; manager found a route to open left door slot 0 and sent one accepted left/no-shoot six-frame command |
| Runtime stop | failed target | No six-frame progress was observed within the 0.8-second pulse window. Release was accepted; zero cleanup errors. Original code mislabeled the short pulse deadline as operator-wait expiry (actual gate wait 0.859s versus 90s cap). Exit 0 was a handled stop, not completed target |
| Native geometry readback | passed | Separate read-only v2 probe: shape 7, 28x9 grid, 72 safe cells, six fresh samples advancing game frame 14125 -> 14132. Position remained (80,280), room index 81/visit 0. No native room transition or combat decision was observed |
| Recorded-mask replay | passed, offline replay | On the actual captured mask, left approach uses one cell/outward-left pulse; right approach needs 30 cells and first pulse up to route around blocking geometry. Replay emits no game input and is not completed gameplay evidence |
| Cleanup/lineage | passed | Normal game close, exact temporary approval hash removed, no process/listener, source/installed preflight, full unchanged t5120 model/normalizer identity/reload; training tree 202,002,495 bytes <512 MiB. No death restart, PPO update, second invocation or budget renewal |

The startup/progress failure occurred immediately after Continue. A frozen or
not-yet-steady game update phase is suspected; its precise mechanism is not proven
by the retained records. The later fresh readback shows ongoing game updates and
valid telemetry, not proof that the earlier movement was physically executed.

Offline correction: require two consecutive same-context gameplay frame advances
before management movement or automatic readiness. Frozen render snapshots wait
under the original deadline. A pulse-progress timeout now reports NavigationStopped
unless the original operator/run deadline also expired. New tests verify no action
or readiness from frozen frames and accurate short-deadline classification. The
corrected startup path has not been rerun in Isaac under this consumed budget.

## Per-shape coverage

Updated after subsequent user-prepared checks on2026-10-20. A passed route means
the explicitly recorded doorway only, not every position/exit in that shape.
See [fresh-door check](2026-10-20-fresh-door-check.md),
[combat handoff](2026-10-20-combat-handoff-check.md) and
[LTR check/recovery limitation](2026-10-20-large-layout-check.md) and
[LBL cleared-room route](2026-10-20-cleared-L-check.md) and
[LBL secondary exit](2026-10-20-LBL-secondary-exit-check.md) and
[2x2 slots4/5](2026-10-20-2x2-route-check.md) and
[LTL slot3](2026-10-20-LTL-route-check.md) and
[LBR slot3](2026-10-20-LBR-route-check.md) and
[horizontal2x1 slot5](2026-10-20-2x1-route-check.md) and
[vertical1x2 slot0](2026-10-20-1x2-route-check.md).

| Shape | Name | Lua capture + path/steering offline | Installed v2 telemetry | Completed v2 route |
| --- | --- | --- | --- | --- |
| 1 | 1x1 | passed | passed | passed, observed exits in subsequent checks |
| 2 | IH | passed | not_run, user deferred | not_run, user deferred |
| 3 | IV | passed | not_run, user deferred | not_run, user deferred |
| 4 | 1x2 | passed | passed | bottom-to-upper-left slot0 passed; slot4/other exits not_run |
| 5 | IIV | passed | not_run, user deferred | not_run, user deferred |
| 6 | 2x1 | passed | passed | cross-room upper-right slot5 passed; slot7/other exits not_run |
| 7 | IIH | passed | passed | left and far-right exits passed after correction |
| 8 | 2x2 | passed | passed | slots4/5 exits and return entry passed; other exits not_run |
| 9 | LTL | passed | passed | lower slot3 exit/return/second exit passed; other exits not_run |
| 10 | LTR | passed | passed | upper slot1 passed; other exits not_run |
| 11 | LBL | passed | passed | upper slot1 and secondary slot6 exits/return entries passed; other exits not_run |
| 12 | LBR | passed | passed | lower slot3 exit/return/second exit passed; other exits not_run |

Historical version-1 1x1 door crossing does not count as a v2 grid route. No debug
room spawn/teleport/save manipulation was used to manufacture missing coverage.

Private artifacts: `reports/local/all-layout-runtime-20261020-080930/` contains
setup/backup, post-stop native samples, replay and cleanup; console is
`reports/local/all-layout-runtime-console.txt`. Raw media/checkpoints stay ignored.

## Verification

Using openspec-verify-change on bounded-combat-navigation, schema spec-driven;
status/apply context and all five planning files reread after scope amendments.
Separate self-review covered new producer bounds, capability dependencies, wire
validation, BFS/steering, default compatibility, original gate deadlines, health
and release handling, and learner isolation. No standalone synthetic RL smoke was
rerun: dependencies/config/model schemas are unchanged; real-wrapper normalization
and training regression tests are included in the full gate.

| Dimension | Result |
| --- | --- |
| Completeness | 9/10 tasks complete; seven ADDED/MODIFIED requirements have offline implementations/tests. Runtime task 2.2 incomplete |
| Correctness | Negotiation/default/legacy, mask validation and all shape captures: observer_client.py/navigation_wire.py/main.lua and production Lua tests. All-shape topology/steering/obstacles: room_path.py/test_room_path.py. Same-client bounds/freshness/cleanup/normalizer exclusion: combat_navigation.py and real-wrapper tests |
| Coherence | Measured current-room grid only, explicit v2, no direct fallback, all twelve shape IDs and eight slots, no encoded-map/model/reward change. Documentation/spec/design and implemented finite limits agree |

CRITICAL before archive: installed-game corrected transition and fresh combat
handoff remain not verified (task 2.2). In addition, per-shape native coverage is
explicitly incomplete in the table above. No other implementation critical issue,
warning or suggestion found in the checks that ran. Final strict validation and
diff whitespace check passed. No archive readiness or all-shapes installed-game
claim. Coverage-report task does not turn not_run cells into passes.

Next concrete check: a new bounded attach after two advancing gameplay frames,
traverse the existing narrow room with the v2 grid, and record destination combat
readiness. No automatic retry under this consumed budget. No commit/push/delegation;
all unrelated dirty work preserved.
