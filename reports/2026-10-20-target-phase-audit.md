# Target phase and exported-membership audit

Date2026-10-20,Europe/Amsterdam; primary Windows implementation and acceptance,
gpt-6-luna/high executes supplied checks. Dirty checkout/unrelated work preserved.
Change:live-target-phase-audit. No learning,policy/gate/reward/schema changes.

## Contract and sources

Current capture requires visible,existing,nondead active enemies for policy
membership; oracle drops the visible requirement but also filters dead/inactive
entities. The API distinguishes [IsActiveEnemy and IsVulnerableEnemy](https://wofsauge.github.io/IsaacDocs/rep/Entity.html)
and exposes [NPC State](https://wofsauge.github.io/IsaacDocs/rep/EntityNPC.html).
These primary API documents justify diagnostic reads,not claims about this installed
enemy. No enemy name/classification or target strategy is assumed.

Default-off literal target_phase_diagnostics flag enables local-only state/change
records. Read NPC/enemy/vulnerability,existence/death/visibility,active(false/true),
type/variant/subtype,state,HP/maxHP and position; correlate exact actual post-cap
policy and oracle membership using separate capture maps. No extra room scan.
No raw pointer/seed log. Limits:120s,10Hz,64 scanned entities,128 lifetime labels,
512 lines,800 chars/line. Position changes do not cause line spam. API/log errors
disable only the audit; reconnect/software resets cannot renew it.

First offline test exposed different policy/oracle IDs in the first capture of
one newly seen lifetime. Existing identity() reads the previous map twice and can
allocate twice before retained replaces it. The audit now correlates each actual
export ID separately; production identity assignment is unchanged in this scope.
Do not conflate that separate issue with the pile-phase diagnosis.

## Offline results

First targeted run:exit1,12 passed/one failed,0 skipped. A diagnostic membership
assertion exposed the first-capture ID distinction above; corrected diagnostic
correlation,not the underlying export behavior. No full gate ran after that failure.
Final targeted:exit0,13 passed in0.58s,zero skipped. Full Check.ps1:exit0,1950
passed in44.57s,zero skipped,plus Ruff,format114 files,mypy47 files,pip consistency
and OpenSpec33/33. Worker before/after hashes match and primary verifies current
files; logs reports/local/phase-audit-final-*. Smoke not rerun: no model/dependency
or training change; the prior16-step smoke remains historical evidence.

## Native budget recorded before launch

One finite random check via reports/local/Run-TargetPhaseAudit.ps1. Primary checks
closed game and owns deployment. Back up installed main.lua exactly; activate the
tested source with only target_phase_diagnostics=true; record source/configured/
original hashes in reports/local/phase-audit-deployment.json. Metadata unchanged.
Luna does not deploy. Restore tested default-off source only after verified closure.

Steam launch,file2/Continue,at most12 guarded menu keys; no New Run or keyboard
gameplay,no save/Cloud/options edits. Existing approval/listener/instance stop
preflight. Random seed20,1200 decisions or3 controller minutes; startup/connection
120s,absolute total360s,disk512MiB,maxfaults0,maxdeaths1,maxrestarts1,gate90s,
navigation256 commands/90 pulse seconds/four transitions. Approval342s,within
the absolute deadline. No retry/budget renewal. No learning or checkpoint writes;
t8960 hashes/latest must remain unchanged. Close normally immediately at return;
persist wrapper/runtime codes and verify process/listener/exact approval cleanup.

Native attempt ended early; the reported revival/pile transition remains pending.
An unobserved or truncated diagnostic window cannot prove phase inclusion/exclusion.
Audit output is oracle-only and never model input.

## Partial native result and cleanup

reports/local/phase-audit-native contains plan,console,game-log,cleanup and numeric
wrapper-exit records. The user helped enter gameplay before the helper established
its required visual file-2 menu proof. The worker then closed normally as its plan
required. The native log independently records seed F4C7 BB19, [Continue, 2]; slot2
is therefore evidenced, but autonomous entry is not. 128 random combat decisions
and one handoff ran before closure; no learning,death or restart occurred. Closing
the game caused the controller's peer-closed transport failure: runtime exit2,
wrapper exit1. This is a failed/incomplete check, not a spontaneous game death.

115 raw phase lines include six vulnerable invisible/oracle-only and twenty
vulnerable visible/policy+oracle records. No vulnerable entity excluded from both
exports was observed. No correlated revival/pile transition was captured, so no
inclusion/exclusion conclusion is accepted. Type11/variant1 appeared; no enemy
name is inferred from this alone.

Primary verified zero game processes/listeners and exact approval absence, plus
unchanged t8960 identity/hashes. After closure, restored tested source with the
diagnostic flag false: deployed SHA256 CD930CC3743DD530238C05CB735D543128426D2D88EE1490F229FFF801969D26.
Deployment record preserves original backup/configured hashes. Native scenario
acceptance remains blocked. User subsequently requested startup without screenshots
or agent desktop control; no second phase-audit attempt was made.

## Separate self-review and OpenSpec verification

Using openspec-verify-change for live-target-phase-audit,spec-driven. Reviewed
proposal,design,delta spec,tasks,source diff and behavioral tests. This is primary
self-review,not independent review. Three requirements map to literal/config/live
guards,post-cap capture maps,private bounded labels and pcall-contained logging.
Tests cover disabled/nonliteral flags,no extra API reads,wire parity,dead vulnerable
mock phase,policy capacity,position-only changes,absence,API/log failure and all
resource limits. No source change after final offline gate. Native API behavior
and actual pile-phase correlation remain pending; no proof is inferred from mocks.

Checked that optional maps do not allocate bridge IDs or mutate membership; the
diagnostic reads existing references only. The first-capture ID issue is recorded
separately rather than silently fixed. Failure stops only the journal. No policy
state,normalizer,reward,action-return or authority writes were added. No new issue
found in this self-review. Native deployment/restore and resulting audit evidence
must still be verified before marking the remaining tasks complete.
