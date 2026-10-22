# Evidence: boundary-supported-progress

Date2026-10-21 Europe/Amsterdam. Source base3f0c3aa plus this change.
Primary implementation/self-review; one gpt-6-luna/high script runner executed
prepared offline/native checks. No independent code review. Raw logs/models stay
under reports/local and runs outside Git. See [plan](2026-10-21-boundary-progress-plan.md).

## Findings and correction
The user clarified that Continue places the character at the door; the corner is
a later policy behavior. Attempt01 wrongly required initial corner coordinates and
stopped before any movement. Attempt02 captured actual door(560,280),then275 frozen
decisions to the left wall around(70.101,354.509); no scripted escape occurred.
It exhausted the900-native-update progress window. One final attempted step is
separate from275 completed decisions. Partial endpoints do not prove zero damage.

Attempt02 also exposed rounded source coordinates in the new evidence,which
strict pose matching rejected. Final Lua exports raw coordinates and queries that
exact source vector; fractional-source regression prevents this mismatch.

Attempt03:46 completed decisions,34 frozen policy then12 scripted right/up moves,
one room83/session4c66784700834c71a3c237c62128c4b2/epoch1. Initial(560,280),
unsupported wall(69.778,350.915),final(168.569,270.000). All12 prescribed escape
commands completed without death/clear/context change. This is measured geometry,
not learned escape. Actual old shadow ledger paid0.070806 total and zero during
escape; net combat return0.022806 is a different metric. Maximum earlier potential
0.764706 explains the second blind spot: high-water novelty prevents later recovery
below the door-to-wall record,even when local geometry improves.

Before publishing any v5 child,we added signed recovery: measured retreat charges
bounded debt; same-target approach refunds only charged debt. Outstanding room
debt<=0.25; novelty allowance remains0.25; debt survives reset/reentry and target
switching. Unknown/stationary/changed unsupported patches do not charge or refund.
Recovery cannot create positive cumulative undiscounted reward; closed supported
cycles cancel. This is not a discounted policy-invariance guarantee.

Replaying the47 actual attempt03 endpoints under the final ledger yields signed
shaping return0.020496 and positive escape-phase shaping0.036219. This is offline
reward recomputation on measured native geometry,not a new native training outcome.
The earlier shadow-ledger/source hashes remain recorded; its two Python reward
files intentionally changed afterward. Final Lua/deployed geometry/model parents
are unchanged. Do not call the earlier complete frozen map unchanged today.

## Offline results
| Check | Exit | Status | Evidence |
|---|---:|---|---|
| Focused boundary/Lua/legacy checks |0|passed|74 earlier targeted;21 final boundary tests;full gate includes all |
| Check.ps1 final publication iteration |0|passed|2322 tests,zero failures/skips;54 strict items;lint,format,mypy64files,pip |
| Final checked input readback |0|passed|430 hashes unchanged before/after and primary readback |
| Native boundary capture/12-command qualification |0|passed|Attempt03,measured source/patch fields and owned cleanup |
| Five-minute child training/persistence/cleanup |0|passed|2502 completed,2304 saved,198 unsaved;9 complete rollouts;699 frozen inputs at readback |
| Gameplay improvement |-|not demonstrated|97.16% old-corner occupancy;observed damage/clear lower bounds0 |

Local evidence:reports/local/boundary-progress-recovery-check-20261021/{full.log,
result-checks.json,assignment-checks.json}; reports/local/boundary-progress-20261021/
{native-analysis.json,native*/session/*,migration.json}. Earlier failed temp cleanup,
missing test scratch parent,initial fractional-test fixture error and superseded
native attempts are retained as intermediate failures,not final passes.
Final publication gate:reports/local/boundary-progress-publish-check-20261021/
{full.log,result-checks.json,assignment-checks.json};2322 passed,430 frozen inputs.

## Compatibility and explicit lineage
Default firing reward staysv4; boundary flag explicitly selectsv5 and requires
firing/gate/navigation. v4 resume asv5 fails before environment creation. No policy
inputs changed:observation2/723 with649 prefix retained; new evidence only in oracle.
Legacy v3/v4 replay remains available. No dependencies,save/Cloud/mod-setting changes.

New initial childa0a93c29-s20-t24064 from10cb7030-s20-t24064,seed20,schema2,
rewardlive-firing-v5,collectorlive-segment-refresh-v1. All weights/Adam tensors,
observation/return normalization statistics and manifest RNG verified equal after
save/reload;timesteps24064,optimizer376,Adam1504 unchanged. Collector observations
and recurrent state cleared. Return-stat inheritance across objectives is explicit.
Config hash:a0a93c29b588fb2ee4b23e3c19f16c5e4124b97fb312503978a6ada405f13f15.
v2/v3/v4 parents and pointers remained unchanged. Migration is not learning.

## OpenSpec verification and limitations
Using openspec-apply-change and openspec-verify-change. Requirement implementation:
Lua capture/negotiation plus FiringGeometry, FiringProgressV5, CLI/options/checkpoint
contract. Scenarios covered by test_boundary_progress,test_lua_boundary_support and
legacy/coherent compatibility tests. Signed debt cap/refund/cycle/reset/reentry/
unknown coverage is explicit. Native blocked/unknown API behavior remains simulated;
native ordinary positive support was measured. Whole-body path safety,all weapons,
held-out multi-seed improvement and Dead God acceptance remain unverified.

| Verification dimension | Result |
|---|---|
| Completeness |6/6 tasks;1 added requirement;no removed/renamed requirements |
| Correctness |All5 scenarios mapped to source/tests;native ordinary positive support plus actual training/replay measured;blocked/unknown native APIs simulated only |
| Coherence |Measured links,explicit v5 compatibility,raw pose binding and bounded debt follow final design;historical v4 defaults/replay retained |

Native body safety/other weapons/held-out gameplay improvements are not verified.
No archive or improved-play acceptance is implied by task completion. Final self-review
found no remaining implementation blocker within this scope;future firing/behavior
work remains necessary. Docs-only final updates use strict validation/diff/link checks;
the unchanged successful final code suite is not rerun merely for report edits.

All three diagnostics ended with no cleanup errors,owned game/listener/approval
absent. Attempt01 positional guard was an engineering error,not missing user
permission. The higher wall position and continued shots into rocks are the same
policy failure; no gameplay improvement follows from relocating stagnation.

## Completed five-minute learning pilot
Single Continue/file2,actual door start,seed20,one physical room/session/epoch,
ten collector handoffs. Inclusive action window299.578seconds;startup/cleanup total
302.328seconds. No extension,retry or New Run. Source699-file snapshot unchanged at
primary post-run readback before these result/status edits. Every2502 completed
native action joined its policy endpoint:2244 lag0frames,258 lag1. Nine actual
post-update refreshes resumed with lag0/1;all5004 schema2 endpoints reconstructed
exactly with no oracle input leakage. Trace37,696,766bytes<128MiB.

Latest childa0a93c29-s20-t26368:2304 new saved steps,nine256-step rollouts;
198 completed unsaved steps. Optimizer376->412,RMS observation count24079.0001->
26392.0001. Model/normalizer reloaded and all9 parent links/increments validated.
The latest modelSHA2566e94cc1ffeb3280adf5881cc56e1625cbe62f400a1c1b34b173165a2f0f55d08,
normalizerSHA2562d4e839015fd0e2aaafa1230e7edbece1dd28f85128d77d13c86d65609b1662c.
Preserve this child as evidence,not as a promoted better player. No process-crash
or resumed-native-training test was performed;deadline interruption/readback only.
Reward ledger history persists within the collector/session,not serialized across
independent process launches.

One additional command was accepted15.2ms beforedeadline and released66ms later,
with no completed endpoint or learning credit. The copied legacy audit initially
required its native accepted frame to equal the last endpoint frame;it was one
frame newer,consistent with all observed0/1frame joins. The raw failed audit is
retained as primary-verification-strict-initial.json. Reconciled audit explicitly
checks0..1frame boundary delta,same session/epoch,predeadline acceptance and bounded
explicit release. No production guard/test was weakened and no endpoint invented.

Final publication self-review added a conservative unknown-field refund guard:
even if shared old geometry is usable,the actual after-pose field must be known
before recovery can refund debt. A synthetic changing-goal regression covers it.
This was after the native pilot;all5004 pilot fields were known,and replay of
every2502 signed term remains exact after the guard (max error0). The final
publication full gate is recorded separately from the earlier training-source
gate. Only this Python reward file changed after native readback;Lua/actions/
model artifacts remain as measured. No native outcome is relabeled as a new run.

| Metric | Earlier v4 pilot | Current v5 pilot |
|---|---:|---:|
| Completed decisions |2500|2502|
| Observed enemy HP-loss lower bound |0|0|
| Observed player half-heart loss |0|0|
| Observed clear edges |0|0|
| Within20units of(70,410) |2443/2500 (97.72%)|2431/2502 (97.16%)|
| Requested moves with<0.5displacement |2000/2374 (84.25%)|1950/2406 (81.05%)|

Single adaptive trajectories with different initial weights,not a held-out A/B
comparison. Partial endpoint coverage cannot prove zero actual hits/damage.
No gameplay improvement is demonstrated. The inherited left/down choices remain
2306/2502 (92.17%);upshoot1463/2502. 2057 decisions selected shooting. With a
transverse aim tolerance20units,1440 had only blocked near-axis target lines,
615 had no near-axis target and2 had a clear one. These are measured target-line/
aim proxies,not actual tear collision traces;the strict8unit counts are preserved
locally. The user's report of continued ineffective firing is supported.

The feedback correction did work:all5004 endpoints had v5 potential versus51 with
v4 support on this trace.231 positive and230 negative position terms;positive sum
0.173115,negative-0.150947,net0.022168. Every logged signed term exactly matched
offline replay (max error0). Novelty0.091384 minus outstanding debt0.069217 equals
net shaping;recovery did not create unbacked credit. Net combat return-2.642832
includes other components and is not this shaping sum.

Cleanup independently verified successful native shutdown/observer close,absent
game/listener/approval/temp approval,zero cleanup errors. v2/v3/v4 parents and new
initialv5 checkpoint remain unchanged. No learning or automatic next run remains.
Task6 is complete as execution/evaluation;better play remains unaccepted.

Next work should isolate firing/clear-line decision learning and the strong
inherited action prior. A short simpler-room control may be useful with the same
saved model,but replacing this Continue requires explicit New Run authority.
Do not spend a longer budget merely because reward/weights now change.
