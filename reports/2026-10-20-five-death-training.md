# Experiment: up to five deaths with continued PPO learning

User explicitly requested more samples and automatic new attempts after death,
up to five deaths. New game runs reset gameplay only: retain seed20 checkpoint
t5120 and its normalizer. Initial normal New Run on file2, then at most four
natural-death restarts; no save edits/unlock/reset commands or fresh model.

Initial production training invocation target9216 (4096 new combat steps), at most
30 minutes or five observed terminal deaths, whichever comes first; maxfaults0,
disk512MiB,gate90s. Lua approval max_restarts4,35-minute lease. Explicit
navigation budget scale5:1280 action/release commands,450 cumulative pulse seconds,
20 transitions; same2..6-frame pulses,three stationary pulses,health-change stop,
two-second door-settling and original gate/run limits. Counters do not renew on
death/handoff. Menu/startup cap180 seconds after final checks. Normal close
immediately after runtime returns. No automatic budget renewal. The recovery
amendment below replaces the initial single-invocation plan under the same global
caps after a newly observed delayed native callback.

The prior512-step session preparation was superseded before any learner call,
closed normally and its exact approval removed. User-deferred native shapes2/3/5
remain not_run; special/boss/locked-door routing remains excluded. A navigation
limit or missing route can stop this experiment before five deaths; maximum five
is not a promise to force five complete runs or to finish the floor.

Implementation: explicit --max-deaths5 checked before another request/reset,
paired with four native restarts; optional --navigation-budget-scale5. Defaults
remain no explicit death cap and256/90/4 navigation limits. Invalid/noninteger/
ungated combinations reject. No policy/normalizer/wire/config hash change.
Training logs now retain the actual budget-stop reason instead of always
mislabeling it wall time. Completed256-step rollouts checkpoint normally;
partial rollout samples at death/budget stop remain unsaved and reported.

Offline targeted checks:64 passed in3.38s,lint/format/mypy passed. Initial new
test expected a separate normalizer count for VecEnv auto-reset; corrected that
test assumption because reset observations substitute inside steps. Five real
fake-world death episodes verify stopping before a sixth reset/request/action;
scaled multi-fight test passes more than four native visit changes without extra
normalizer samples. Full Windows Check.ps1 passed,exit0; log
reports/local/five-death-check.txt. Separate self-review/OpenSpec verification
checks default compatibility, strict options/CLI plumbing, cumulative limits,
fifth-death stop before request/reset, unchanged release and learner separation,
and actual stop-reason/partial-rollout accounting. No policy/schema/Lua change,
no synthetic smoke rerun; real-wrapper training regressions are in the full suite.
Native experiment results pending; offline death sequences are not game proof.

## First native invocation and bounded recovery amendment

New file2/Isaac run prepared manually after agent menu focus refusal; startup42s.
PID40792/gamev1.9.7.17,initial native clear start,index84/shape1,epoch1/visit0,
six red half-hearts. Setup reports/local/five-death-20261020-105504/.
Command live --mode train --config configs/training-live-v1.yaml --resume --seed20
--steps9216 --minutes30 --max-deaths5 --navigation-budget-scale5 --max-faults0
--combat-gate --auto-navigate --gate-wait-minutes1.5 --confirmed-save-slot2
--connection-timeout15 (normal option spacing used). Logs
runs/live/sessions/20261020-105602-7852a9/ and reports/local/five-death-console.txt.

188 combat decisions, zero deaths/restarts, zero complete rollout/checkpoint/PPO
updates;188 unsaved samples. Native post-enemy settling wait was observed and
an ordinary exit opened afterward; actual navigation resumed. Two room changes
before that fight, then traversal toward a left door. Last accepted outward
action referenced frame2250/ack2251; accepted release, then grid replan stopped
as blocked. Native game log shows Starting room transition at2260, after the stop.
This is direct delayed-callback evidence, not proof the interior route was blocked.
Summary wait10.812s, zero resume races/observation gaps/cleanup errors. Exit0,
normal immediate closure, process/listener absent, exact approval removed and
full t5120 identity/model/normalizer reload/latest unchanged.

Offline correction retains the eight-unit door corridor and blocked-cell checks.
Only after a final outward approach pulse, poll without input for <=0.5s after
release, within existing pulse/gate/run caps. Validate same session/epoch,health
and actual native visit; if no transition occurs, any next action still needs a
fresh valid measured route. Targeted44 tests pass, including accepted release
with delayed transition, absent transition, damage, foreign epoch and original
deadline. No extra movement/fallback or invented neutral acknowledgment.

The agent announced one recovery continuation within the ORIGINAL global budget,
not a fresh30 minutes/4096 steps/five deaths. Original runtime start
1792486562.7515984, absolute deadline1792488362.7515984.188 decisions already
spent, zero deaths/restarts. Recovery resumes t5120/Continue in the same game run,
not a new random game or model. At most3840 further decisions (complete256-step
chunks), target8960; total at most4028 <=4096. Navigation scale4 on recovery
allows1024/360s/16 transitions, within original1280/450s/20 after accounting for
the first invocation. Remaining wall time is recomputed after menu setup; approval
expires no later than the original absolute deadline. No further recovery/retry.

Final correction Windows gate:1920 passed,zero skipped,44.55s; lint,format,mypy,
pip consistency and all31 strict OpenSpec validations passed,exit0. Log:
reports/local/door-callback-check.txt. No production change after this gate.

Recovery startup used agent menu navigation on file2/Continue, then an observed
death occurred before the controller attached. Count that death and the normal
game-over Space restart against the GLOBAL budget. Thus recovery training uses
--max-deaths4 and approval max_restarts3, not five/four again. The model remains
t5120. Menu setup took214s: the local180s preparation cap was exceeded and
explicitly superseded before training by the unchanged original absolute global
deadline. This is an exception, not a passed180s check. No further recovery is
allowed. Recovery PID28932; session runs/live/sessions/20261020-110829-df9a80,
bridge879207079e6b47af800c719e58b5e9ed, mod0.5.0-dev/Lua5.3. Runtime command
resumes seed20,target8960,remaining17.55min,max-deaths4,navigation-scale4,
maxfaults0,combat-gate/auto-navigate,gate90s,file2,connection15s. Exact approval
and parent hashes/global accounting are in the ignored recovery/setup.json.

## Final native results

Recovery passed its step target,exit0:3840 combat decisions,all3840 checkpointed,
zero recovery unsaved samples. Runtime429.922s; original global elapsed1180.111s
(19m40s), within30min including first invocation, correction/checks and startup.
Combined4028 decisions=188 first unsaved+3840 learned; no budget renewal.
Checkpoint chain:15 complete256-step children from t5120 through t8960, latest
1f4a187e-s20-t8960. Full reload/hash/schema/config/seed/parent-chain validation
passed for every child; all20 policy tensors finite and changed at each update.
Parent identity unchanged. PPO updates80->140,normalizer count5125.0001->8966.0001
(3840 steps plus initial reset observation). No management samples were inserted.
Disk353032593 bytes <512MiB. Verification stored locally in verification.json.

Recovery:8 fresh accepted handoffs,24 movement/release pairs,2 native transitions,
13.141s management wait; zero rejected readiness,resume races,observation gaps,
withheld actions or cleanup errors. One59-step death then a confirmed autonomous
restart old_epoch2->new_epoch3; new session identity after reconnect was
d4590ba74cfb41f5b6b7cd4ecb12c73d. Six60-second combat segments ended unknown
(548/537/553/565/565/571 decisions); last442 decisions ended at the training step
budget, without an invented terminal outcome. These are combat segments, not
six additional deaths or full runs. Total recovery reward -65.922333 is a training
signal, not an improvement measure. The surviving run remained in its first fight;
no full-run/room-clear success or comparative policy improvement is established.

Global observed deaths2 (one startup,one controller),restarts2 (one normal menu,
one native death restart). The five-death ceiling was not reached; the actual
fifth-death stop remains offline-covered only. Global122 navigation commands and
4 transitions are within1280/20. All recovery navigation occurred inside13.141s
of gate waits; adding first invocation's entire34.761s gives a conservative
47.902s upper bound for cumulative pulse time, below450s.
Both actual recovery transitions used rejected-release reconciliation; the new
accepted-release waiting branch was not exercised natively. The first invocation
observed post-combat exit opening but saved no checkpoint; recovery saved training
but did not clear that fight. Therefore task4.3 remains pending as an end-to-end
post-clear/checkpointed-continuation condition; do not combine disjoint observations
into proof of that sequence.

Normal WM_CLOSE immediately after return; process absent on follow-up, native log
reports Observer unloaded and successful shutdown,port9528 listener absent.
Exact matching recovery approval removed. No game/save/Cloud/options edits or Lua
deployment. No further game invocation. Initial New Run was user-assisted;
recovery menus were agent-operated, so fully unattended startup is not claimed.

## Separate self-review and OpenSpec verification

Completeness: experiment and bounded recovery evidence recorded (tasks5.3/6.2);
task4.3 remains pending. Correctness: diff/spec/test review confirms strict option
validation, cumulative limits across handoffs/deaths, release before death-cap
reset check, fresh context validation, no-input callback wait and unchanged
policy/oracle separation. Accepted-release and fifth-death native conditions are
not verified; offline behavioral checks passed. Coherence: existing gate subclass,
typed CLI options, unchanged model/config/schema lineage and fail-closed measured
routes follow design. No further code issue found in this separate self-review;
it is not independent review. Strict validation and git diff --check passed,exit0.
No archive: pending end-to-end condition and user-deferred shapes2/3/5 remain
explicitly unobserved. Next: diagnose the prolonged surviving fight from recorded
combat/oracle events before selecting another finite experiment.

Current checkpoints are development training, not disposable mocks. Retain them
for integration and regression work. A later clean training baseline may start
from scratch in a separate lineage once observation/reward/episode contracts are
stable; do not overwrite this lineage or silently reset on resume.
