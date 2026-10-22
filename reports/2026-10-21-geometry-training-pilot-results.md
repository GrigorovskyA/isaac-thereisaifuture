# Evidence: geometry schema2/v4 five-minute pilot

Date: 2026-10-21, Europe/Amsterdam. This recovers the already-completed pilot after
both coordinating chats reached their usage limit. It does not resume training.
The user's observation of continued corner stagnation is supported by the trace.

## Execution, lineage and checks

Source revision during execution: 0e94999a16831f04f120dc2c93d87a978249514d.
Plan: [explicit warm start and finite pilot](2026-10-21-geometry-warm-start-plan.md).
One Luna/high worker launched the prepared pilot command once; the standalone
runner completed even though the worker's reporting turn later hit its usage limit.
Primary recovered actual result/log/checkpoint evidence directly, without a retry.

- Root: runs/live-geometry-v4-pilot-20261021; seed20, observation2/723,
  reward live-firing-v4, collector live-segment-refresh-v1.
- Config hash: 10cb703000aff1f3f6291e43c41f7a0c932f59b76c865b30b542d0050804eea0.
- Initial warm start:10cb7030-s20-t21760, explicitly expanded from preserved
  conservative-v2 7d53f55f-s20-t21760. Original v3 7951bf19-s20-t24064 unchanged.
- Latest:10cb7030-s20-t24064, nine complete 256-step rollouts,2304 saved new steps.
  Another196 completed decisions were unsaved; one additional accepted timer-boundary
  action has no completed endpoint and no learning credit. No fresh model fallback.
- Loaded SB3 epoch/update counter340->376; Adam step1360->1504. Saved observation
  RMS count21766.0001->24079.0001 =2304 steps plus9 collection resets. Model and
  normalizer loaded successfully with723 inputs; parent chain increments are exact.
- The source gate passed105 targeted/2294 full tests,52 strict items and synthetic
  CPU smoke before the run; no implementation changes are made by this analysis.
  Docs/task edits use strict validation, links and diff checks, not repeated RL tests.

Exact entry: `.venv/Scripts/python.exe -u reports/local/geometry-training-pilot-20261021/pilot.py --run`,
PYTHONUNBUFFERED=1, working directory D:\isaac. Helper SHA256
 df47b7fa34dd3b59f62d0f2fe17305419b7e97069764093195e5eb2de5b4a9d9;
assignment SHA25643f6839595cc6ce6776c392dd8abfb0035904e356aa3c3e43577c0f815f5fdcd.
Declared caps:300s inclusive startup,2GiB,128MiB paired trace,10 natural death
restarts/observed deaths,zero retries or infrastructure faults,9000 sampled native
updates without registered progress. Only Continue/file2; no New Run or extension.
Absolute action/cleanup stops were1792606739.7564585/1792606784.7564585 Unix;
actual SessionClock supplied the tighter effective runtime deadline.

Actual action window299.345698s including startup, reward endpoint span273.791808s,
script plus cleanup302.234044s. Runtime roots147370217 bytes, trace36960301 bytes.
Script exit0, worker process exit0, state completed_budget. This is an approximately
five-minute inclusive-startup experiment, not five full minutes of combat learning.

## Native gameplay result

| Metric | Closed v3 pilot | New geometry v4 pilot |
| --- | --- | --- |
| Completed endpoint pairs | 2506 | 2500 |
| New saved steps | 2304 | 2304 |
| Observed enemy HP-loss lower bound | 0 | 0 |
| Observed player half-heart loss | 0 | 0 |
| Observed clear edges | 0 | 0 |
| Poses within20 units of(70,410) | 96.49% (2418/2506) | 97.72% (2443/2500) |
| Poses rounded exactly to(70,410) | 82.48% | 86.08% (2152/2500) |
| Requested motion under0.5 units | 70.87% | 84.25% (2000/2374) |

Both are single adaptive training trajectories with matching recorded initial raw
state; contracts and collection behavior differ. This is descriptive, not a held-out
frozen/multi-seed comparison or proof of causal regression. Partial endpoint damage
coverage cannot prove zero actual hits. No improved-play claim is supported.

All2500 decisions stayed in one physical room/session/epoch/visit. Ten accepted
handoffs are collection segments, not ten rooms or successful episodes. Outcomes
remain empty, not inferred deaths or clears. Selected movement: left1280,down1015,
none126,up44,right35;91.8% left/down. Shooting: up1562,left341,none379,down128,
right90. Standing against walls and shooting upward remain the dominant behavior.

Native identity: session ad2513c463cf4a6db092f71426c8b18a,epoch1,visit0,
frames59095->67303. Fresh native `[Continue, 2]` and active Isaac/type0 verified;
no `[New, 2]`. Bridge reports0.5.0-dev,Lua5.3,no extender; installed game version/
Steam build not exposed. No save/Cloud/launch-option or third-party mod edits.

## Freshness and new-feature integrity

All5000 before/after endpoints reconstruct the723-vector and unchanged649 prefix
exactly, with matching frame and visible enemy identities; no oracle input was
added. Actual learned tensors retain723 input columns. Each of the nine optimizer/
checkpoint gaps refreshed collection; gap spans24-32 frames and first-action lags
were1,1,0,1,0,1,1,0,0. Across all2500 completed native action joins,2262 had0-frame
and238 had1-frame lag. The earlier9-21-frame post-update lag did not recur in this
recorded pilot. This qualifies this actual optimizer load, not all future latency.

Total native span8208 includes7950 sampled updates and258 explicitly unobserved
gap updates. Gaps generated no fictional actions/outcomes. The2501st native action
was accepted20.7ms before the deadline and explicitly released67ms later; it has
no endpoint or saved training credit. All2500 completed actions match ordered
session/epoch/directions. No dropped/withheld actions or reported observation gaps.

New actor/critic input weights are nonzero (7680 entries each; maximum absolute
0.039526/0.017517), and Adam advanced normally. Frozen counterfactual analysis on
64 recorded policy-only vectors, copying probability tensors before subsequent
calls, found geometry-present versus74 raw unknown/zero features changed movement
probabilities by up to0.103779 and shooting by0.038841. These are offline
counterfactuals, not probabilities logged during native training. New features
are connected and influence decisions; this does not establish a correct response.
An initial local calculation reused SB3's mutable distribution object and falsely
returned zero differences. It was discarded, retained locally, and rerun using
copied tensors. No production/model change was needed for that analysis correction.

## Why this trial did not resolve the corner

Corrected novelty reward totaled0.0570361122569918 across13 moving pairs. All positive
bonuses occurred at decisions7-34; the following2466 decisions earned no such bonus.
All2109 pairs with displacement<=0.5 units earned0. No repeated standing reward was
introduced. Crucially,4937/5000 endpoints lacked complete interpolation support.

Offline queries of the measured final-frame reward geometry show:

| Hypothetical position | Current v4 potential |
| --- | --- |
| (70,410), observed corner | unavailable |
| (80,410) or(90,410), initial rightward displacement | unavailable |
| (70,400) or(70,390), initial upward displacement | unavailable |
| (80,400), both coordinates inside supported lattice | 0.393939 |
| (90,390) | 0.40625 |
| (280,280) | 0.764706 |
| (280,200), measured firing lane | 1.0 |

These are hypothetical reward-field queries against a saved measured grid/target,
not new native movement or proof of a traversable arbitrary segment. Requiring all
interpolation corners removes the former sign bug but leaves a reward-signal gap
at walls. The first moves out of this corner are not credited by this term. Actor
prior left/down preference was already strong, and the trial contained no successful
damage/clear experience to teach firing behavior. This combination is consistent
with persistence of the corner, not proof that any one factor is the sole cause.

On the same64 late-corner raw states, separate frozen recurrent replays of initial
and final policies gave mean left/down probability0.889947->0.932673. Up shooting
remained0.606956->0.597916. These reconstructed probabilities are not saved native
behavioral probabilities. Only three early before-states had clear in-range X;
two actions did not shoot and one shot up while X was to the right. Opportunities
were too sparse to establish a useful learned firing policy.

Next is an offline corrective reward contract: provide a measured, obstacle-aware
progress signal for initial moves away from a wall, retaining sign correctness,
unknown handling, shared room caps and no repeated/standing credit. Do not infer
unmeasured clearance or replace learning with a route-following controller. Test
counterfactual up/right/retreat/blocked moves before any further experiment. Reassess
the strong inherited policy prior as a separate hypothesis. No longer unchanged
run or coefficient-only success claim follows from these results.

## Verification, source audit and cleanup

Primary ran local analyze.py,verify-pilot.py,analyze-geometry.py,
analyze-freshness-features.py,compare-descriptive.py and diagnose-corner.py, plus
native timestamp/span/source checks. JSON evidence and scripts remain under
reports/local/geometry-training-pilot-20261021. Raw logs/models/approvals are not in Git.
Luna hit its usage limit during reporting; primary performed recovery directly.

The original strict verifier exits1 on11 changed frozen documents. This failure is
retained in primary-verification.json, not described as an unchanged670-file pass.
At recovery readback, before result/task document edits, all659 remaining inputs
match, including runtime source/config/helpers/deployed Lua
and original/new parent models. All11 documents match exact historical snapshots
or pre-run Git bytes. The later documentation-only workflow commit92deebc was made
at1792608652 Unix, after pilot completion1792606502.888. Source audit found no
runtime-critical mismatch. post-run-source-audit.json records every path/hash and
primary-acceptance.json explicitly reconciles this later documentary drift. There
are no other action/storage/cleanup errors in the strict readback.

Native successful shutdown,observer closure and timer-boundary explicit release
were verified. Primary separately checked no Isaac process,9528 listener,owned
approval or temporary approval. Both preserved v2/v3 artifacts and the initial
schema2 warm start remain unchanged. Latest child is retained, not selected as a
better gameplay model. No background task or standing resume authority remains.

## OpenSpec self-review

Using openspec-verify-change on geometry-policy-warm-start; this is primary
self-review, not independent review. Both requirements and three scenario groups
map to geometry_migration.py/test_geometry_migration.py, the declared finite
assignment, native lineage/control evidence and this negative-results analysis.
Completeness4/4; explicit migration and bounded trial requirements accepted.
Gameplay improvement is not an acceptance criterion silently inferred from task
completion. Change remains unarchived. Native special weapons, held-out/multi-seed
improvement and broader Dead God progression remain not_run/not established.

No implementation was changed in recovery. Strict change validation and changed
local-link/diff checks are run; the successful unchanged full RL suite is not repeated.
