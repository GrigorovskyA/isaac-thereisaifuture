# Evidence: four-hour continuation startup

Current outcome update (2026-10-21):the attempt ended early and the user stopped
further overnight execution. No training process is active. Latest t7424 is saved;
see the final early-stop section below and the [readiness plan](2026-10-21-long-run-readiness-plan.md).
The startup observations below are historical evidence,not current process state.

- Date:2026-10-21,Europe/Amsterdam.
- Base revision:9e0f30a819aea0ff7998675ebb34faa82ac69357 plus reviewed comparator/configuration/preparation.
- [Declared plan and retained startup correction](2026-10-21-overnight-plan.md).
- Scope:separate native scripted damage comparator,then time-dominant continued learning on existing code. No learned-policy/reward/observation/action changes.
- Python3.12.14,observer0.5.0-dev,Lua5.3;current native hello game/build metadata unavailable. Existing file2 profile,Steam launch options and third-party mods retained.

## Verification and diagnostic comparator

| Check | Command/evidence | Exit | Result |
|---|---|---:|---|
| Comparator behavior | pytest tests/test_diagnostic_baseline.py -q | 0 | 4 passed:open/aligned shots,known blocker,local route,closed space,no enemy,invalid shape,absolute-position independence |
| Targeted stack | Run-NightChecks.ps1 | 0 | 108 passed,no skips |
| Full Windows gate | Check.ps1 via finite driver | 0 | 2048 passed,zero skipped;Ruff/124 formatted files,mypy52source files,pip clean,OpenSpec40/40 |
| Frozen artifacts | Primary independent SHA256 readback | 0 | 188 baseline paths unchanged |
| Native baseline | run_approach_baseline.py | 0 | 224 decisions,19 enemy-damage events totaling66.5HP;zero deaths/faults |
| Baseline shutdown | Native journal/result/primary free-port check | 0 | Owned game closed,approval removed,t6912 unchanged |
| Budget lineage | Byte comparison/config comparison/strict manifest load | 0 | Exact model/optimizer/normalizer/RNG retained;all nonbudget keys identical |
| Initial overnight startup | launch_overnight.py | 1 | Stopped before game/learner due fractional-clock lease deadline assertion;cleaned approval,153 frozen hashes,zero learning |
| Corrected lease calculation | Three fractional-clock cases against actual approval writer | 0 | Expiry fits fixed deadline with margin;4hour allowance preserved |

Initial comparator assertion expected no right movement even with a blocker60units away;inspection showed an initial20unit right step was valid before the detour. The test was corrected to an immediately blocking20unit obstacle,which verifies the intended collision-avoidance behavior. No production checks were weakened.

Baseline native session87b6237026a64c5c98efa59bddf80f30,epoch1,initial frame14962,active Isaac(type0),fresh [Continue,2],seed AZEX27H7. One accepted combat handoff,224 decisions,63.89s outer,exit0. Final gate classification was empty;last pre-action oracle still recorded3HP androom_clear=false. Therefore report damage and an empty export boundary,not an independently sampled room-clear or exact kill count. Oracle enemies initially totaled90HP;conservative damage events66.5HP. Missing entities are not credited as kills. Pure comparator uses exported observation only,does not learn and supplies no demonstrations to PPO.

Gate driver62.91s,sampled temp grew73,964,807bytes within512MiB;primary read stage exits and independently rehashed frozen files. Native diagnostic used at most512decisions/180s controller,300s outer,one-death/no-restart stop,zero faults,retries0,256MiB outputs. No source/config changes during the worker run. Raw local evidence:reports/local/approach-baseline/ and runs/approach-baseline-20261021/.

## Explicit continued lineage

Original parent08e0d262-s20-t6912 remains immutable. Budget-only descendant7d53f55f-s20-t6912 in runs/live-conservative-v2-overnight-20261021/,seed20,config7d53f55f92aae137da716f2916e4cc18db2c2594ef76bb58d2104bdb1e7ce4ee. Binary model/optimizer and normalizer were copied exactly,RNG preserved;only manifest id/config/parent and budget keys changed. Provenance in run-root budget-extension.json.

The four-hour config retains all prior PPO and conservative-v2 coefficients. It has one-billion timestep sentinel,240minutes and32GiB emergency disk. No max-deaths argument;5000restart approval sentinel cannot bind within4hours with4second minimum dispatch spacing. These are finite schema values,not literal infinite counters. Time/infrastructure/resource/focus guards remain. Completed256-step rollouts save;last incomplete rollout may be unsaved. No inference from changed weights to improved play.

## Corrected launch

Primary verified the corrected launch and actual first complete update at02:05:30.
Supervisor PID42224,learner48876,Isaac42828 were alive. Native session
9e722afa5c48435f8c24180de3a281ee,epoch1,initialframe15963,active Isaac(type0),
fresh file2 Continue verified with seven keys. Supervisor start02:03:12;training
record02:03:34;240minute learner window ends approximately06:03:34. Fixed outer
cleanup deadline06:05:12,earlier than declared06:17 latest bound.

First complete checkpoint7d53f55f-s20-t7168 has parent7d53f55f-s20-t6912.
Primary independently loaded both trusted local policy states:all20/20 tensors
changed,PPO updates108->112. Observation count6914.0001->7171.0001 and return
count6912.0001->7168.0001;normalization state continued rather than reset.
All156 frozen source/config/helper/parent files rehashed unchanged. Raw receipt:
reports/local/overnight-primary-start-verified.json. This proves a resumed native
PPO update,not improved gameplay or final four-hour completion.

The navigator found combat after15 transitions/40.56s and the learner resumed;
no diagnostic comparator controls this run. No death cap,one-billion step and
5000restart sentinels are nonbinding within the fixed time window. The supervisor was active at startup readback;it subsequently stopped early as recorded below. Exact supervisor status is reports/local/overnight-four-hours-2/status.json;the first failed pre-game attempt is retained separately in overnight-four-hours/. A detached finite supervisor holds system execution state only during the run,owns normal shutdown/exact approval cleanup and writes final result/metrics;it does not renew the lease or schedule more sessions. Launch-before02:15,stop-by06:17;exact earlier deadline recorded in its plan.

## Self-review and OpenSpec verification

Using openspec-verify-change. Primary self-review,not independent code review;Luna executes commands only. Diagnostic comparator is isolated from training and reads no oracle/management grid. BFS bounded41x41;unseen obstacles remain unknown. Native damage confirms a positive control without changing the learned state. Budget-only lineage and default-off observer hashes verified. Full gate passed on the reviewed implementation;no dependency changes. Synthetic RL smoke not repeated because actual native resumed PPO update is the relevant next acceptance gate.

Preparation tasks1.1..1.3 complete. Startup task2.1 is complete with independent native/update verification. Task2.2 remains incomplete until four-hour final results,shutdown/cleanup and comparable play assessment. Do not archive or claim four-hour completion while active. Missing final evidence is not counted as passed. Continue reading current status/artifacts rather than starting another worker or game instance during this assignment.


### Verification scorecard at startup

| Dimension | Status |
|---|---|
| Completeness | 4/5 tasks;final task2.2 pending running experiment |
| Correctness | Diagnostic scenario and exact lineage/resume verified;four-hour stop/final cleanup and comparable learning outcome not yet verified |
| Coherence | Existing learning/reward/observation behavior preserved;diagnostic comparator isolated;finite local supervision/frozen inputs followed |

The incomplete final evidence is a current acceptance blocker,not a failed test
or a claim of four-hour success. Do not archive. No other worker/game control or
source/config change while the finite supervisor is active. Final metrics and
result files are produced locally on exit;next action is to inspect those and
perform a comparable frozen gameplay evaluation before declaring improvement.


## Final early-stop and user cancellation

The supervisor ended after161.23seconds (not four hours),learner exit0,
state=early_stop,error=null,cleanup_errors=[]. Budget record:
Navigation budget exhausted;unfinished rollout has no new checkpoint.
Cumulative navigation reached20 transitions. Gate had725 combat decisions,
512 checkpointed steps,213 unsaved,outcomes unknown1/empty1,zero infrastructure
faults/deaths/restarts. Oracle5 enemy-damage events total17.5HP and2 player-damage
events. This was a management-budget stop and does not establish learned improvement.

Latest7d53f55f-s20-t7424,parentt7168,retained alongside the initial migratedt6912.
Original08e0d262-s20-t6912 unchanged. The existing four-hour configuration and
weights are preserved,not restarted. Final local result/metrics:
reports/local/overnight-four-hours-2/{result.json,metrics.json}.

After this early stop,the user cancelled further four-hour execution and asked
for a plan. Primary confirmed Isaac/learner/supervisor absent,port9528 bindable,
approval JSON/tmp absent,and installed default-off observer hashcc81b2daa5c52437dcae042c3f6e702d18e053c546d9933b06985e9b1c271390.
Receipt:reports/local/overnight-user-stop-verified.json. Temporary system-awake
state was released in supervisor cleanup;its process is gone. No replacement
New Run was executed. No scheduled/heartbeat task or automatic retry was created for this attempt.

An unfinished time-only navigation/explicit replacement sketch was preserved
locally as reports/local/deferred-time-only-navigation-and-reset.patch and removed
from production source. It received no full gate/native acceptance and is not a
completed fix. No new game tests were run for this documentation-only stop/plan
update. OpenSpec strict validation and diff checks were rerun. Full-duration and
comparable-play evidence remain not_run;task2.2 stays incomplete. Next work follows
the readiness plan,starting with runner and navigation progress contracts.
