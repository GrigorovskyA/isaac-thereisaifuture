# Evidence: all-layout navigation settling recheck

New user request to check the corrected runner. One Steam launch and file-2
Continue; one random-policy seed-21 invocation, <=512 combat decisions, three
minutes, 90-second handoff cap, zero tolerated infrastructure faults, one natural
death restart, 512 MiB training-tree limit. Navigation is bounded to 256 commands,
90 pulse seconds, four transitions and three stationary pulses. No training,
forced reset/room spawn, second invocation or budget renewal. Full t5120 identity/
reload and source-matching installed observer preflight passed before launch;
exact temporary approval hash retained. Startup cap 120 seconds before attach.
Runtime acceptance requires a real transition followed by fresh combat readiness;
unseen room shapes remain unverified.

## Runtime results

| Check | Result | Evidence |
| --- | --- | --- |
| Startup/profile | passed, assisted entry | One Steam launch, PID 45728/game v1.9.7.17. Initial capture showed FILE 2 selected. One menu Enter attempt refused focus before input; user then explicitly reported entering the room. No further selection/Continue keys sent. Initial read-only probe showed active room index 81, shape 7, frames 15541/15542/15544, four red half-hearts |
| Production attach | passed | Session `9ba28a1127c54255a015faa730850c32`, log `runs/live/sessions/20261020-082450-fd074f/`; v2 negotiation and fresh frame-advance guard active |
| Actual route | passed, partial goal | Goal index81/slot0 -> index80/slot2 -> index81/slot2. Two in-run native visit changes, 0 -> 1 -> 2. Exited the narrow room, returned, then routed toward its far right doorway. No screenshot-based route choices or gameplay keyboard input |
| Commands/bounds | passed | 36 accepted movement pulses and 36 accepted releases, 72/256 commands, 7.071862/90 cumulative pulse seconds, two/four transitions, zero/one restarts; 9.891-second wait, zero combat decisions/ready acknowledgments, zero cleanup errors |
| Stop | handled limit, target incomplete | At the far-door approach, repeated one-frame left corrections stopped moving; three stationary pulses stopped the run. Exit 0 is a handled stop, not next-combat success |
| Post-stop readback | passed | Separate read-only probe: active epoch1/visit2/index81/shape7, frame16971, position (1089.7366943359,288.58288574219), unchanged four red half-hearts. Planner replay at this point requested left/1 for the right exit, up/1 for the left exit |
| Recovery/cleanup | passed, agent check | Menu Escape opened visible pause menu with two full hearts. Game left open on pause, no active client/listener. Exact approval hash removed; full t5120 model/normalizer identity/reload and latest unchanged, disk 202,020,389 bytes <512 MiB. No human manual-control recovery/non-intervention assertion |

The settling guard is now exercised in a real running session with two successful
transitions. Entry was assisted and already advancing before attach, so this does
not separately prove an immediate automatic Continue/loading recovery window.
Runtime task 2.2 remains incomplete: next combat/readiness was never reached.
No learned-policy update, achieved room-clear outcome or progression claim.

## Offline correction after the completed attempt

Production Lua action_guard expires held input when game frame >= until_frame;
the command sets until_frame=frame+frames. A one-frame lease can expire at the next
input sample before movement. The native stall and replay are consistent with this
sampling boundary; no callback trace was enabled to claim exact input timing.
Navigation now uses minimum two/maximum six-frame leases; the stationary detector
and alignment tolerance remain unchanged. Combat action schemas/repeat are untouched.

Review also identified a doorway-crossing edge: after an outward pulse, the player
may be past the interior approach while still in the old room. Continue outward
only within the selected observed open door's narrow approach-to-boundary corridor,
with a safe measured approach and <=8-unit perpendicular displacement. Do not
recenter backwards or permit a general fallback through blocked cells. Closed doors
still reject the route. New tests cover all eight slots plus the observed native
alignment offset with a one-input-frame sampling margin.

Management logs now include goal shape/grid dimensions and action reference/ack
frames/positions. These fields remain outside policy/normalizer/reward input.
Targeted tests: 91 passed, exit 0, 2.89 seconds. Final Check.ps1 passed, exit 0:
1893 tests, zero skips, 45.97 seconds; lint/format/mypy/pip and strict OpenSpec
31/31 passed. Final whitespace and updated strict validation passed.
No second gameplay invocation, budget renewal or post-fix runtime claim.

Private artifacts: `reports/local/layout-settling-20261020-082401/` (setup, probes,
cleanup); console `reports/local/layout-settling-console.txt`; final pause image
`reports/local/settling-paused.png`. Raw media/checkpoints remain ignored.

## Separate self-review and OpenSpec verification

Using bounded-combat-navigation/spec-driven: current status/apply context and all
artifacts reread. Seven ADDED/MODIFIED requirements remain implemented/tested;
new minimum-lease and partial-crossing scenarios map to room_path and nine new
regressions. Review confirms unchanged alignment/stall/health/deadline guards,
closed-door rejection and no generic blocked-cell fallback. Management log fields
stay outside learning. Final completeness is 9/10 tasks; critical before archive:
task 2.2 still needs destination combat and fresh readiness after corrected routing.
Per-shape full native coverage also remains incomplete. No other critical issue,
warning or suggestion found in checks that ran. No archive/commit/delegation.

No synthetic RL smoke rerun: no dependency/config/model schema changes; the full
suite includes real-wrapper normalizer/sample-separation and training regressions.
Post-close preflight was not run because the user-visible game remains open on
verified pause; installed main.lua/metadata byte comparison passed without writing
or deploying anything into the running game. New two-frame/crossing corrections
are Python-only and have not been run in Isaac in this completed budget.
