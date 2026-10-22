# Evidence: settled-controller native check

Date2026-10-22;basec628e40e78667463b877dbe5534d82f56962e761. Current user
authorized proceeding with the proposed settled controller. One Luna/high worker
executed the [finite plan](2026-10-22-settled-control-plan.md) once;primary read
actual artifacts and independently verified restoration. No inference/training,
model changes,New Run or reset.

## Result and blocker

- File2/Continue,Isaac,room83,session4228e9fa5dd54c7fa2cf9d73aa7b6cdc,epoch1.
- Frames77663->78565;291 accepted/completed commands,0shots,0waypoints acquired.
  Executed phases:133route,158braking. One additional selected neutral command
  was stopped before dispatch;it has no native accept or reward/endpoint credit.
- Target HP10->10 and player half-hearts5->5 at observed endpoints;no death/clear
  observed. Endpoint coverage is partial;no actual damage qualification.
- Position started(560,280),ended(560,217.6383). x stayed560:the controller never
  left the first vertical segment. y reached174.2733 and repeatedly reversed.
- 324 local diagnostic target records,zero tear samples/callback notes. Since no
  shot was requested,this provides no evidence about firing duration efficacy.

The neutral-braking correction prevented false waypoint latching but did not
converge. Coarse three-frame pulses and position-only steering still produced
overshoot/reversal around y200. Four recorded-state checks were insufficient:
they tested rejection of moving arrivals,not closed-loop convergence. Do not
report this as an accepted controller fix or a learned-policy failure.

The actual stop was an inherited `combat_progress_updates=900` gate,not the
published180second/320command caps. It triggered after902game updates at the
next bounded batch check. This additional limit was present in the frozen helper
but omitted from the written plan;the plan was incomplete in this respect.
Increasing that limit would not repair the observed oscillation. No limit was
changed or renewed during this run.

Pause native waypoint attempts with this approach. Next engineering work is an
offline closed-loop convergence test against measured motion and explicit
accounting of every active cap. A candidate alternative is previously measured
one-frame movement with three-frame shooting;it requires its own validation and
finite plan. No automatic native retry or training is authorized by this report.

## Identities,verification and cleanup

Tasksettled-native-20261022-01;helperSHA256
9d4e2cbba71c873056985ac7ab8a29ea357560cf4b5865c6e7ddb304970634bc.
Parenta0a93c29-s20-t26368,seed20,schema2/723,rewardlive-firing-v5;
configa0a93c29b588fb2ee4b23e3c19f16c5e4124b97fb312503978a6ada405f13f15.
All291 completed actions and vectors joined actual native accepts:277lag0,14lag1.
537 frozen inputs matched before restoration. Both temporary observer source and
deployment were restored to baselineSHA256
b9a55abc5c63e68e02ad71bb44b64313dad294bdd2f310d103baff4521b18425;
the other535 frozen files remained unchanged,including preserved checkpoints.
No training-sample/model/normalizer/optimizer/pointer writes occurred.

The first offline verifier rejected292selected versus291accepted records. Its
traceback is retained. A corrected exact readback requires this one unmatched
selection and the recorded902update gate stop;it verifies the291 completed
records without inventing a final command. The dependent initial trajectory
aggregation consequently lacked its input;its error is also retained. Neither
offline readback attempt repeated or extended native execution.

Harness exited0;normal native shutdown/observer close confirmed,game/listener/
owned approval absent,cleanup/restoration errors empty. Disk/trace limits were
not exceeded;zero retries,faults or death restarts. Script success is cleanup
success,not native positive-control acceptance. No manual save/Cloud changes.

Local evidence:reports/local/settled-control-20261022/{verification.json,
verification-console.txt,verification-reconciled.txt,restoration.json,analysis.json,
native/{assignment.json,deployment.json,native-game-log.txt,session/}}.

OpenSpec apply/verify self-review:3/4tasks,task3 still unchecked. Existing
directional diagnostics remain unchanged;native damage qualification and waypoint
convergence remain unverified. No archive or improved-play claim. Final checks
are strict specs,diff/links and frozen-file readback;no new full gate is claimed
for this documentation/ignored-helper milestone.
