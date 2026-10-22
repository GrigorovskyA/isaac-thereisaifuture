# Task: diagnose and address post-target wall stagnation offline

Task ID: wall-stagnation-offline-20261022-01.
Role: primary implementation agent, launched by the user on Linux/macOS. You are
not a restricted script runner. Work sequentially and finish a reviewable offline
milestone. Conversation may be Russian; repository artifacts must be English.

## Objective

Explain why the policy remains at the left wall after the first target disappears,
then implement the smallest evidence-backed correction if the diagnosis supports
one. This task authorizes diagnosis and evidence-backed offline implementation.
Reward/weight changes alone are not a success criterion. Do not start another
training run just to see whether more time helps.

Start from origin/main containing809e141 or later. Read AGENTS.md, this task,
docs/STATUS.md, and reports/2026-10-22-ready-curriculum-pilot-results.md. Inspect Git
status and relevant diffs first. The captured runtime source is e5264e52fccd308fcf96e874bcb01eb46da816a9.
Do not revive closed approvals, experiments or pending-work text in historical reports.

## Environment and inputs

Prefer a separate local checkout. If accessing the shared Windows checkout, do not
replace its .venv, node_modules, frozen runtime inputs, models or unrelated files.
Use Python3.12 in a dedicated environment outside the shared checkout. Existing
project dependencies and locks remain authoritative; do not update dependencies
just to accommodate this task. Preserve untracked errors.txt and tools/.

The raw traces and checkpoints are ignored by Git. The user must also transfer
`wall-stagnation-evidence-20261022.zip` from
reports/local/wall-stagnation-handoff-20261022/. Extract it outside tracked source
(e.g.reports/local/wall-stagnation-input/). Verify every file against MANIFEST.json
before analysis. Paths in this task are repository-relative; never assume D:/isaac
exists on this computer. BUNDLE_README.md describes the bundle and provenance.

Required bundle data:
- traces/learning-policy.jsonl and learning-oracle.jsonl:1606 paired transitions;
- run/live-events.jsonl,phases.json,oracle-events.jsonl;
- verification/primary-verification.json,native-outcome-analysis.json,
  learning-native-joins.json,loaded-timestep-readback.json;
- config/training-live-boundary-v5-pilot.yaml and the published result report.

The bundle deliberately has no models,normalizers,saves,approvals,credentials or
raw native game log. Models are optional for diagnosis,not a prerequisite for
observation/reward/geometry replay. If the user separately supplies trusted project
checkpoints,read them immutably;otherwise mark frozen-policy counterfactuals not_run.
Do not train a replacement model or fabricate logits from selected actions.
If the evidence bundle is missing,finish bounded source review and record exactly
which measurements are blocked;never claim a trace-based cause without the trace.

## Confirmed baseline to reproduce

- Parent:a0a93c29-s20-t26368 under runs/live-boundary-v5-pilot-20261021.
- Child:a0a93c29-s20-t27904 under runs/live-exposed-start-ready-pilot-20261022.
  Seed20,observation2/723,rewardlive-firing-v5,collectorlive-segment-refresh-v1.
- Config SHA256:a0a93c29b588fb2ee4b23e3c19f16c5e4124b97fb312503978a6ada405f13f15.
- Unscored setup:3s readiness wait,171one-frame commands,health5 unchanged;
  fresh learner start near(317.217,200.598),clear shot to target1 at(80,200).
- Learning:1606 completed decisions;HP-loss lower bound7,player loss2half-hearts,
  clears0,deaths0,partial coverage. Saved1536steps/sixrollouts;70completed steps
  unsaved plus one accepted final action without a collected endpoint.
- HP drops on target1 at records26/30:10->6.5->3. Last membership at record33 with3HP;
  disappearance is not proof of a kill or permission to credit the missing3HP.
- Remaining target2 stays near(560,360),HP10. Tear range260.
- 1572/1606 endpoints(97.883%) within20units of(70,209.35);7ten-active-second
  stagnation windows;clear-shot exposure6/1613 sampled learner states.
- Frozen parent and child each64decisions:observed damage/taken/clears/deaths all0.
  These later sequential phases are observational/unpaired,not causal improvement.
- Six saved optimization cycles:SB3epoch counter412->436,Adamstep1648->1744;
  normalizer count26392.0001->27934.0001. All parents/pointers preserved.
- Previous final Windows gate:2416passed/0skips,56strict items. Its status is history;
  your changed source still needs fresh checks. No native acceptance transfers to a fix.

## Work in order

1. **Reproduce the baseline.** Add a bounded cross-platform replay/aggregation
   command with explicit input/output arguments and stable record IDs. Verify the
   paired traces,report the above metrics,and separate setup/learning/frozen phases.
   Keep full outputs under reports/local/;commit only a concise reproducible report
   and a genuinely minimal sanitized fixture. Do not commit full traces/models.

2. **Diagnose the transition.** Inspect records1-40,then representative later states
   and the six recorded optimizer refreshes. Follow the chain:
   raw visible/oracle memberships -> encoded observation -> selected action ->
   measured movement/line/range -> target/potential/reward state. Determine:
   - Does target2 remain correctly encoded after target1 disappears? Are IDs,target
     selection,caches,episode resets or recurrent refreshes retaining stale state?
   - Which movement/shooting directions are selected and actually move the player?
     Distinguish pressing the wall,obstacle collision,range and blocked fire.
   - What are the measured v4/v5 potential,support masks,target keys,novelty/debt
     state and signed reward components before/after the transition and wall states?
     Is there usable feedback toward a reachable firing position for target2?
   - Is the failure explained by missing/flat feedback,incorrect state transitions,
     inherited action bias,or a combination? Give evidence and competing hypotheses.
   Read relevant source/tests on demand:firing_progress_v5.py,firing_progress_v4.py,
   firing_position.py,firing_reward.py,policy_geometry.py,encoding.py,combat_gate.py,
   live.py,rewards.py,and mod/observer/main.lua only where acquisition is relevant.
   Reports may use oracle labels;policy inputs/normalizer/recurrent state may not.
   Missing native rays/support must remain unknown. Do not fabricate visibility,
   traversability,complete geometry or collision proof for hypothetical positions.

3. **Make a measured engineering decision.** Use OpenSpec explore/apply/propose
   skills as appropriate. A behavior/protocol/reward/evaluation change needs a small
   NEW OpenSpec change with explicit acceptance;do not rewrite the completed
   exposed-start experiment as though its old native evidence tested new code.
   If a source defect or demonstrable feedback gap supports a bounded correction,
   implement it,with meaningful regressions from the measured transition. Avoid
   arbitrary coefficient tuning,extra hand-coded gameplay,removing guards or just
   moving the scripted start to another convenient point. If evidence does not
   justify a fix,deliver a reproducible diagnosis and a concrete minimal proposal
   instead of an invented patch. Do not stop at a list of vague possibilities.

4. **Preserve contracts and test exploits.** If reward/observation/action semantics
   change,version the contract and provide an explicit lineage/migration plan;
   no silent in-place change of live-firing-v5 or723input semantics. Preserve t27904,
   t26368 and all ancestors. No real checkpoint migration/init/training is authorized.
   Cover repeated entry,healing/damage,item/target cycling,disappearance/reappearance,
   wall oscillation and reset/debt farming where relevant. Test the transition to
   a remaining distant/occluded target and refusal of unsupported geometry. A changed
   weight or larger computed reward does not establish better play.

5. **Validate and hand off.** Run focused checks,then cross-platform equivalents
   of Check.ps1 on final code:ruff lint+format,mypy,pytest -m "not game",pip check,
   strict OpenSpec validation. Use the existing local OpenSpec JS CLI directly
   through Node on POSIX rather than assuming PowerShell scripts run there.
   Record exact commands,versions,exit codes,pass/fail/skip counts and tested hashes.
   Do not edit/skip/weaken tests merely to make platform failures green. Windows
   adapters or missing optional Lua runtime/JSON codec may be unavailable:record
   exact failures/skips and run all independent checks;do not install/copy proprietary
   game files or claim the full Windows gate passed. Windows Check.ps1 and native
   gameplay remain not_run for the changed source. Use openspec-verify-change;
   native-dependent acceptance tasks remain unchecked and changes unarchived.

## Runtime and publication boundaries

No game launch/control,approval writes,Steam/menu actions,NewRun,save/Cloud edits,
unlocks,mod deployment,real model writes,checkpoint fallback or new learning
experiments. Tiny synthetic training fixtures used by existing offline tests are
allowed;they are not gameplay evidence.
No file bus,heartbeat or scheduled supervisor. No messaging other chats. Do not
spawn script workers to perform source implementation;you own the work.
No global PATH/profile/security changes. Existing credentials must not be read.

Commit a meaningful verified milestone to the existing origin under the project's
standing authority;review staged paths and exclude evidence bundles/raw logs/models,
credentials and unrelated changes. No force-push or new remotes. If publication
is unavailable,retain the exact commit/patch and report that blocker. Do not archive
unfinished native scope or claim model promotion.

## Required deliverable

- A concise English report in reports/ with trace IDs,baseline reproduction,
  evidence-ranked diagnosis,implemented change or concrete justified proposal,
  tests/results/limits and the next Windows-only verification step.
- Minimal reusable replay tooling and small fixture/regressions where warranted.
- OpenSpec artifacts for changed behavior;STATUS updated in place,about100lines;
  ROADMAP only if the next acceptance milestone changes.
- Handoff:commit IDs and file list,exact tested commands/counts/hashes,source and
  contract versions,what remains not_run,plus a finite proposed Windows plan.
  That plan must identify the checkpoint/lineage,Continue/file2 entry,steps,time,
  disk,fault/death/restart caps and cleanup;it is a proposal,not execution authority.
  Assess native models by damage dealt/taken,clears/deaths and stagnation across
  explicit comparable conditions. Keep the5min->15-30min->1h->4h qualification stages.
