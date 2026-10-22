# Evidence: user-prepared cleared L room

User reported an L room with cleared neighbors and requested traversal. Initial
read-only probe in PID29928: active epoch5/visit5/frame3586, position
(837.21838378906,452.1552734375), four red half-hearts. Pause was not observed.
Hello lacked safe_actions/live_loop/navigation after a prior normal in-game exit.
No gameplay command was sent in that process. The agent closed it normally and
launched through Steam with a fresh authorization; no Steam options/save edits.
Actual post-Continue shape must be read back before movement.

One production seed21 random invocation after startup, <=1 combat decision only
if unexpected combat appears,90-second run cap,60-second gate cap,maxfaults0,
at most one natural death restart,disk512MiB. Navigation256 commands/90 pulse
seconds/four transitions/three stationary pulses. Startup capped120 seconds.
No PPO/training update, forced layout/reset, second invocation or automatic renewal.
Normal close immediately after runtime stop if active combat; otherwise verify
pause or close normally before slower evidence work. Fresh approval exact hash,
initial probe and full unchanged t5120/source preflight retained under
reports/local/current-l-cleared.txt's artifact directory. No observer deployment.

## Startup and measured room

New PID37996. Guarded capture/menu attempt refused foreground without input;
user selected file2/Continue. Latest game log loaded rep+persistentgamedata2.dat.
Startup completed within63/120 seconds before runtime. Readback was active,
epoch1/visit0/frame4509, index97, shape11/LBL, position(1080,280), four red
half-hearts. Room clear, no enemies. Native v2 mask28x16/448 cells, lower-left
concavity blocked; observed ordinary exits slots1/2/5/6. No pause claim despite
the requested setup. Installed observer0.5.0-dev, Lua5.3, no extender.

## Runtime result: passed observed LBL route

One production CLI invocation: live --mode random --seed21 --steps1 --minutes1.5
--max-faults0 --combat-gate --auto-navigate --gate-wait-minutes1
--confirmed-save-slot2 --connection-timeout15 (normal argument spacing used).
Logs runs/live/sessions/20261020-092822-8b80c8/ and
reports/local/l-cleared-console.txt. Exit0, handled four-transition cap after
14.015 seconds of gate wait/270 snapshots. Zero combat decisions/readiness,
reward, episodes or restarts; no model update. Cleared neighbors were sufficient
for traversal acceptance; no combat was needed or fabricated.

Goals recorded: index97/shape11/slot1 ->83/shape1/slot2 ->84/shape1/slot0
->83/shape1/slot3 ->96/shape11/slot1 (last goal stopped before movement).
Four native visit changes: exit the prepared LBL through upper slot1, traverse
the neighboring ordinary rooms, then enter LBL again. Large-room current indices
96/97 are recorded as returned; not evidence of two unique physical L rooms.
46 accepted movement pulses and46 releases,43 accepted releases/three rejected
at transitions. Each rejection was reconciled with a fresh same-epoch later visit
under the existing cap; no successful neutral acknowledgment is invented.
Zero stationary stop, resume race, observation gap, infrastructure fault or
cleanup error. No second invocation or budget renewal.

Coverage: real LBL capture and one upper-door route, not every exit/position,
all missing-corner detours, another L rotation or2x2. The policy never ran.

## Recovery, lineage and checks

Launcher sent normal WM_CLOSE immediately when the production process returned,
before evidence reads. Game shutdown/Observer unloaded log entries and process
absence confirmed; no listener remains. No post-close live snapshot or human
manual-control recovery claim. Navigation guards saw no damage/health stop, but
no final health snapshot was collected before immediate closure; initial health
was four half-hearts. Do not manufacture an exact final-health readback.

Exact temporary approval hash checked/file removed. Process closure removed cached
authority. Full t5120 model/normalizer reload, identity/hash comparison and latest
pointer unchanged. Source/installed main.lua+metadata comparison passed without
deployment; disk202115498 bytes <512MiB. Private setup/probes/cleanup are in
reports/local/l-cleared-20261020-092654/.

No production/dependency/schema change; previous1893-test/zero-skip full gate
retained, not rerun for evidence-only edits. Separate self-review distinguishes
observed shape11 traversal from unobserved layouts/exits and missing final-health
snapshot. Strict OpenSpec validation and whitespace check passed. Existing10/10
representative tasks retained; per-shape native coverage remains partial.
No archive/commit/delegation. Next: native2x2, LTL/LBR and other unobserved narrow
shapes under separately recorded finite checks; no automatic next run.
