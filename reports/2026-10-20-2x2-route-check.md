# Evidence: native 2x2 route

User prepared a large room and requested the check. PID34888, gamev1.9.7.17,
file2 confirmed by latest persistent-data load. Native action-free probe: paused,
epoch9/visit3/frame2530,index109,shape8/2x2,clear/no enemies, position
(534.09497070313,369.04373168945),four red half-hearts. Measured v2 grid28x16,
448 cells; open ordinary exits slot4(left-lower) and5(upper-right). Observer
0.5.0-dev/Lua5.3/no extender; source/main.lua+metadata match without deployment.
Full t5120 model/normalizer reload, identity/hash and latest unchanged before
actions. Fresh15-minute approval loaded; exact hash retained.

One production random seed21 invocation, <=1 combat decision only if unexpected
combat appears,90-second run/60-second gate cap,maxfaults0,at most one natural
death restart,disk512MiB. Navigation256 commands/90 pulse seconds/four transitions/
three stationary pulses. Menu-only unpause after listener setup; immediate normal
close on runtime return before slower evidence processing. No training/model
update, forced layout/reset/teleport, second invocation or automatic renewal.
Private setup/hello/probe: reports/local/room2x2-20261020-095856/.

## Runtime results: observed 2x2 routes passed

Production random CLI used seed21/steps1/minutes1.5/maxfaults0/combat-gate/
auto-navigate/gate-wait-minutes1/confirmed-save-slot2/connection-timeout15.
Logs runs/live/sessions/20261020-095915-ad12d7/ and
reports/local/room2x2-console.txt. Initial pause was honored. Guarded menu Escape
refused focus and sent no input; user asked to unpause. Subsequent bridge frames
became active and movement began within the original gate cap; no timeout renewal.
There was no explicit textual reply to the unpause request before completion.

Goals: index109/shape8/slot4 ->108/shape1/slot2 ->109/shape8/slot5
->84/shape1/slot1. Four native visit changes: left-lower2x2 exit, return into2x2,
traverse the measured safe grid to the upper-right exit, then travel onward.
Both selected2x2 routes physically completed. No screenshot route, direct blocked
fallback, hidden floor map or manual gameplay routing during the recorded travel.
Unmeasured human intervention is not ruled out by this report.

64 accepted navigation movement commands and64 releases,128/256 commands total.
62 releases accepted; two rejections at transitions reconciled under the existing
fresh same-epoch/later-visit/health/deadline checks, without claiming neutral acks.
Wait42.203s/826 snapshots including the initial pause; four transitions, no stall,
resume race, observation gap, infrastructure fault or cleanup error.

Final epoch9/visit7 contained combat. Fresh readiness for request
e12ff69ff4a10398b4e7571ea05f21e3 accepted; one permitted random combat decision
then normal step-limit exit0. Reward -0.001 is not gameplay-quality evidence.
No completed episode/clear/death/restart or training/model update. No second
invocation or automatic renewal. Native proof covers this obstacle mask and
slots4/5, not every2x2 layout, exit or starting position.

## Recovery, lineage and verification

Launcher requested normal WM_CLOSE immediately after runtime return. Process and
listener absence plus Observer unloaded / Isaac has shut down successfully verified.
Exact authorization hash checked/file removed; process closure removed cached
authority. Full t5120 model/normalizer reload, complete identity/hash/latest and
source/installed observer comparison passed unchanged. Disk202171859 bytes <512MiB.
No final live-health snapshot before prompt close; initial four half-hearts are
not presented as exact final health. No living-player pause/manual-control recovery
claim. Private setup/probes/cleanup retained in the artifact directory.

Evidence-only follow-up; no production/dependency/schema/deployment changes.
Previous1893-test/zero-skip full gate retained, not rerun for these edits. Separate
self-review maps native shape8 and completed slots4/5 routes to current measured
path requirements, preserving unseen shapes/exits as not_run. Strict OpenSpec
validation and whitespace check passed. Representative tasks remain10/10;
native shapes1/7/8/10/11 observed. Next: LTL/LBR and remaining narrow shapes2..6,
each under a separately recorded finite check. No archive/commit/delegation.
