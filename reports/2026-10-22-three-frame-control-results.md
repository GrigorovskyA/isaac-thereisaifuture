# Evidence: three-frame clear-shot control

Date2026-10-22 Europe/Amsterdam. Base1909fffda06078bd9db6b56a80a50c642ec60041.
The user authorized the proposed three-frame control with "Do it" in the current
conversation. One Luna/high worker executed the
[finite plan](2026-10-22-three-frame-control-plan.md) once;primary independently
verified logs,identities and cleanup. No learning,inference or New Run.

## Native result

| Measurement | Observed result |
|---|---|
| Entry |Fresh guarded file2/Continue,Isaac,room83,door(560,280) |
| Context |Sessiondb58749fc26540a585f4e34ca94239e3,epoch1,frames77516->77641 |
| Completed commands |40:26 route,2 waypoint neutral,12 final settling |
| Shoot commands |0;range guard withheld shooting |
| Stop |No positively measured left firing opportunity |
| Final position |(340.8798,198.8968) |
| Target distance/range |260.8823/260 worldunits;aligned,clear,but out of range |
| HP |Target10->10;player5->5 half-hearts during covered endpoints |
| Native accepts |40joined,37 lag0frame and3 lag1frame |
| Tear diagnostic |72 target records,zero tear samples;no shots were commanded |
| Death/clear |Neither observed;endpoint coverage remains partial |

This stopped before shooting and therefore does not compare one-frame and
three-frame firing efficacy. It provides no native tear/hit/damage qualification
and no learned-policy result. The actual range guard behaved correctly.

## Diagnostic-controller defect

The helper advanced its waypoint on position tolerance alone. It did not require
low residual velocity or revalidate x after final settling. At the final arrival
latch,frame77600,position was(322.0542,199.6947),velocity(2.253,-0.095). Neutral
input allowed a further18.8256units of x drift,to340.8798. The target at(80,200)
was then0.8823units beyond measured range. The first waypoint also latched while
moving:frame77542,y199.4005,vy1.869. These are controller preparation failures,
not a defect proved in the learner or native firing implementation.

An ignored offline candidate now enters a braking phase,keeps neutral until
speed<=0.1,then rechecks both coordinates before advancing. A drifted endpoint
returns to route acquisition. The shooting guard remains unchanged. Execution
of the candidate's actual route branch passed four checks:reject both recorded
moving arrivals,reacquire the stopped drifted endpoint,and accept a genuinely
settled endpoint. Syntax parsing passed. This is recorded-state regression,not
a full physics simulation,native convergence proof or accepted runtime fix.
The candidate's --run entry point is disabled;no retry/assignment was created.

Next work is to validate settled waypoint acquisition before another positive
damage control. Do not relax range or alignment to hide this failure. Do not
repeat a closed budget or begin training automatically.

## Identity,bounds and cleanup

Taskthree-frame-native-20261022-01;helperSHA256
597703b60764b02f307b072b4962320a14c741d1b9f9b6fabf1950f29861bbad.
Parenta0a93c29-s20-t26368,seed20,schema2/723,rewardlive-firing-v5;
configa0a93c29b588fb2ee4b23e3c19f16c5e4124b97fb312503978a6ada405f13f15.
All537 frozen inputs matched before restoration,including preserved checkpoints.
No model/normalizer/optimizer/pointer changes or training samples were created.

Clock startedUnix1792641660.0069313;cleanup finished1792641697.3599331,about
37.353seconds of the180second inclusive limit.40/320 commands,0/90 shooting
commands,zero retries,declared faults or death restarts. Disk/trace bounds were
not exceeded. Exit0 means guarded stop/cleanup completed,not damage acceptance.

Native shutdown and observer close confirmed. Game/listener/owned approval absent,
cleanup_errors empty. Primary restored both temporary diagnostic source and
installed observer to baselineSHA256
b9a55abc5c63e68e02ad71bb44b64313dad294bdd2f310d103baff4521b18425.
The other535 frozen files remained unchanged;zero restoration errors.
No manual save/Steam Cloud edit or launch-option change occurred.

Local evidence:reports/local/three-frame-control-20261022/{diagnostic.py,
verification.json,restoration.json,arrival-analysis.json,candidate-branch-regression.json,
diagnostic-settled-candidate.py,native/{assignment.json,deployment.json,native-game-log.txt,session/}}.
Raw logs/models/approvals/backups remain ignored.

## Verification

OpenSpec apply/verify self-review:3/4 tasks;task3 remains unchecked because actual
positive damage is unverified. Existing directional diagnostics/scenarios remain
mapped and unchanged;this scripted controller failure is recorded separately.
No archive or gameplay-improvement acceptance. Shipped source/config/dependencies
are unchanged after exact diagnostic restoration;retain the previous2342-test
full gate and36-test diagnostic preparation receipt without claiming a new run.
Final checks use strict specs,diff/local links and frozen artifact readback.
