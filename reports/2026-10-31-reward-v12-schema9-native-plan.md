# Reward v12 / schema9 finite training plan

Human authorization: October31,2026, current chat: verify/publish both prepared changes,
archive v11 with checkpoint hash verification, keep deployed Lua unchanged, close the
dashboard and initialize once. Train until the first saved model checkpoint >=300000;
report at50000/150000/300000 against v11 on identical observed-step bounds. This plan
does not revive any prior run/deadline. Implementation source is committed before launch.

## Identity and limits

- Config configs/training-pure-v4.yaml; reward configs/reward-v12.yaml; seed1;
  contract1a6d8146f5e89b7bdad14fe21d3afa9cc1f5c4192b8e5f24cefb6bbab0e0c8d8.
- Observation9=11691/action2, reward_version12. The checkpoint reward_contract label
  remains pure-v11 by current design; exact config hash and reward_version distinguish it.
- Door coefficient4, death-11, stall_restart-4, stagnation-0.39 after12 seconds;
  stall.seconds30 must match watchdog30. Full stagnation floor=-7.02.
- n_steps1024,batch128,epochs10,targetKL0.03,features512,gamma0.998,ent0.005 unchanged.
- One Start-Pure.cmd --initialize; automatic same-lineage eight-hour lease rollovers
  only. Stop at first saved checkpoint>=300000 or after30 hours from actual launch,
  whichever first. Owner records one absolute UTC deadline before launching; never
  extend it. The30-hour ceiling is a conservative bound for the requested300k attempt.
- Existing20,480,000,000-byte disk cap. Any session fault or required audit failure
  writes stop.forever; no manual retry, reinitialization or fallback repair. Automatic
  startup race before stop propagation must be recorded, not omitted.
- Death/stall New Runs unlimited within the authorized supervisor sessions. At session
  entry use Continue if existing; New Run only with fresh positive file2 absence.
  Missing/contradictory evidence stops. Do not force a death to test rollover.
- Pause failures and descriptive KL/timing alone do not stop; no threshold tuning.

## Preparation

Run Check.ps1 with isolated test-only Lua5.3/installed JSON and process-local TEMP,
then OpenSpec strict. Review/stage only relevant changes; exclude tools, runs, local
logs/models/approvals. Publish requested menu-start and reward12 commits separately
where practical. No incomplete native OpenSpec changes are archived.
Hash every file of stopped runs/pure-v4 before/after Move-Item to
runs/pure-v4-reward-v11-schema9; verify finalt253952 model,normalizer,counts,manifest.
Preserve older archives. Confirm no active Isaac/worker before moving. main.lua must
match b647b712a4dc92d7fee21ce9031d0e2ef24c058f61292d56ba2e41b9969d8c50;
metadata00f46cc452c2a4e7809c14501d94de2db1ac94b1dde12b3c25d163922f34b997.
No redeployment, save,Cloud or launch-option edits. Close only the identified
project dashboard processes. Native guarded menu owns focus; monitoring never opens
or activates a window.

## Audit at18 minutes

Evidence E=reports/local/reward-v12-schema9-20261031: launch/status/result/owner
stderr, preflight,archive receipts; supervisor session plan/menu/events/result.
A bounded passive hook preserves original decoder result,model input,reward state
and env.step returns, logging first22minutes/worker with64MiB/stream cap.
Check exact config hash, snapshot decoder/frame caps, novelty_counts.npz hash against
latest manifest and repeated counts. Confirm menu_entry_resolved then matching
menu_new_run_verified or menu_continue_verified; fresh native file2 evidence required.
For encountered stall transitions record backend idle clock near30 active game
seconds, learner terminated=true/truncated=false; CSV col_stall exactly-4, and full
col_stagnation around-7.02. Episode duration/time-in-room are not the idle clock.
Report denominators and any exceptions rather than impute missing cases. Required
invalid frame/reward/contract/counts evidence stops; unencountered scenarios stay open.
Report train rows,entropy/KL/clip fraction and update time with denominators; optimizer
statistics are not native gameplay acceptance.

## First lease rollover and milestones

Capture the first transition between sessions: previous last episode/outcome/time,
session completion/fault/cleanup, new menu_entry_resolved mode, verified run entry,
same contract/resume parent, fresh episodes and checkpoint advancement. If the agent
died immediately before rollover and fresh logs verify no file2 game, require New Run.
If that precondition is absent, report it as unencountered; do not claim tested.
At each first>=50k/150k/300k checkpoint copy manifest/metrics and receipt, verify
model/norm/counts hashes promptly, then publish English report and STATUS/training
links. Report v12 cumulative fromzero and recent~50k observed completed-episode
steps; unsplit whole episodes assigned by cumulative endpoint. Show actual episodes
and observedsteps, separate from savedmodel/trainrows. Compare v11 only at identical
cumulative bounds up to254782 available observedsteps; baselineN/A beyond that.
Metrics: exit-start,stall,rooms,stage2,startroomstallproxy,collectibles sum/per episode/
1ksteps,kills/clears/damage,novelty/rewardcolumnmeans,entropy/KL/clip with row coverage.
No extrapolation, no imputation, no performance stop rules or frozen-policy claims.
Read-only checks every15minutes compare game/worker/owner presence and fresh progress;
>10minutes without advancement triggers bounded logs/possible-stall notice, never retry.
Quiet healthy progress; notify Russian audit/milestone/fault/final only.

## Terminal handoff

Retain stop.forever; freeze finalmodel/normalizer/counts/manifest/source/config/deployed
hashes and archive integrity. Inspect every session learner exit,fault,cleanup_errors,
status_writes_skipped; launcherexit0 cannot erase failure. Check actual absence of
Isaac/worker/finiteowner/Start-Pure/listener9528/deployed authorization.json/tmp.
Report unverified cooperative release even if processes are absent. Final report uses
actual end date/reason, achievedstepsvs300k and all native/baseline limits; publish
only relevant docs/reports/tasks evidenced, whitespace/links/strictchecks. Delete
report monitor once all authorized work is complete. No archive acceptance by stats.
