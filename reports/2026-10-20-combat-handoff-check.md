# Evidence: navigation to fresh combat handoff

User authorized continuation after the four-transition doorway test. Preflight
read-only probe: same PID35824, epoch1/visit4/index82/shape7, active and clear,
four red half-hearts. The prior observed route and current probe showed clear
rooms; this did not establish a full floor map or prove absence of other fights.
Special/boss-room routing remains excluded. User then manually prepared a room
with access to uncleared ordinary combat and reported ready. Exact destination
will be recorded from bridge data, not inferred from the user's message.

One production random-policy seed21 invocation, <=512 combat decisions, three
minutes, gate wait90 seconds, maxfaults0, at most one natural death restart,
disk512MiB. Navigation256 commands/90 pulse seconds/four transitions/three
stationary pulses. No training, forced reset, second invocation or automatic
renewal. Reuse only the current process's still-valid cached authorization expiring
at1792481034; no new file or lease extension. Full t5120 identity/model/normalizer
reload/latest verified before probe. Setup/probe:
reports/local/combat-handoff-20261020-091305/.

## Observed traversal and combat

Production command (normal option spacing): live --mode random --seed21 --steps512
--minutes3 --max-faults0 --combat-gate --auto-navigate --gate-wait-minutes1.5
--confirmed-save-slot2 --connection-timeout15.
Logs: runs/live/sessions/20261020-091415-a8e612/ and
reports/local/combat-handoff-console.txt. Same game v1.9.7.17, observer0.5.0-dev,
Lua5.3, no extender. Native v2 negotiation succeeded. No observer deployment.

Initial request f6a9869292bc0be003837394eaed7e67, session
62d46f5def52462098a90c8783933843. Initial bridge state was active/cleared,
epoch1/visit5. Goals: index80/shape1/right ->81/shape7/left ->80/shape1/down.
Three native visit changes reached combat in epoch1/visit8. Automatic readiness
at1792480462.5586455; existing token/context validation accepted it at
1792480462.6101396; fresh reset resumed combat at1792480462.6537051.
First handoff wait6.656s. This is actual travel followed by fresh combat, not only
an on-disk readiness file or successful handshake.

| Episode | Combat decisions | Outcome | Approximate oracle diagnostics |
| --- | --- | --- | --- |
| 1 | 418 | death | Four half-hearts lost,13.5 enemy HP removed,one enemy kill |
| 2 | 85 | death | Six half-hearts lost,10 enemy HP removed,one enemy kill |

The configured one natural death restart occurred: epoch1 ->2, fresh transport
session ca8efccc64794a03a48a84938e2788a5. New start-room goal index84/shape1/left
crossed one more doorway; a distinct readiness request
a95a350febe88e5db0d81dcdd7a96964 was accepted in epoch2/visit1 and combat resumed
after8.063s. Total four transitions; counters were not renewed after death.
After the second death no further restart occurred. Both episodes failed to
clear a room. These are random-controller integration results, not learned-policy
evaluation, training progress or achievement evidence. The log's scenario split
label train does not mean PPO updates occurred in random mode.

31 navigation movement commands and31 releases;28 accepted releases and three
transition rejections reconciled against later same-epoch visits under the
existing bounded guard. No successful neutral acknowledgment is inferred for
rejections. Navigation remains outside combat decisions/reward/model input;
503 combat decisions total. All-shape implementation remains offline-tested;
native route coverage in these checks is shapes1 and7 only.

## Stop, recovery and lineage

Exit0 at1792480614.2361145, about158.81 seconds after invocation. After the
second death, readiness never arrived and the original90-second gate cap ended
the run: CombatGateExpired, not success at clearing a room. Summary: three
handoffs, two accepted readiness requests,503 combat decisions, four room changes,
2053 wait snapshots,104.719 cumulative wait seconds, two deaths; no resume races,
observation gaps or cleanup errors. The cumulative navigation counters survived
the restart. No second invocation, extra restart or lease renewal occurred.

Post-stop action-free probe: epoch2/visit1/frame433, paused/dead, index83/shape1,
zero health and two remaining enemies. A guarded Escape attempt during the final
wait had refused focus without sending input; pause is not attributed to that
attempt. Normal WM_CLOSE then closed the game. Process and listener absence plus
Observer unloaded / Isaac has shut down successfully verified. No human
non-intervention/manual-control recovery assertion: scenario preparation was
explicitly manual; the game is now closed.

Approval file remains absent; closing the process removed its cached authority.
Full checkpoint1f4a187e-s20-t5120 model+normalizer reload, complete identity/hash
comparison and latest pointer passed unchanged. Source/installed main.lua and
metadata comparison passed without deployment. Disk202076442 bytes <512MiB.
Cleanup JSON and post-probe retained in the private artifact directory.

## Separate self-review and OpenSpec verification

Using openspec-verify-change, bounded-combat-navigation/spec-driven. Local root,
status/apply context and all five planning files reread; explicit task2.2 checked
against the recorded telemetry, native transitions, two fresh readiness/resume
sequences, cleanup and unchanged parent identity. Task2.2 is now satisfied;
coverage-report task3.4 still explicitly records unseen native layouts as not_run.

| Dimension | Result |
| --- | --- |
| Completeness | 10/10 tracked tasks, seven ADDED/MODIFIED requirements mapped; representative installed-game acceptance passed |
| Correctness | Negotiation/bounds/default/legacy: observer_client.py, navigation_wire.py, main.lua and Lua/wire tests. Geometry/leases/crossing: room_path.py and all-shape route tests. Gate deadlines/freshness/release/restart/learning exclusion: combat_navigation.py, base gate, and real-wrapper normalizer tests |
| Coherence | Same-client management, no hidden floor map or model/reward/schema change; native telemetry and readiness proof match the specified behavior and finite limits |

Prior final Windows gate remains1893 passed, zero skips, lint/format/mypy/pip and
OpenSpec31/31. No production changes since that gate; full suite/synthetic RL
smoke not rerun for evidence/task-status edits. Current strict change validation
and whitespace checks passed. No implementation critical issue found in the
checked scope. Remaining limitation: native evidence is only shapes1/7; no claim
that every rotated L/2x2/narrow layout was exercised. No archive/commit/push or
delegation. Next: targeted native checks for the remaining shape families, then
a separately specified bounded training experiment if requested.
