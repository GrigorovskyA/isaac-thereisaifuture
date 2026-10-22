# Evidence: user-prepared large layout

User prepared a cleared large ordinary room and authorized the check. New game
PID29928, Repentance+v1.9.7.17, latest persistent-data load file2. Initial action-free
probe: active epoch1/visit1/frame1341, index71, shape10/LTR, position
(264.46334838867,347.08493041992), six red half-hearts. Open ordinary exits slots
1/3/6; measured v2 grid28x16,448 cells with the upper-right concavity blocked.
Native telemetry is actual installed-game data, not a synthetic shape fixture.

One production random-policy seed21 invocation: <=64 combat decisions, two minutes,
90-second gate wait, maxfaults0, at most one natural death restart, disk512MiB.
Navigation256 commands/90 pulse seconds/four transitions/three stationary pulses.
No PPO update, forced layout/teleport/reset, second invocation or automatic renewal.
Installed/source Lua+metadata comparison and full t5120 model/normalizer identity/
reload/latest passed before actions. Fresh15-minute authorization loaded by this
new process, exact on-disk hash retained. Observer0.5.0-dev/Lua5.3/no extender.
Private setup/hello/probe: reports/local/large-layout-20261020-092147/.

## Runtime results

Production random CLI used seed21/steps64/minutes2/maxfaults0/combat-gate/
auto-navigate/gate-wait-minutes1.5/confirmed-save-slot2/connection-timeout15.
Logs runs/live/sessions/20261020-092210-2f66b3/ and
reports/local/large-layout-console.txt; sessionb7569de4eb68455fa04f23b47411a41d.
Exit0 after the64-decision limit, about10.34 seconds after invocation.

LTR goal index71/shape10/grid28x16/slot1. Eleven accepted movement pulses with
eleven releases: ten accepted; the final rejection was reconciled with a later
same-epoch room visit under the existing bounded transition guard. Actual native
visit1 ->2, fresh combat/readiness accepted, combat resumed after3.109s. No
stationary stop, resume race, observation gap or cleanup error.64 random combat
decisions, no completed episode/clear/death recorded during the runtime, no
training or model update. No restart or second invocation.

This confirms the real v2 LTR mask and one bounded route to its upper exit, then
fresh combat handoff. It does not prove a route around every part of the L void,
the secondary exit slot6, another L rotation, a full2x2 or gameplay quality.

## Recovery limitation and cleanup

Important post-stop sequence: Lua log records Peer disconnected, then Game Over,
then Game exited; observer closed. The character died in the still-active combat
after the runtime had released input and stopped. Agent Escape successfully sent
a menu key later; capture shows the main menu with Continue disabled, not a living
paused character. Action-free post-probe timed out because no active-game peer
connected. Final health/state therefore not confirmed by a bridge snapshot.
Do not count this as successful live-player pause recovery, a runtime episode
death, or an observed human intervention. Future tests ending in combat should
close normally immediately on stop before slower evidence processing unless
pause is already verified; releasing input alone does not freeze enemy activity.

Exact approval hash checked and file removed even after failed readback. No
port9528 listener remains; game left at main menu. Full t5120 model/normalizer
reload, complete identity/hash and latest pointer comparison passed unchanged.
Disk202088043 bytes <512MiB. Cleanup JSON in the private artifact directory.
Cached authority is not claimed revoked by file removal alone; the normal
in-game exit path logged closure, and the file is absent for a subsequent load.

## Verification and next action

Evidence/documentation only, no production/dependency/schema changes or deployment.
Prior1893-test/zero-skip full gate retained; not rerun for these edits. Separate
self-review distinguishes successful shape10 traversal from failed post-stop
living-player recovery. OpenSpec10/10 representative tasks remain satisfied;
the per-shape report now adds only the observed LTR route, leaving other native
shapes/rotations explicit not_run. No archive/commit/delegation.
Next native scenario: cleared2x2 or another L rotation, with prompt normal close
if the bounded test ends in active combat. A new runtime requires its own finite
budget; this completed test is not automatically renewed.
