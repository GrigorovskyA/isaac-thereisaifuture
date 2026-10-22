# Design

## Decisions
Consume only validated EntityFrame and CombatGeometry; never oracle HP/navigation
or hidden target state. Use the established none,left,right,up,down indices. For
each cardinal direction retain visible IDs in aligned/in-range clear,blocked,
unknown and aligned/out-of-range groups. Report unknown weapons/lines and visible
overflow without negative certainty. An observed clear proxy can be reported
even with overflow; absence of all useful targets cannot be proved with overflow.
Validate same frame/visible identities. Alignment tolerance defaults8worldunits,
matching observation2; audit20 separately as a sensitivity check,never hit proof.
Target-center clearance/range/alignment ignore tear radius,motion and vulnerability;
the output is an opportunity proxy,not a guaranteed hit or action recommendation.

Keep diagnostics outside learner observations/info/reward. Existing45-degree aim
proxy remains historical. Aggregate saved records with fixed byte/record bounds,
identities and complete failure counts. Frozen model probabilities must not mutate
weights/statistics/recurrent training state; clone returned probabilities.

## Native control
Prepare one explicit180-second inclusive plan with step/disk/fault/restart caps,
expected source/deployment/model identities and cleanup. Continue/file2; record
actual door start. In measured room83 ordinary-tear state,move along verified
walkable waypoints(280,280),(280,200),then fire left only with positively measured
same-frame clear/aligned/in-range target evidence. Stop on first observed enemy
HP loss,death/clear/context change,unknown evidence,fault or budget. No reset/New Run.
Every scripted action is explicitly labeled;no samples enter training.
Absence of native acceptance or safe compatible state leaves the task unfinished.

The original control closed without damage qualification. A separately authorized
2026-10-22 shot-flight control superseded its route with(560,200),(320,200),320
commands/90 guarded shots under the same180second and first-health-loss stops.
It added the existing bounded local tear diagnostic and exact source/deployment
restoration. It also failed to qualify damage;both used one-frame holds whereas
training uses three. Preserve this limitation and leave task3 unfinished. Any
new control requires its own declared plan and authority;neither closed budget
permits a retry. See reports/2026-10-22-shot-flight-control-results.md.

A new user-authorized three-frame control on2026-10-22 stopped before shooting:
position-only waypoint completion ignored residual velocity,then neutral settling
drifted beyond measured range. The range guard correctly withheld all shots.
An offline-only braking/revalidation candidate rejects the recorded false arrivals;
native convergence/damage remains unverified. No range relaxation or renewed
runtime budget follows. See reports/2026-10-22-three-frame-control-results.md.

The separately authorized settled-controller check did not acquire even the
first waypoint:three-frame movement oscillated and the inherited900update gate
stopped execution at902updates. Recorded-state arrival checks are not convergence
tests. Stop this native approach pending offline closed-loop motion validation
and a plan listing every active bound;do not extend limits or infer learner
failure. See reports/2026-10-22-settled-control-results.md. Task3 remains unfinished.

Current accepted scope: the mixed control passed after512 bounded offline
convergence cases. One-frame navigation/braking acquired both waypoints at low
speed;three-frame shooting produced native tear callbacks and observed target
HP10->6.5 with unchanged player health. The900update gate was explicit and retained.
Task3 now qualifies for this scripted scenario only;earlier pending statements
above describe historical attempts. Learning/input/reward contracts and preserved
models remain unchanged. See reports/2026-10-22-mixed-control-results.md.
