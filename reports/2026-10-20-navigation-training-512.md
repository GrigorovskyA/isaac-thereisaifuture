# Experiment: gated PPO continuation with production navigation

User accepted one training experiment: resume seed20 checkpoint
1f4a187e-s20-t5120 with its saved normalizer, collect512 new combat steps to
target5632, at most10 minutes and two natural death restarts. No second invocation,
automatic budget renewal, fresh initialization, save/Cloud/Steam-option edits,
deployment or forced room/reset. Startup/menu preparation capped120 seconds before
runtime. Approval expires15 minutes after setup, max_restarts2. Ordinary-room
navigation stays bounded to256 action/release commands,90 cumulative pulse
seconds,four transitions and three stationary pulses, without renewal across
handoffs. Gate wait90 seconds per handoff; maxfaults0; disk512MiB.

User explicitly deferred installed-game checks for narrow shapes2/IH,3/IV,5/IIV.
They remain not_run, with offline tests passed; this is not all-layout native
acceptance. Native representative routes cover nine of twelve shape families.
Special/boss/locked-room routing remains outside navigation scope.

Preflight passed with Isaac absent and installed observer/source byte match.
Config configs/training-live-v1.yaml hash
1f4a187ebea6a6e9e58946f44504b6354425334fe7d0fcf6fff850fdb79499a5,
CPU RecurrentPPO,n_steps256,n_epochs4,batch64,seed20 override; schemas unchanged.
Full parent model/normalizer identity/reload/latest passed. Parent PPO updates80,
normalizer count5125.0001; runs/live disk202284729 bytes. Fresh exact approval
hash/setup recorded in reports/local/navigation-training-20261020-103101/.
Steam launch requested after preflight; actual file2/game state must be read back.

Success requires512 checkpointed combat decisions, two full PPO rollout updates,
valid t5120 ->t5376 ->t5632 lineage, finite changed policy tensors, normalizer
reload, bounded navigation/restart/cleanup and evidence of actual fresh combat.
If a limit/fault interrupts a rollout, record saved versus unsaved samples and
preserve the latest complete checkpoint. No learning-quality/progression claim
from one experiment. Close normally immediately after runtime stop before slow
evidence processing.

## Runtime result: stopped before a complete PPO rollout

Steam launch PID43196/gamev1.9.7.17. Capture already showed active combat; the
agent did not send file-selection/Continue keys, so menu-entry assistance is not
attributed to the agent. Latest persistent-data load confirms file2. Agent menu
Escape paused successfully; action-free bridge probe: epoch1/visit0/frame3821,
index82/shape1, five red half-hearts,room_clear=false,three enemies at HP3 each.
Startup66/120 seconds before runtime. Production CLI then negotiated v2; one
guarded menu Escape unpaused and fresh combat readiness was accepted.

Command: live --mode train --config configs/training-live-v1.yaml --resume
--seed20 --steps5632 --minutes10 --max-faults0 --combat-gate --auto-navigate
--gate-wait-minutes1.5 --confirmed-save-slot2 --connection-timeout15 (normal CLI
spacing used). Logs runs/live/sessions/20261020-103208-c397cd/ and
reports/local/navigation-training-console.txt; sessionc51f3628b35d405ea9a94d3bc6279987.

| Check | Result |
| --- | --- |
| Resume/readiness | passed, parent loaded; fresh request2274b9df627c850c55e0a9b2220f5e15 accepted |
| Combat decisions | 21/512 new decisions; first segment ended empty, reward7.475666666666664 |
| Saved learning | failed target: zero complete rollout/PPO updates/new checkpoints;21 unsaved samples |
| Handoff | stopped: No open ordinary-room exit, about0.15s after empty handoff began |
| Bounds | one invocation, zero navigation pulses/transitions/restarts, no renewal; zero cleanup errors |
| Recovery | immediate normal WM_CLOSE on process return, shutdown/Observer unloaded verified, process/listener absent |
| Lineage/cleanup | full t5120 model/normalizer identity/reload/latest unchanged, PPO updates80,normalizer count5125.0001; t5376/t5632 absent; exact approval removed;disk202291492 bytes |

Approximate oracle events recorded three enemy kills, last at frame3900. The
gate classified empty, which means room_clear was still false; no confirmed room
clear event was collected. The native log shows a pickup initialized after peer
disconnect. These records support a post-combat update/door-opening race as a
hypothesis; they do not establish actual door-open timing or exclude a floor
with no eligible ordinary exit. No extra game launch/probe was used to manufacture
that missing evidence. Exit0 is a handled stop, not training success. The generic
top-level budget message says wall time, but rollout_accounting names the actual
No open ordinary-room exit stop; the10-minute cap was not reached.

## Offline correction after the consumed experiment

The production manager previously stopped immediately when an empty uncleared
room reported no open ordinary exits. Add a maximum two-second context-bound
no-action wait, within original gate/run limits, with health checks and no renewal
on paused/frozen frames. Cleared rooms with no prior settling interval still stop
immediately. Returning combat needs existing fresh readiness validation. No policy,
reward, normalizer, wire or checkpoint schema change. Revised OpenSpec artifacts
and behavioral tests track this correction; new runtime task4.3 remains pending.
No second training invocation or approval renewal under this completed budget.

## Verification and remaining runtime task

Targeted corrected suite:28 passed in2.60s, exit0. Nine added behavioral cases
cover delayed opening/room_clear-before-door, returning combat with fresh
readiness, persistent no exit, pause/frozen frames, health damage, original gate
deadline and immediate stop for an already cleared room without exits. Real
VecNormalize reset test admits exactly one reset observation, no waiting samples.
Initial targeted invocation reached passing tests but exited1 during pytest
cleanup on an inaccessible existing system-temp symlink. A fresh project-local
TEMP/TMP fixed the test environment without deleting unrelated temp contents;
targeted and full checks then completed successfully.

First full gate passed1901 tests/zero skips in46.32s. Separate self-review added
the room_clear-before-door regression and same-timer handling; final full
Check.ps1 passed1902 tests,zero skips,44.92s,exit0, lint/format/mypy/pip and strict
OpenSpec31/31. Log reports/local/exit-settling-final-check.txt. No dependency/model
schema change, so no separate synthetic smoke; full suite includes training/
normalizer/rollout boundary regressions. No further game invocation.

Using openspec-apply-change and openspec-verify-change on
bounded-combat-navigation/spec-driven: root/status/apply context and planning
artifacts reviewed. Separate self-review checks context-bound timer, no movement
during wait, no extension on pause/frozen/clear-flag change, health stop, strict
navigation validation, unchanged fresh-readiness path and zero waiting learning.
Seven ADDED/MODIFIED requirements mapped to the same modules/tests; two new
post-combat scenarios map to combat_navigation.py and the new fake-clock cases.
Completeness12/13 tasks. Offline correctness/coherence passed; CRITICAL before
archive: new task4.3 must observe post-combat opening and checkpointed training
in a new finite game session. Native door timing remains unproven; no claim the
512-step target was completed. The actual remaining requested learning
is512 checkpointed steps from unchanged t5120, since21 partial steps were lost.

User-deferred native narrow shapes remain not_run, not passed. Nonblocking
diagnostic limitation: the top-level training stop message still labels any
LiveBudgetExpired subclass as wall time; use the recorded rollout_accounting
reason for this attempt. No independent-review, improvement or progression claim.
No archive/commit/delegation or automatic approval/budget renewal.
