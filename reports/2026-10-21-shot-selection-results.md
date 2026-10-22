# Evidence: shot-selection-audit

Date2026-10-21 Europe/Amsterdam. Base01c4898 plus diagnostic-only source/tests.
Using OpenSpec apply/verify;primary self-review,not independent code review.
One Luna/high script worker executes prepared commands. See
[finite plan](2026-10-21-shot-selection-plan.md). No learning,model migration,
reward/input/action changes or New Run are part of this milestone.

## Offline findings
The earlier nearest-enemy45degree cone was explicitly coarse,but unsuitable for
judging whether the selected cardinal firing direction had a clear target. New
pure diagnostics separate alignment,range,blocked/clear/unknown center lines,
visible overflow,missed opportunities and wrong-direction choices. Only existing
EntityFrame/CombatGeometry data are consumed;no oracle or hidden target labels.
Results never enter policy/normalizer/reward and do not select model actions.

| Saved trajectory | Decisions | Clear proxies at8units | Clear proxies at20units |20unit missed/wrong/selected |
|---|---:|---:|---:|---|
| Earlier v4 |2500|2|3|2 missed,1 wrong,0 selected |
| Latest v5 |2502|0|6|1 missed,4 wrong,1 selected |

The tolerance is transverse world distance,not degrees.20unit sensitivity is
looser than observation2's8unit alignment bit;none of these proxies guarantee a
tear hit because radius,motion,vulnerability and full trajectory are not measured.
There were no unknown classifications in these traces. v5 shooting decisions:
1440 only-blocked near-axis choices,611 no-aligned-target,444 no-shoot,
4 wrong-direction-with-clear,1 missed clear,1 selected clear proxy,1 out-of-range.
No observed damage/clear improvement is established by these counts.

All six v5 loose opportunities were rightward at decisions33-38 near
(346.75,347.51)->(301.91,349.35);this is a brief door-to-wall passage. The remaining
trajectory offers almost no measured clear firing experience. A frozen final
checkpoint replay assigns mean3.64% shooting probability to the clear rightward
direction on these six states. Overall frozen mean probabilities in order
none/left/right/up/down are18.47%,20.25%,3.47%,54.42%,3.39%.
These are counterfactual final-model replays on actual states,not probabilities
logged while training. Six nearby states are not an independent evaluation set.
The evidence supports a strong inherited firing bias and sparse opportunities;
it does not prove one sole learning failure or justify coefficient-only tuning.

## Inputs and execution
Read exact paired native traces and checkpointa0a93c29-s20-t26368,seed20,schema2/723,
rewardlive-firing-v5,configa0a93c29b588fb2ee4b23e3c19f16c5e4124b97fb312503978a6ada405f13f15.
ModelSHA2566e94cc1ffeb3280adf5881cc56e1625cbe62f400a1c1b34b173165a2f0f55d08;
normalizerSHA2562d4e839015fd0e2aaafa1230e7edbece1dd28f85128d77d13c86d65609b1662c.
Every encoded before-vector reconstructed exactly;model/statistics/input hashes
were checked before/after and independently read back by primary.

The first offline helper completed computation but failed JSON serialization of
one NumPy aggregate. Its traceback/assignment are retained. The corrected prepared
execution used the same original absolute deadline;exit0,all5002 records audited.
No game/model/dependency writes or hidden retry occurred. Local evidence:
reports/local/shot-selection-audit-20261021/{assignment-initial.json,assignment.json,
console.txt,console-second.txt,analysis.json}.

## Implementation and validation
shot_diagnostics.py is a pure bounded helper;it preserves unknown/overflow and
uses the same nearest16 enemy capacity as encoding. It rejects mismatched frame/
entity identities and invalid direction/tolerance. Legacy coarse proxy remains
available. No hard action mask or reward for shooting walls is introduced.
Focused gate:48 tests passed;lint/format and mypy65 files passed. Full Check.ps1
exit0:2342 tests passed,zero failures/skips,55 strict items,pip consistency passed.
All437 input hashes matched before/after execution and primary readback. Local
gate evidence:reports/local/shot-selection-checks-20261021/{assignment-checks.json,
full.log,result-checks.json}. Final docs use strict/diff/link checks only.

## Native positive control: incomplete damage qualification
Executed exactly once,Continue/file2/Isaac,session6459c5a9a1cb43a9bfc38aab62f8e225,
epoch1,room83,frames76769->77072. Scripted start(560,280),final(280.760,198.649).
197 completed1-update decisions:180 route,2 waypoint settle,12 final settle,
3 guarded left-shoot commands. Target1 stayed at(80,200);its current center line
was clear,in range and within8unit transverse tolerance at every shooting decision.
All197 selected actions joined native accepts with correct direction/session/epoch,
107 lag0frames,90 lag1. Encoded policy vectors reconstructed exactly. Ground grid
and expected context stayed unchanged. The wrapper's legacy status label
`frozen_inference` was generic;the mode/controller/action phases explicitly identify
scripted control and no model inference occurred.

The first observed player health loss stopped the probe:red half-hearts6->5.
Target HP remained10->10 at observed endpoints. Stop obeyed the recorded bound;
there was no retry,reset,New Run or extra budget. Three accepted commands are not
proof of three tear births or sufficient projectile flight/cadence coverage.
No damage qualification and no broken-projectile conclusion are justified.
This remains an unfinished native acceptance task,not a passed positive control.

Cleanup independently confirmed successful native shutdown/observer close,absent
game/listener/owned approval/temp approval and zero cleanup errors. All frozen
source/deployed/model/normalizer/pointer hashes matched at readback before final
documentation edits. v2/v3/v4/v5 checkpoint artifacts remain unchanged;current
model is stilla0a93c29-s20-t26368. No training samples or model updates were created.
Local receipt:reports/local/shot-selection-audit-20261021/{verification.json,
native/assignment.json,native/native-game-log.txt,native/session/*}.

## Reward-scale observation and interpretation
Current configured reward is2.0 for an enemy's entire HP plus0.5 for its kill;
one player half-heart costs8.0. The room-clear bonus is8.0. Thus one half-heart
costs3.2 full enemy damage+kill rewards (not counting clear),or32 times the physical
room's0.25 novelty allowance. The native control registered-8.101 combat return
after one health loss;the preceding stuck five-minute policy registered-2.6428.
Different durations/controllers make this descriptive,not a paired policy ranking.

Inference:sparse firing successes plus the immediate penalty can reinforce hiding
before the model discovers successful attack/dodge behavior. It does not prove
that changing these coefficients would solve learning. No coefficients were changed.
There are two evidence needs:an actual clear-shot HP-drop control with sufficient
native tear/cadence observation,and a declared firing curriculum/evaluation with
enough successful examples. Longer unchanged runs or a probability/weight change
alone are not acceptance. A new room may help but needs explicit New Run authority.

## OpenSpec verification
| Dimension | Result |
|---|---|
| Completeness |3/4 tasks;native positive-damage task remains unchecked |
| Correctness |1 added requirement,3 scenarios mapped to shot_diagnostics.py and20 new tests;native clear proxy/accepted commands verified,actual damage not verified |
| Coherence |Policy-only diagnostics,unknown/overflow/capacity handling and unchanged contracts follow design;no training/deployment changes |

No archive or improved-play acceptance. The blocked native task is an evidence
limitation at the planned health bound,not a need to invent missing hits or silently
relax limits. Next work must record its own finite probe/curriculum plan.
