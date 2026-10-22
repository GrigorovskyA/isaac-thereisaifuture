# Evidence: shot-flight positive control

Date:2026-10-22 Europe/Amsterdam. Revision1da941e8abab5f798ea4230ae106d7b02cc46583.
User authorized this exact [finite plan](2026-10-22-shot-flight-control-plan.md)
with "Launch" in the current conversation. One Luna/high script runner executed
the frozen helper once;primary independently read back artifacts and restored
the diagnostic deployment. No training,inference,New Run or model writes.

## Outcome

| Measurement | Observed result |
|---|---|
| Entry | Fresh guarded file2/Continue,Isaac,room83,door(560,280) |
| Native context | Session0d6f2f1470c14bb8885aaffa42d3ef08,epoch1,frames77097->77484 |
| Completed commands |254:150 route,2 waypoint settle,12 final settle,90 left-shoot |
| Stop |90 guarded shooting-command cap;no retry/reset |
| Final position |(317.2173,196.8247) |
| Target HP |10->10 at observed endpoints;no positive damage qualification |
| Player health |5->5 red half-hearts;no observed loss during covered endpoints |
| Death/clear |Neither observed;coverage remains partial |
| Sampled tear diagnostics |157 target records,zero tear samples/labels,no stop/error record |
| Native tear callback notes |Zero during this control |
| Native accepts |254 joined commands,133 lag0frame and121 lag1frame |
| Model |a0a93c29-s20-t26368 unchanged,seed20,schema2/723,rewardlive-firing-v5 |

The initial covered endpoint already had5 half-hearts. This receipt does not
establish health before that endpoint. Every shot had same-frame visible clear,
in-range left-target evidence within8 transverse units;all policy vectors
reconstructed exactly. Accepted actions and geometric proxies do not prove
engine firing,tear birth,collision or a hit.

## Control limitation: one-frame holds differ from training

The helper requested one-update actions. All90 shooting holds expired after
exactly one game frame:15-33ms,median17ms. The accepted shooting phase spanned
138 frames. No native tear note or sampled trajectory was observed. Sampling
at100ms and callback guards are incomplete;absence is not exhaustive proof of
no tears. The result cannot qualify projectile flight or target damage.

This is a material limitation of the chosen control. The training configuration
uses `action_repeat_game_updates:3`,not1. Saved native v5/v4 training logs contain
653/656 native `Action tear` notes respectively,among2503/2501 accepted commands
(including their final censored accepts). Those notes establish actual native
tear callbacks in those past runs,not hits or damage. Thus a general broken-fire
claim and a claim that the model never shoots are unsupported. A causal effect
of the one-frame duration is plausible but not established by this unpaired
comparison. The original corner/blocked-aim behavior remains unresolved.

Next required evidence is a separately declared clear-target control using the
same three-frame hold as training,with flight sampling and actual target HP
readback. Do not increase hold durations,bypass expiry,relax health stops,repeat
this closed experiment or train automatically. This receipt grants no new budget.

## Identity,bounds and cleanup

HelperSHA256676202452e65c8bbd9214018df1deb5399cf5999c142d3fe5cc365845f880419.
Assignmenttaskshot-flight-native-20261022-01. Parent config hash
a0a93c29b588fb2ee4b23e3c19f16c5e4124b97fb312503978a6ada405f13f15.
537 frozen inputs matched before restoration,including every preserved checkpoint
artifact found under runs/checkpoints. No checkpoint or normalizer changed.
Zero saved/unsaved training steps were created;no learner was instantiated.

The180-second inclusive clock began at Unix1792630357.9148324;cleanup completed
at1792630402.1767519,about44.262seconds later.254/320completed commands and90/90
shoot commands;zero declared infrastructure faults,retries or death restarts.
The legacy approval API accepts a minimum max_restarts1;no reset was requested.
Disk/trace limits were not exceeded. Script/harness exit0 means the prescribed
stop and cleanup completed;it does not mean the positive control passed.

To satisfy the existing matching-source deployment preflight,the same reviewed
single literal `tear_diagnostics=false->true` was temporarily applied to source
and installed first-party observer,with exact private backups. Both matched
diagnosticSHA256cf755878c3e2198b73d18dc5e8f155f8360fae5dbf604150efd9eb4f8c2db081.
After worker completion,input release and normal owned-game shutdown/observer
close were confirmed from native logs;game/listener/owned approval were absent.
Primary restored both exact baseline files to
b9a55abc5c63e68e02ad71bb44b64313dad294bdd2f310d103baff4521b18425.
The other535 frozen inputs remained unchanged;zero restoration/cleanup errors.
No save/Cloud files were manually edited;normal game exit performed its own saves.

Local evidence:reports/local/shot-flight-control-20261022/{diagnostic.py,
verification.json,hold-analysis.json,restoration.json,verification-console.txt,
run-console.txt,native/{assignment.json,deployment.json,native-game-log.txt,session/}}.
Raw traces,models,approvals and backups remain ignored.

## Verification and acceptance

OpenSpec apply/verify self-review,not independent code review:

| Dimension | Status |
|---|---|
| Completeness |3/4;native positive-damage task3 remains unchecked |
| Correctness |254 action/accept joins and vectors verified;90 clear proxies;no actual damage qualification |
| Coherence |Scripted diagnostic isolated from learning;original guards and restoration preserved;one-frame control limitation explicit |

The existing36 focused tests passed during preparation with the isolated Lua
harness,zero skips. Shipped source/config/dependencies are unchanged after exact
restoration;no new full gate or RL smoke is claimed. Final verification uses
strict specs,diff/link checks and artifact/hash readback. No archive,model
promotion or learned-gameplay improvement acceptance.
