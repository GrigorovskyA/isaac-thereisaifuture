# Evidence: automatic target-phase audit and diagnostic refinement

- Date:2026-10-20,Europe/Amsterdam.
- Base revision:1cb3fa7;native script used this unchanged tested source.
- Active change:live-target-phase-audit;actual revival-phase acceptance remains pending.
- Runtime:Repentance+1.9.7.17.J460,observer0.5.0-dev,Lua5.3,no extender.
- Parent:1f4a187e-s20-t8960,seed20;no model/normalizer/checkpoint updates.

## Native assignment and results

One script worker,Luna6/high,executed the primary-prepared script. No screenshots,
agent desktop tools or manual menu handoff. Source frozen53 files;all matched the
recorded runtime manifest. Primary alone enabled the tested diagnostic flag while
closed,then restored its exact default source after verified shutdown.

Budget:1200 random decisions or180 controller seconds,360s absolute runner budget,
512MiB new output,one death,max one restart,zero infrastructure-fault retries.
Navigation capped256 commands/90 seconds/four transitions. Menu limited60 seconds
and eight keys. Exact approval342 seconds,max_restarts1,with explicit agent-check
evidence;no permission renewal. Parent model/normalizer/manifest/latest frozen.

| Check | Exit | Result | Evidence |
|---|---|---|---|
| Automatic menu setup | 0 | seven keys,fresh Continue2 confirmed | reports/local/phase-audit-automatic/menu.jsonl |
| Random structured-bridge run | 0 | 863 combat decisions,two handoffs,one software unknown outcome,one natural death;stopped at death limit | console.txt and run live.jsonl |
| Prepared wrapper | 0 |119.55s,no errors or retry | result.json |
| Diagnostic sample | n/a |280 lines;153 states,126 disappearances,one stop | phase-lines.txt,analysis.json |
| Cleanup | n/a |game closed,listener absent,exact approval removed,parent unchanged | result.json,primary process/port/hash readback |

Run directory:runs/phase-audit-automatic-20261020/sessions/20261020-154456-9b68a5.
Session063c5eeec8204f2f944a126afeed9d62,epoch1,visit0. First episode568 decisions
ended as unknown at the software boundary;second295 ended in death. No learning,
successful clear,automatic death restart or policy improvement is claimed. Native
seed remained F4C7 BB19. The existing run ended naturally;future startup may need
an explicit New Run path,which the accepted Continue-only launcher does not provide.

Primary independently checked the exact model,normalizer,manifest/latest hashes
against the plan. Configured observer SHA256
11e55b8554ef6a9e3d7fafd00b4cdf1ac5579fe6fb8c0ff3d750579c7add3d1c
was restored while closed to prior default SHA256
cd930cc3743dd530238c05cb735d543128426d2d88ee1490f229fff801969d26.
The subsequent revised default source deployment is recorded separately below.

## Observed facts and diagnostic limit

The audit sampled frames16743..17794 over38.033 seconds,then exhausted128 labels:
six NPC lifetimes and122 effect lifetimes. State records contained Type11/Variant1
and Type1000 effects. Installed enums identify11 as Gusher and24 as Globin.
Twenty-two visible vulnerable records were included in policy observation;none
were excluded. No sampled vulnerable candidate was excluded from both exports.
No HP increase on a tracked lifetime or correlated revival transition was seen.

These are incomplete observations:the journal stopped before the run ended and
the reported pile phase was not demonstrated. They cannot prove that the relevant
phase is exported correctly or excluded. Passive-effect churn was a verified
diagnostic-capacity problem,not a demonstrated policy-perception bug.

The user clarified that the observed enemy was a red elite and noted Globin's
mechanic. Installed ChampionColor enum distinguishes RED=0 and DARK_RED=12,with
the latter's comment identifying regeneration. Neither the user's color report,
Type11 nor20HP alone proves the actual modifier. The current native trace did not
record it. It is a separate hypothesis from a Globin species transition.

## Diagnostic refinement

Default diagnostic candidates now remain all NPCs and entities marked enemy or
vulnerable,including effects with those properties. Other visual effects require
literal target_phase_passive_effects=true,default false. This changes only the
local journal's selection;normal policy/oracle membership,wire,gate and reward are
unchanged. Original scan/time/line/label limits remain enforced without eviction
or renewal. Default mode does not claim coverage of passive visual effects.

Added optional local champion_color from NPC:GetChampionColorIdx,when available.
Missing method leaves the field unavailable and other phase records continue.
The API and its non-champion -1 result are documented in the primary
[IsaacDocs source](https://github.com/wofsauge/IsaacDocs/blob/main/docs/EntityNPC.md).
This is diagnostic metadata only;no modifier or hard-coded combat strategy enters
the policy. Installed-build champion API behavior still needs a new native sample.

## Offline checks and primary verification

First refinement:18 targeted tests passed,but full gate exited1 on an E501 test
helper line. Fixed formatting without changing behavioral assertions. Next gate
passed1982 tests,exit0. User champion clarification then added two behavioral cases.
Final targeted:20 passed,exit0,zero skipped. Final full gate receipt and current
source hashes:reports/local/phase-champion-{check.txt,exit.json,before.json,after.json}.
Final full gate:exit0,1984 pytest tests in45.17s,zero skipped;Ruff,format117 files,
mypy49 files,pip consistency and OpenSpec35/35 passed. Primary verified receipts,
before/after/current hashes. Final main.lua SHA256:
4190fca03ddee98380eef6e75d16fc5bffb7e480eeacce434202e29c434a2e25.
After two closed-game checks,primary installed this exact tested default source
with both diagnostic flags false. Previous default remains backed up;deployment
record reports/local/phase-refinement-deployment.json. CMD --preflight-only passed,
exit0,no launch. Revised diagnostic behavior has not yet run in a live phase audit.

Using openspec-verify-change for live-target-phase-audit. This is primary
self-review,not independent review. Existing default-off isolation,post-cap
membership and finite bounds remain covered. New scenarios prove143 passive-effect
lifetimes do not consume NPC history,still record a vulnerable effect,require
literal opt-in for other effects,keep all wire payloads unchanged,record champion
changes locally,and tolerate an unavailable optional champion method. Real native
phase/champion correlation and a native test of the refined selection remain
pending;no mock success is counted as that evidence. Completeness6/7 tasks,four
requirements mapped. One critical archive blocker remains:task2.3's real correlated
phase evidence is unobserved. No other implementation/spec issue or suggestion
found in the separate self-review. Native-refinement scenario coverage remains
not verified;the change is not ready for archive.

No training/dependency change;synthetic RL smoke was not repeated. The final full
gate and strict OpenSpec validation are required before the revised default source
is deployed/published. No change is archived while actual phase evidence is missing.

## Next action

Add a bounded explicit New Run entry after a natural death,then collect a correlated
Globin or regenerative-champion phase using the refined journal. Keep the phase
task pending until that evidence exists. A separate explicit compatible reward
lineage is still required before resuming learning from legacy t8960.
# Revised journal native follow-up (2026-10-20, 19:34 Europe/Amsterdam)

Base00ca10deebb11a9d3ce7c10d86c8de0ea746902a. One fresh bounded random audit,
no learning,via Steam/local guarded file2 Continue and structured gameplay.
Default observer4190fca03ddee98380eef6e75d16fc5bffb7e480eeacce434202e29c434a2e25
was configured with diagnostics=true/passive_effects=false while closed; configured
SHA4d3d86a6d52b03dc5721ca49837911c6ff1a284d488002b02a97bb299dbed543.
All53 frozen source files matched before/after. Approval342s/max_restarts1,
outer360s,controller180s,1200 decisions,512MiB,one death,zero faults/retries.
Runtime and wrapper exit0;48.69s elapsed,109 combat decisions,one natural death,
one gate handoff,two navigation visit transitions. Actual stop:death limit.

Session8719f4b89da448e984be4bd17c0c84cd,epoch1;diagnostic frames14..659.
124 lines:122 states,two gone,eight entity lifetimes. State types292/217/220
had2/88/32 records;all122 contained champion_color=-1. The optional native API
is functioning for these non-champions. No diagnostic budget exhaustion;passive
effects did not consume labels. No sampled vulnerable entity was absent from
both policy/oracle exports. No actual revival/champion scenario was observed,
so task2.3 remains pending;this does not prove the user's mechanic fixed.

Primary checked raw native shutdown,actual results,source hashes,parent hashes,
approval absence and closed game,then restored byte-identical default-off source
while closed. No model/checkpoint/latest changes. Local receipts:
reports/local/phase-champion/{plan,result,analysis}.json,menu.jsonl,phase-lines.txt,
game-log.txt;session runs/phase-champion-20261020/sessions/20261020-193452-e5865d.
Deployment/restoration manifests remain ignored. Next: explicit independent
conservative reward baseline;retain this unobserved enemy scenario as a limitation.
