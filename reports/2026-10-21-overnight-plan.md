# Plan: four-hour time-dominant continuation

User request2026-10-21:finish diagnostic baseline,then run existing training for four hours without practical step/death/restart count limits. Base9e0f30a819aea0ff7998675ebb34faa82ac69357. No learning/reward/observation/action hyperparameter changes.

## Diagnostic preparation and test

Primary added an explicitly hand-written observation-only local approach comparator,not a learned policy. It reads exported nearest enemy/obstacle slots only;no management/oracle grid or absolute clipped player-position input. Approximate41x41cell BFS,narrow cardinal alignment,known-blocker exclusion;unknown obstacles remain unknown. Its trajectories never become demonstrations/model input. Primary copied the current t6912 binary into the declared budget-only continuation root;no training yet.

One fresh gpt-6-luna/high worker executes these exact commands sequentially from D:/isaac,stopping on the first failure,no retries:
1. `D:/isaac/.venv/Scripts/python.exe D:/isaac/reports/local/run_night_gate.py`
2. `D:/isaac/.venv/Scripts/python.exe D:/isaac/reports/local/run_approach_baseline.py`

First driver verifies reports/local/approach-frozen.json,sets exact Lua test environment inside Run-NightChecks.ps1,runs targeted/full checks,records start/end/exit and samples temp growth. Offline cap480s,512MiB incremental temp,32MiB small check outputs;absolute deadline embedded at preparation. Native test uses existing default-off installed observer cc81b2daa5c52437dcae042c3f6e702d18e053c546d9933b06985e9b1c271390,one Steam/guarded Continue2 launch,initial Isaac verification,512decision/180s controller,300s outer,one-death stop,no reset/restart,maxfaults0,retries0,256MiB output,240s lease(max_restarts1 schema minimum),eight menu keys/60s. No checkpoint writes. Wrapper closes its owned game normally,removes exact approval and verifies original t6912 latest/model unchanged. Primary performs final readback. A zero-damage baseline is a diagnostic result,not permission to weaken reward;user still requested the overnight experiment.

Worker allowed writes:tests/caches/temp,night-targeted/gate outputs and exits,reports/local/night-gate/,reports/local/approach-baseline/,runs/approach-baseline-20261021/,exact approval/tmp only. No source/test/config/helper edits,fixes,deployment,dependencies,Git,nested agents,focus bypass or command invention. Primary freezes tested files;one worker at a time.

## Overnight lineage

Explicit budget-only descendant runs/live-conservative-v2-overnight-20261021/seed-20/checkpoints/7d53f55f-s20-t6912. Config configs/training-live-conservative-v2-overnight.yaml,canonical hash7d53f55f92aae137da716f2916e4cc18db2c2594ef76bb58d2104bdb1e7ce4ee. Parent08e0d262-s20-t6912 retained unchanged. Binary model9b8e7eaa8aa89cc23debc82e99f26c365a24c617f63bbd6f5676b7ed350a22f4 and normalizerd5ec622cf5dd653b7ac5bc8070693ddb0c5b65768f4d90c6bb3ba95ceaba6fd0 copied exactly,including optimizer;RNG unchanged. Only manifest config/id/parent and budget keys differ. Provenance at run-root budget-extension.json and reports/local/night-lineage.json. All nonbudget config fields verified identical. Missing/incompatible lineage stops,never reinitializes.

## Overnight execution contract

Pending exact prepared command/frozen hashes and absolute startup deadline after baseline. Four-hour learner,one approval,no death cap,one-billion nonbinding step sentinel,5000 nonbinding restart sentinel (4-second minimum spacing allows at most3600 in four hours),32GiB emergency disk guard on671GiB free disk. Existing navigation/focus/infrastructure guards retained;maxfaults0,no automatic retry. No diagnostic comparator mixed into training;only unchanged stochastic RecurrentPPO controls combat. Completed256-step rollouts save weights/normalizer/manifest;last partial rollout may not save. Primary must verify an actual fresh checkpoint/update before saying training started. No changed-weight claim is a learned-play improvement claim;comparable frozen evaluation remains necessary after training.

## Exact overnight launch assignment (prepared after baseline completion)

Primary independently verified188 baseline-frozen hashes,224 policy rows,19 conservative damage events totaling66.5HP,zero faults/deaths,normal shutdown/free9528/exact approval removal and unchanged t6912. The baseline gate's final label was empty;the last pre-action oracle still had3HP androom_clear=false,so this proves damage,not an independently sampled room-clear result. Final baseline gate passed108 targeted/2048 full tests,zero skipped,OpenSpec40/40;124 formatted files,mypy52 source files.

One fresh gpt-6-luna/high worker executes exactly:
`D:/isaac/.venv/Scripts/python.exe D:/isaac/reports/local/launch_overnight.py`
from D:/isaac. No special environment needed. It starts exactly one detached finite local supervisor(run_overnight_four_hours.py),records PID/command,then observes at most240seconds for an actual new complete checkpoint above6912. It never restarts/retries. The supervisor owns its learner,Steam launch/menu input,one approval,local progress sampling and cleanup after the worker returns;this is not a recurring automation or renewed lease.

Source freeze:153 paths in reports/local/overnight-frozen.json,including source/tests/configs/mod/scripts/AGENTS/prepared helpers,original and migrated t6912 binaries/manifests. Mutable run outputs/latest pointers and progress documentation are excluded. No source/config/model-parent edits during the run. Missing/mismatched files stop before action. Initial root/id/config are exact as above. Initial entry mode is Continue after the non-death baseline;it requires fresh file2 metadata and active Isaac. No fallback to overwrite Continue or to a new model.

Absolute launch-before2026-10-21T02:15:00+02:00;absolute stop-by2026-10-21T06:17:00+02:00. The supervisor records its exact earlier deadline at start:at most14520seconds total (four-hour learner plus two-minute startup/cleanup envelope),one nonrenewed lease of14520seconds,max_restarts5000,steps sentinel1000000000,no max-deaths argument,maxfaults0,retries0,32GiB emergency output budget. Learner uses unchanged conservative_guarded_cli.py,config overnight,resume,seed20,steps1000000000,minutes240,combat-gate,auto-navigate,gate-wait1.5min,navigation scale5,confirmed save2,connection timeout90. Existing eight-key/60s menu and navigation liveness guards remain. Supervisor polls own process/time each second,output/complete checkpoint progress every15seconds. Temporary thread execution state prevents system sleep while allowing display sleep;it is released in finally,without changing Windows power settings.

Allowed writes:the new overnight run root(checkpoints/normalizers/manifests/logs),reports/local/overnight-four-hours/,reports/local/overnight-launch.json,overnight-startup-verified.json,overnight-supervisor-console.txt,andexact approval/tmp. No source/test/config/helper edits,installs,deployment,saves,Cloud,launch options,Git,nested workers,focus bypass or additional runs. Primary verifies first native update and publishes prepared code/progress;final acceptance remains pending until completion. No concurrent game control or other script worker during the overnight assignment.

Cleanup:release environment/input,close only the owned Isaac normally,no game force-kill,wait for the learner,remove approval only on matching created hash,release execution state,verify frozen source,write result/status and streaming summary metrics. Controller timeout may terminate only its owned learner. The supervisor records early_stop for a clean stop before the time window,not four-hour completion. Root artifacts:status.json(plan/deadline/latest),plan.json,console.txt,menu.jsonl,result.json,metrics.json. Parent t6912 remains immutable. No training success claim until measured comparable play is evaluated after this run.

## Corrected fresh startup after pre-game expiry rejection

The first overnight launcher exited1 before launching Isaac or the learner:the approval used its own later clock read and exceeded the supervisor's deadline by a fraction of a second. The assertion correctly stopped;exact approval cleanup passed,153 frozen files verified,and latest remained6912. Retain reports/local/overnight-four-hours/ and overnight-launch.json as failed pre-game evidence. No gameplay/training occurred. Primary corrected the helper to compute remaining lease seconds from the fixed deadline using one explicit now value,with a one-second margin. Three fractional-clock regression cases against the actual approval writer passed,including the rollover case.

New finite assignment uses exactly `D:/isaac/.venv/Scripts/python.exe D:/isaac/reports/local/launch_overnight2.py`. Supervisor/helper suffix2,output reports/local/overnight-four-hours-2/,launch/startup receipts and supervisor console suffix-2. It uses the same untouched migrated t6912 and the same four-hour budget/guards. New source freeze156 paths at reports/local/overnight-frozen-2.json,assignment overnight-assignment-2.json. Same launch-before02:15/absolute stop-by06:17;the exact earlier fixed deadline is recorded at new startup. One fresh launch only,no automatic retry or renewal of the first removed lease. No further game/test worker runs concurrently. Parent binaries and all learning settings unchanged.


## Execution closed by user (2026-10-21)

The corrected run ended early after161.23s at t7424 due cumulative20-transition
navigation budget. Completed512 new saved steps,213 unsaved,17.5HP conservative
damage;no infrastructure faults/deaths/restarts. Cleanup/source/lineage verified.
The user then cancelled further four-hour execution and requested a plan. No
replacement New Run occurred;that one-off approval is not a standing authorization.
All launch assignments here are closed. Do not reuse them or renew their leases.
See reports/2026-10-21-long-run-readiness-plan.md for future preparation. The
unfinished navigation/replacement sketch is deferred and not accepted code.
