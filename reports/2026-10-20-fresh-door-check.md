# Evidence: fresh-process doorway correction check

User launched Isaac for the next check after normal closure. Fresh PID35824;
game v1.9.7.17. One production random-policy seed21 attach, <=512 combat decisions,
three minutes, gate wait90 seconds, zero infrastructure faults, one natural death
restart; disk512 MiB. Navigation capped at256 commands,90 pulse seconds,four
transitions,three stationary pulses. No training/model update or automatic retry.
Menu-only input may enter file2/Continue and pause after cleanup.

Fresh approval created before production attach; no prior-process cached lease.
Full t5120 model/normalizer identity/reload/latest and source/installed Lua/metadata
comparison passed. No deployment. Setup/hash/private artifacts:
reports/local/fresh-door-20261020-090854/.

Latest game log loads/saves rep+persistentgamedata2.dat. Continue is selected in
the captured menu. Guarded Enter failed to acquire foreground and sent no input.
User pressed Continue and asked where to leave the player. The agent requested
the current room, without manual repositioning. One production runtime followed.

## Runtime result: traversal passed, combat scenario not reached

Command: live --mode random --seed21 --steps512 --minutes3 --max-faults0
--combat-gate --auto-navigate --gate-wait-minutes1.5 --confirmed-save-slot2
--connection-timeout15 (normal CLI argument spacing used in console).
Exit0, handled navigation-budget stop, not complete runtime acceptance.
Session4c18978d2b6e4507a457459a30db39e6; log directory
runs/live/sessions/20261020-090952-6e15df/; console reports/local/fresh-door-console.txt.
Handshake advertised both navigation capabilities; observer0.5.0-dev/Lua5.3,
no extender. The new process loaded the fresh approval successfully.

37 accepted movement pulses,37 release commands:35 accepted, two rejected during
room transitions and reconciled against fresh later visits by the existing guard.
Four native visit transitions,225 wait snapshots,11.437 seconds; zero combat
decisions/readiness/reward/updates/restarts and zero cleanup errors. Goals observed:
index81/shape7/left ->80/shape1/right ->81/shape7/right ->83/shape1/left
->82/shape7/left. Large-room indices are recorded as returned by native telemetry;
they are not treated as a full map or unique physical-room count.

The complete narrow-room obstacle route and far-right doorway now crossed rather
than stalling. Six two-frame alignment pulses were accepted. This exercises the
corrected production route, but does not isolate each fix in a controlled A/B
comparison. Stop was four-transition budget exhaustion, not a movement stall.
No extra invocation or budget renewal. All visited rooms remained clear; next
combat handoff is still not verified. Native evidence covers shapes1 and7 only;
2x2/rotated L/other narrow shapes remain offline-only.

## Cleanup and recovery

Guarded Escape refused focus and sent no input. User asked to press Escape;
pause is not claimed. Separate action-free bridge probe confirms alive/active,
epoch1/visit4/index82/shape7, frame20567, position(1080,280), four red half-hearts,
unchanged health. Player is at the right entrance of the long narrow room.
No listener remains. Exact temporary approval removed; cached authority can
persist until expiry/process exit, so on-disk removal alone is not revocation.
Full t5120 model/normalizer identity/reload/latest unchanged; disk202044690 bytes
<512MiB. Recovery by human/manual-control intervention is not measured.

## Verification and next action

No production changes, deployment, PPO or dependency changes. Prior full gate:
1893 passed, zero skips; not rerun for evidence-only changes. Separate self-review:
transition evidence is valid, task2.2 remains open because no fresh combat was
observed after travel. Do not archive or claim all-layout native acceptance.
Next finite check needs enough declared transition budget to reach an uncleared
ordinary room, with all original health/fault/command/wall limits retained.
Leave the character in this room; manual routing to a special layout is unnecessary
for continuing traversal acceptance. A later targeted shape check needs its own
recorded native scenario. The completed budget is not renewed automatically.
