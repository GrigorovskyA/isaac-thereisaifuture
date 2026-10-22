# Evidence: five-minute firing-reward learning pilot

- Date/time:2026-10-21, Europe/Amsterdam; native wall start15:40:38.835,
  cleanup finished15:45:40.485. Revision425f26754249647fcab26cb258f25f28d2291c8c.
- Scope:one user-requested finite v3 warm-start training trial, not the stopped
  hour/four-hour experiment. [Declared plan](2026-10-21-firing-training-pilot-plan.md).
- File2/Continue verified from fresh menu metadata/native log; initial Isaac/type0
  verified before gameplay. No New Run. Steam launch, guarded menu input, structured
  bridge gameplay. Ordinary user profile remains the authorized exception, not isolation.
- Mod0.5.0-dev,Lua5.3,no extender,protocol/schema1. Game version/Steam build unavailable.
- One fresh gpt-6-luna/high script worker; primary prepared migration/helper and
  independently accepted actual artifacts. No worker implementation or retry.

## Assignment and checks

Prepared exact command from D:/isaac, PYTHONUNBUFFERED=1:
`D:/isaac/.venv/Scripts/python.exe -u D:/isaac/reports/local/firing-training-pilot-20261021/execute.py`.
It executes the declared194-test targeted suite, then one `pilot.py --run` invocation.
Helper SHA2562a6c04d2557ec42477068f3d79ffd536f5eee594544f70dfd4e02e42ff608320;
driver7baf6cb0f351b24f2860d8f103694a93e41524e133ec26d8c0945b19c00a3ae0.
Assignment start-before1792590170.143783,absolute action-stop1792590530.143783,
cleanup-stop1792590575.143783 Unix. These were not renewed.

Native maximum300s inclusive setup; integral lease alignment gave299.165s actual
action window. First-to-last completed reward endpoint span273.603s; native update
span8206. Total startup/action/normal-cleanup301.650s. This completes the declared
five-minute inclusive-startup window, not five minutes of active combat collection.
Step/restart sentinels1billion/5000,no deathcap,maxfaults0,no retry,2GiB disk,
128MiB trace,9000-update registered-progress guard,time-dominant navigation.
Total local pilot/check artifacts143,776,612bytes at primary measurement;
paired trace34,498,150bytes,within bounds. No additional session/stage launched.

| Check | Exit | Status | Evidence |
|---|---|---|---|
| Explicit migration/readback |0|passed|Byte-identical model/normalizer; RNG/config fields checked; parent untouched |
| Fresh targeted checks |0|passed|194 passed,zero skips,10.72s; existing Lua5.3 harness |
| Full source gate |n/a|not_run this trial|Unchanged source/mod/tests retain prior2269 tests/zero skips,49 strict items and synthetic smoke; no gratuitous rerun |
| Native finite training |0|passed|completed_budget,wall-time stop,nine new checkpoints |
| Trace/vector validation |0|passed|2506 paired endpoints,original encoder vectors reproduced,no detected identity/input separation errors |
| Geometry/bonus replay |0|passed|5012 plain-tear endpoints,range260,five candidates,zero overflow; exact replay match |
| Initial primary action-count check |1|failed|Assumed every accepted action had a completed endpoint; found2507 accepted versus2506 completed |
| Completed/boundary action classification |0|passed|2506 action joins;one separately proven timer-censored action with explicit release,not a fabricated sample |
| Checkpoint load/chain/frozen inputs |0|passed|Nine256-step descendants;loaded optimizer/timestep state;632 unchanged input hashes |
| Owned cleanup |0|passed|Native normal shutdown and observer closure; primary process/listener/approval/temp absence |
| Frozen model comparison /15-30min stage |n/a|not_run|Adaptive trial is not frozen paired evaluation; no escalation |

Local receipts are under reports/local/firing-training-pilot-20261021:
assignment.json,migration.json,offline-result.json,targeted.log,session/result.json,
analysis.json,firing-analysis.json,primary-verification.json,timing-summary.json and
descriptive-comparison.json. Initial failed primary-verification-initial.json is
retained. Raw logs, models, normalizers and private approvals are excluded from Git.

## Learning and storage

Original7d53f55f-s20-t21760 and original latest remain unchanged. Separate v3 initial
7951bf19-s20-t21760 preserved byte-identical model/normalizer/optimizer/RNG under
the explicit objective-transition receipt, not a fresh network. Canonical config
7951bf196cd5181f825c71c6e40d496a2e2c7cfc843755e4e05cafdf04a22c8c,seed20,
reward live-firing-v3,observation649/schema1,action schema1,CPU RecurrentPPO.

Latest7951bf19-s20-t24064 contains2304 new saved timesteps across nine complete
256-step rollouts. Model reload reports24064 steps and SB3 _n_updates340->376
(four training epochs per rollout);this is evidence of optimizer execution, not
better play. Normalizer observation count21766.0001->24071.0001.
All nine manifests/artifact hashes and monotonically linked parents verified.
Last model SHA256a8fb6c500fd1ab356c323edf602b542b4ae0ccf2d466f336c2b252d31f67775d,
normalizer0ba0c288b68400a272c05e73fb010f8116a62cbd9441ad47f0855d100b49dcb6.
Inherited return statistics and critic were not reset; the new objective/collector
baseline discontinuity was recorded before learning.

2506 completed decisions minus2304 saved=202 completed rollout steps unsaved.
There was also one accepted action at the timer boundary without a completed
endpoint:sequence2519,frame56411,accepted monotonic261545270ms,then explicit
release261545337ms;deadline261545289.650ms. It started before the deadline and
released during cleanup. It earns no completed sample, reward or learning credit;
do not conceal it inside the202 completed-unsaved count. Initial count mismatch
was investigated against the native release/timing evidence, not ignored/retried.

2506 completed selected-action/native-command joins matched session/epoch/directions.
2229 commands executed in the policy frame,268 one frame later,and nine9-21frames
later. Each larger delay followed a completed checkpoint by35.5-51.1ms in the
paired wall/monotonic timeline (optimizer-lag-audit.json),supporting association
with optimization/checkpoint pauses; this timing observation
does not establish continuous fresh policy state during optimizer work. Preserve
the actual delays;do not claim all actions were within one frame. Game session
0781af09e392428ca9f743f3275401a2,epoch1,room visit0,frames48205->56411.

## Gameplay and comparison limits

| Metric | Frozen reference audit | Adaptive v3 pilot |
|---|---:|---:|
| Completed decisions |561|2506|
| Native update span |1800|8206|
| Observed enemy HP-loss lower bound |0|0|
| Observed player red+soul loss,half-hearts |0|0|
| Observed clear edges |0|0|

Raw initial player/enemy/room/grid state matched the frozen shadow audit. However,
deterministic frozen inference versus stochastic adaptive training and unequal
budgets are not a paired frozen model evaluation. No winner or improvement claim
is accepted. Enemy HP/terminal coverage is partial:zero sampled HP loss is not
proof of zero actual damage. Enemy disappearance is not kill evidence.

Five accepted combat handoffs/four unknown software episodes stayed in one physical
room/visit,not five rooms. No observed death/clear,transport fault,observation gap
or withheld action. Endpoint poses2067/2506(82.48%) lay within5units of(70,410).
Of2245 requested movement pairs,1591(70.87%) moved under0.5units;including no-move
actions,1786/2506 pairs were at or below0.5units. Corner stagnation remains.

Firing bonus17 positive pairs,total0.11115502123989211,below the0.25room allowance;
all1786 stationary/tiny-motion pairs received zero. Replayed bonus exactly matched
the2506 scalar records. Reward-ledger history remained one physical room across
software resets. Total combat reward-2.613178312093291 is not a success metric.
All5012 endpoints reported plain tears,range260,five positive candidates and valid
walking potential. Native sampling supports the new signal;it did not establish
that this policy learned to hit enemies or clear the room.

## Cleanup, self-review and next action

Worker exited0,cleanup_errors empty. Primary separately checked native observer
closure/successful game shutdown,no Isaac process,no listener9528,no owned approval
or temporary approval. All632 tracked/source/config/parent/helper hashes unchanged.
The game performed its ordinary save/Cloud activity on normal exit;the agent did
not edit saves,Cloud settings,launch options or install third-party mods.

Primary self-review against the plan accepted bounded learning/storage/cleanup and
descriptive gameplay measurement. No production source/test/mod change occurred in
this trial. Explicit migration is experiment-specific;strict ordinary v2->v3 resume
refusal remains. Latest can load offline, but a new live resume/interruption test
and exact collector-ledger restoration are not implied by that readback.

OpenSpec verification uses openspec-verify-change for firing-position-shaping;
primary self-review,not independent review. Requirements/design/scenarios remain
as reviewed with the original2269-test gate;strict validation passed after the
pilot. The source/input freeze was verified before post-run evidence/status edits.

| Dimension | Result |
|---|---|
| Completeness |4/5 tasks;critical incomplete2.2 retains15-30min/comparable frozen evaluation |
| Correctness |Native shaping/learning/save/cleanup observed;improved gameplay not established;actual damage incompletely covered |
| Coherence |Explicit planned objective transition,new root,original preserved,no schema change or automatic escalation |

Warnings to resolve before another experiment:corner stagnation,optimizer-associated
policy/action delay,and collector-local reward history across external restart.
No applicable new source checks were omitted;fresh full gate was unnecessary for
unchanged source and is explicitly not_run. Do not archive this incomplete change.

firing-position-shaping remains4/5,unarchived:task2.2's15-30min/frozen comparable
evaluation requirements are incomplete. Do not advance automatically. Next concrete
action:offline diagnosis of policy-visible target geometry/vulnerability and action
probabilities on these saved traces,including the optimizer observation delay,
before another longer experiment. Preserve both original t21760 and new t24064.
