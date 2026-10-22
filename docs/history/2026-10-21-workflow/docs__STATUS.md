# Project status

User requested launch2026-10-21. Explicit geometry schema2/v4 warm start prepared
from preserved t21760:10cb7030-s20-t21760 in runs/live-geometry-v4-pilot-20261021.
Zero-expanded74 input columns/moments,old weights/optimizer/RNG/statistics retained;
64 native-vector recurrent equivalence cases had zero value/logprob error. New
feature normalization uses explicit neutral prior/shared count,not historical data.
105 targeted/2294 full tests,52 strict items and CPU smoke passed,zero skips;
660 frozen inputs verified. Original v2/v3 unchanged. Change2/4,unarchived. Next:
one user-requested300s Continue/file2 pilot,no New Run/automatic extension. See
[plan](../reports/2026-10-21-geometry-warm-start-plan.md).


Fresh collection boundary2026-10-21 qualified:278 frozen t21760 actions,three
explicit36-frame idle gaps. Fresh first post-gap action lags0/0/1;all278 native
joins within1 frame.900 sampled updates plus108 unknown idle updates,without
fabricated samples/outcomes.556 schema2/prefix endpoints,76 native frozen inputs
and owned cleanup independently verified. No optimizer/model/checkpoint update.
Final journal-start cleanup regression149 targeted/2292 full,51 strict items and
CPU smoke passed,zero skips;649 final frozen hashes checked. Change
fresh-rollout-observations4/4,unarchived. Next:explicit compatible723-input lineage
plan before any learning. No automatic resume,New Run or duration escalation.
See [native and final evidence](../reports/2026-10-21-native-fresh-rollout-observations.md).


Fresh rollout observations2026-10-21 implemented offline:strict input release at
rollout end,public SB3 force-reset after optimizer/checkpoint work before the next
actor input. Explicit unknown collection gaps;correct normalization/LSTM masks,
no invented transitions/outcomes. Gated live enables live-segment-refresh-v1;
generic defaults unchanged.148 targeted/2291 full tests,51 strict items and CPU
smoke passed,zero skips. Primary verified649 frozen inputs including t21760/t24064.
Change fresh-rollout-observations3/4,unarchived;finite frozen native gap check next.
No training/model migration/New Run. See [evidence](../reports/2026-10-21-fresh-rollout-observations.md).


Native coherent geometry2026-10-21 passed for the ordinary-tear scenario:279 frozen
v2 decisions/903 updates,558 same-frame723-vector/prefix reconstructions. Range260,
blocked in-range Y and clear out-of-range X distinguished;corner left/down blocked.
V4 shadow total0.036865796,9 positive/237 stationary-zero pairs;495/558 endpoints
lack interpolation support. Native action lags245 at0/34 at1;76 frozen hashes and
owned cleanup independently verified. No learning or better-play claim. Original
models preserved. Change4/4,unarchived;optimizer freshness and explicit compatible
schema2 lineage remain next. No automatic training/New Run/escalation. See
[native evidence](../reports/2026-10-21-native-coherent-combat-geometry.md).


Coherent combat geometry2026-10-21:implemented offline under the new active
change `coherent-combat-geometry`. Active firing opt-in now selects v4:corrected
subcell sign,per-target records/shared room cap,legacy v3 replay retained. Separate
opt-in observation2 adds74 observable range/ground/shot features to the unchanged
649 prefix;723 inputs require explicit compatible checkpoint/normalizer schema.
No old model migration,game deployment or learning occurred. Saved2506-pair replay
reproduces exact v3 total;v4 pays0.047586478 and no stationary credit.2465 endpoints
lack full interpolation support,so this is no proof of resolving corner behavior.
261 targeted/2285 full tests passed,zero skips;50 OpenSpec items and CPU smoke
passed. Primary verified641 frozen inputs including both protected checkpoint
triplets. Change3/4,unarchived. Native qualification and optimizer freshness remain pending;no automatic resume,
New Run or duration escalation. Preserve t21760/t24064. See
[implementation evidence](../reports/2026-10-21-coherent-combat-geometry.md).

User screenshot/trace clarification2026-10-21:entry1(560,280),X=enemy2(560,360),
Y=enemy1(80,200),corner2~(70,410). Early bonuses correspond to approaching measured
firing positions around X's blocker,not standing in the corner. Actual Lua source
exports12 nearest obstacles,not24 encoder slots;41 omitted. The relevant stone
(80,240) is exported. Representative cell(80,400) is walkable/aligned/in range but
not projectile-clear;Y's positive firing cells lie to its right. This supports
blocked shooting/ineffective geometry interpretation,not total stone invisibility.
Retain reward fixes and explicitly design observable collision/range/shot geometry.
Corrected prior report's obstacle count. Image/raw/code inspected;no production,
model or game change;tests/native not_run. See
[clarification](../reports/2026-10-21-room-layout-clarification.md).

Offline policy/reward diagnosis2026-10-21 completed;no game/training/source change.
Critical production-ledger counterexample:retreat from a clear firing goal150->159
units earns+0.003231509 because path cost forces a detour to the current cell center.
Also one physical-room record suppresses new-target progress;counterfactual per-
target records/shared cap recover only two small bonuses,not a standalone remedy.
All17 native bonuses occurred in first35 decisions;next2471 earned0. Full trace
rejects target mismatch:nearest enemy and reward target match2506/2506. Adaptive
normalization exactly reproduced9/9 checkpoints;zero raw/normalized clipping.
Frozen replay left/down probability89.12%->78.44%,shoot-up60.39%->53.47%;entropy
increases but deterministic choices remain biased. Nine optimizer-associated
9-21frame lags are0.359% of decisions. Luna script exit0;primary verified99 frozen
inputs plus4 original v2 hashes. t21760/t24064 unchanged. No clean correctness/
improvement or longer-stage claim;change4/5 remains unarchived. Next:new corrective
OpenSpec reward change/regressions,then observation freshness and visible-feature
design before another declared5min run. See
[diagnosis](../reports/2026-10-21-firing-policy-diagnosis.md).

Firing-reward five-minute trial completed2026-10-21:299.165s effective inclusive-
startup window,273.603s reward endpoint span;Continue/file2,no New Run. Separate v3
warm start t21760->latest7951bf19-s20-t24064,2304 saved steps/nine rollouts,
202 completed-unsaved steps plus one timer-censored accepted action with explicit
release. Loaded optimizer epochs340->376;normalizer/chain/hash readback passed.
194 fresh targeted tests passed,zero skips;source unchanged from2269 full gate.
Primary verified632 frozen inputs,2506 completed native joins,one boundary action,
normal shutdown/free9528/approval absence. Five software handoffs stayed in one
physical room;observed HP-loss lower bound0,player loss0,clear edges0,partial actual
damage coverage.82.48% poses near one corner.17 position bonuses sum0.111155;
1786 stationary pairs earned0. No improved-play claim or15-30min escalation.
Original v2 t21760 preserved. Change4/5,unarchived. Next:offline target/action-
probability diagnosis,including9 optimizer-associated9-21frame policy/action lags.
See [pilot results](../reports/2026-10-21-firing-training-pilot-results.md).

User accepted a five-minute firing-reward learning trial2026-10-21. Preparing an
explicit separate v3 warm start from immutable t21760,byte-identical model/normalizer,
preserved optimizer/RNG,changed contract/status/budget only. No fresh model or New
Run. One300s inclusive-startup Continue/file2 session,2GiB disk,128MiB trace,zero
faults/retries; no practical step/death count stops. Native execution not yet run.
Do not treat the prepared migration as learning or automatically advance stages.
See [pilot plan](../reports/2026-10-21-firing-training-pilot-plan.md).

Native firing shadow audit2026-10-21 passed for the ordinary-tear scenario;
firing-position-shaping4/5,unarchived. Frozen t21760,v2 policy with v3 shadow reward,
Continue/file2;561 accepted actions,1800updates/~60s before no-progress stop.
All1122 endpoints:plain tears,range260,five projectile-clear candidates,valid
walking potential.8 positive moving bonuses sum0.04201175;549 stationary pairs
earned0;replay matched live logs. Primary verified561 native command identities,
66 unchanged hashes,normal shutdown and no game/listener/approval. No learning or
model/normalizer change;no New Run. Full5min duration not achieved;actual damage
unknown under partial coverage,zero observed clear edges. Next:explicit v3 lineage
and comparable damage/taken/clear5min then15-30min experiment. Native telemetry
success does not establish better play. See [native audit](../reports/2026-10-21-native-firing-shadow-audit.md).

Firing-position shaping2026-10-21:offline3/5,unarchived. Default-off
live-firing-v3 adds bounded novelty credit for movement toward measured reachable
ordinary-tear firing positions, with native projectile-clear evidence; no idle,
shot or repeated approach credit. Reward-only geometry leaves policy schema1/649
inputs unchanged. Old v2 training checkpoints explicitly refused; no migration,
deployment or training. t21760 preserved. Luna/high final194 targeted/2269 full
tests passed,zero skips;OpenSpec49/49;synthetic16-step smoke passed. Primary read
logs and verified387 frozen inputs. Full first attempt exposed Windows CRT errno13
pointer-read sharing denial; bounded Windows-only retry/regressions fixed it.
Self-review/verify recorded;native weapon/range/clearance and actual gameplay
comparison remain not_run. Next:finite frozen shadow-reward native audit,then
explicit compatible lineage and5min ->15-30min damage/taken/clear comparison.
No automatic learner resume/New Run. See [guide](FIRING_POSITION_REWARD.md) and
[evidence](../reports/2026-10-21-firing-position-shaping.md).

Native frozen diagnostic2026-10-21:Continue/file2 verified,563 accepted actions
from unchanged t21760,one visit,1800gameupdates/60.190s combat. Progress guard
stopped before the next action;563 raw/vector pairs validated,7.53MB under64MiB.
527/563 poses(93.61%) clustered near(70,410);all shots up,coarse aim aligned95.56%.
Sampled enemy HP stayed10/10;no registered endpoint damage/clear,not proof of zero
actual damage. Firing-position/blocked-motion diagnosis is supported;range,actual
shot clearance and target vulnerability remain unverified. Worker exit0,owned
normal closure/approval removal,64 frozen hashes and absence of game/listener
independently checked. No weight/normalizer/checkpoint changes or New Run.
Five-minute-maximum pilot stopped early as designed;full5min duration and native
updated-checkpoint restore remain not_run. Changes remain3/4 and storage4/5,
unarchived. Next:versioned weapon/firing-position evidence and bounded shaping,
then a new5min qualification;no automatic resume. See
[native evidence](../reports/2026-10-21-native-combat-progress-diagnostic.md).

Combat progress instrumentation implemented offline (2026-10-21),3/4 tasks,
unarchived. Explicit opt-in bounded policy/raw-oracle endpoint traces and a
registered-progress window persist across same-room software resets; defaultoff.
No reward,observation or model change. Trace vectors are pre-VecNormalize,selected
actions are not accepted-command evidence,and partial HP coverage cannot prove
zero actual damage. Stop releases input before the next action/reset,without
invented death/clear;checkpoint/unsaved accounting retained. Full gate also exposed
and repaired a Windows latest.txt read-sharing race with bounded classified retry.
160 targeted/2229 full tests passed,zero skips;synthetic16-step RL smoke passed;
OpenSpec48/48;primary verified380
frozen inputs and actual logs. Last Luna report hit usage limit after script
completion;primary accepted saved exit codes/logs directly. Storage follow-up4/5.
No native run/deployment/training. Strict latest read:t21760;no game/listener/approval.
Next:separately bounded five-minute native capture,then versioned weapon range and
firing-position reward diagnosis/comparison. Current user authorizes implementation,
not automatic resume/New Run. See [guide](COMBAT_PROGRESS_DIAGNOSTICS.md) and
[evidence/verification](../reports/2026-10-21-combat-progress-diagnostics.md).

Hour attempt STOPPED by user for corner analysis (2026-10-21). No active learner,
game,listener9528 or owned approval. Latest7d53f55f-s20-t21760,14080 new saved steps
from t7680 across55 immutable checkpoints;293 unsaved decisions across two attempts.
14373 combat decisions,~25min16s active collection. Original hour not completed:
first421.547s attempt faulted on Windows status replacement5;after bounded retry
fix and2198-test gate,the Continue-only correction ran1260.703s and ended by user
request with clean release/closure/status. All parents/config/source verified.

Captured continuation:69.96% of11446 accepted poses within5 units of(70,410),
rising42.66%->88.17% across full5min bins.64.30% of requested movement pairs moved
<0.5 units.20 unknown software-boundary episodes remained in one visit with two
recorded enemy identities;no damage/clear events registered in partial oracle.
No improved-play or verified-zero-damage claim. Weight updates are not success.
Reward incentive for safe inactivity is a hypothesis;enemy geometry/actual policy
inputs were not captured. Next:bounded same-frame observation/progress diagnosis,
not another blind training run. Current user instruction is stop and analyze.
See [full analysis/evidence](../reports/2026-10-21-one-hour-stopped-analysis.md).
status-sharing-retry2/2,unarchived:98 targeted/2198 full tests,zero skips,OpenSpec47/47;
411 frozen check hashes and71 offline-analysis hashes independently verified.

Native thirty-minute request (2026-10-21): NOT achieved. Existing Continue stopped
58.766s early after observed ordinary-room exhaustion,zero combat. User then
approved one New Run/file2; native [New,2]/activeIsaac verified. Five-minute timer
completed with35.75s combat,224.188s waiting,318 decisions,three deaths/two restarts.
Primary's pilot restart cap was too small; no long stage launched. Saved256 steps,
62 unsaved;latest7d53f55f-s20-t7680,parent t7424,storagev2;PPO updates116->120.
Primary verified strict hashes/lineage,61 frozen artifacts,process/listener/approval
cleanup. t7424/t6912 preserved. No learned-play improvement or verified-clear claim.
Explicit replacement change2/2 accepted,unarchived. See
[pilot results](../reports/2026-10-21-thirty-minute-qualification-results.md).

User requested no practical step/death caps for long runs. time-budget-training1/2
now adds --time-budget-only (up to4h),nonbinding1billion/5000 schema sentinels,
time-dominant navigation and hidden-config-limit refusal. Fixed timer and emergency
guards remain. Luna90 targeted/2190 full passed,zero skips,OpenSpec46/46;primary
verified406 frozen files. New mode native qualification remains not_run. Next:
new finite experiment from t7680 with explicit game-entry/replacement authority;
no old assignment/lease resurrection. See [runner](TRAINING_SESSION.md) and
[mode evidence](../reports/2026-10-21-time-budget-training.md).

Readiness item 4 implemented offline (2026-10-21): comparable-gameplay-evaluation
3/4, unarchived. Bounded frozen-matrix/trace analyzer derives raw HP-loss lower
bounds, verified clears/deaths and exposure independently of reward. Actual initial
HP/positions/enemy states must match; missing, synthetic, assisted, mixed-control,
corrupt and faulty evidence cannot produce paired gameplay conclusions. All attempts,
unknowns/faults and denominators remain visible; no automatic learning claim/winner.
Luna/high:105 targeted/2169 full tests,zero skips;OpenSpec44/44. Primary verified396
frozen files and actual logs. t7424/t6912 unchanged; no game or training occurred.
Native comparison is not_run: normalized raw-log exporter/provenance and matched
native starts are not accepted. Next:prepare raw capture and five-minute native
qualification,then15-30min,one hour and only after acceptance a new four-hour request.
See [comparison guide](GAMEPLAY_COMPARISON.md) and
[evidence/self-review](../reports/2026-10-21-comparable-gameplay-evaluation.md).

Readiness item 3 implemented offline (2026-10-21): transactional-checkpoint-publication
3/4, unarchived. Immutable staged checkpoints, atomic latest publication, storage-v2
artifact hashes and an OS-released writer lock preserve complete parent lineage.
Fault injection, a killed writer and concurrent readers cover interruption; actual
synthetic RecurrentPPO resume verifies optimizer, normalizer and RNG restoration
before another completed update. Final runner readback recovers a publication whose
worker event was lost. No fresh-policy fallback around partial or corrupt state.
Luna/high final gate: 209 targeted / 2126 full tests, zero skips; OpenSpec 43/43;
16-step CPU synthetic smoke passed. Primary independently verified 388 frozen files
and logs. No native launch/training or real checkpoint changes; t7424/t6912 preserved.
Native acceptance is not_run. Item4 now has offline evidence above; native
comparison and stage qualification remain pending. Native stages remain separately
requested: 5 minutes, 15-30 minutes, one hour, then four hours. See
[storage guide](CHECKPOINT_STORAGE.md) and
[evidence/self-review](../reports/2026-10-21-transactional-checkpoint-publication.md).

Readiness item 2 implemented offline (2026-10-21):time-dominant-combat-navigation
3/4,unarchived. Explicit --navigation-time-dominant uses the fixed run window;
default diagnostic limits stay. Confirmed directed room/door memory routes toward
observed unexplored exits and stops exhausted/unreachable observed routes instead
of cycling;no hidden map or New Run fallback. Simulated25-transition combat resume,
normalizer separation,blocked-frontier cycles and missing-ack provenance covered.
Final gpt-6-luna/high worker:130 targeted/2101 full tests,zero skips;OpenSpec42/42.
Primary verified381 frozen files and actual logs independently. No native launch,
training,deployment or checkpoint changes;latest t7424 and t6912 preserved.
Native qualification remains not_run. Item3 now has offline evidence above;
separately declared5min native pilot remains required before longer stages. See [navigation guide](COMBAT_NAVIGATION.md) and
[evidence/self-review](../reports/2026-10-21-time-dominant-navigation.md).

Readiness item 1 implemented offline (2026-10-21): durable-training-session 4/5,
unarchived. Versioned finite Continue2 runner shares one fixed monotonic deadline
with live/training, aligns the integral approval without extending it, and records
observed combat/navigation/checkpoint/waiting phases plus exact terminal reason.
Stale telemetry is waiting; cleanup time cannot convert early_stop to completed.
Cooperative stop, owned normal close/hash-checked approval/sleep cleanup and final
status durability have behavioral coverage. Final Windows gate:2084 passed,zero
skipped;OpenSpec41/41,synthetic RL smoke passed. One initial test clock mismatch
was corrected without weakening assertions. No game/training/deployment occurred;
t7424 and t6912 preserved. Native five-minute resume/manual-stop/timer-stop
qualification remains not_run;the stopped overnight experiment stays suspended.
Item2 now has offline evidence above;native runner qualification is still pending.
See [runner guide](TRAINING_SESSION.md) and
[evidence/self-review](../reports/2026-10-21-durable-training-session.md).

Four-hour attempt STOPPED (2026-10-21);user cancelled further overnight execution.
No game,learner,supervisor,listener9528 or action approval remains. Primary verified
cleanup and default-off observer;no authorized replacement New Run was executed.
Current code is the committed tested version;unfinished navigation/replacement
sketch saved in reports/local/deferred-time-only-navigation-and-reset.patch only.

Actual continuation:161.23s outer,725 combat decisions,512 new saved steps,t7168
andlatest7d53f55f-s20-t7424,213 unsaved decisions. Conservative damage17.5HP,
two player-damage events,zero infrastructure faults/deaths/restarts. Stop reason:
cumulative navigation budget exhausted after20 room transitions;not a four-hour
completion or a training crash. Original08e0d262-s20-t6912 remains immutable.
Initial update proof(PPO108->112,20 tensors changed) still proves resumed updates,
not improved play.2048-test gate/108 targeted passed,zero skipped,OpenSpec40/40.

Active change overnight-four-hour-experiment4/5 remains unarchived;full-duration
and comparable-learning acceptance not run. No automatic resume,new worker or
scheduled monitor. Next:durable runner/deadline/status and navigation/no-progress
contracts,then supervised5min,autonomous15-30min and60min qualifications before
another4hour request. Learning/reward/observation changes are separate decisions.
See [readiness plan](../reports/2026-10-21-long-run-readiness-plan.md),
[start/early-stop evidence](../reports/2026-10-21-overnight-start.md) and
[original plan](../reports/2026-10-21-overnight-plan.md).

Combat tear audit completed (2026-10-20): combat-tear-audit4/4,unarchived.
Default-off local telemetry added without policy/reward/schema changes. First
native attempt400 decisions:diagnostic stopped before tears;retained as failed
trajectory evidence. Fixed non-scalar BitSet128 flag handling;69 targeted/2044
full tests passed,zero skipped;OpenSpec39/39. Follow-up399 decisions,64 observed
tear lifetimes/122 samples,548 lines,normal labels-cap stop.331/331 valid nearest
target lines blocked,including124 target samples closer than reported range260;HP90
unchanged. Distance alone does not explain this observed stagnation. No collision
cause/effective range or learned improvement claim. Both launches/Continue2 were
automatic,zero faults/deaths/restarts;799 decisions total,no training. Primary
verified173 frozen hashes,fingerprints,normal shutdown/approval/listener cleanup
and default-off restore. Latest stays08e0d262-s20-t6912. Next:separate bounded
obstacle-aware diagnostic baseline to verify damage/reward,then choose curriculum
or observation repair;keep it distinct from learned policy. Revival remains pending.
See [tear evidence](../reports/2026-10-20-combat-tear-audit-results.md).

Combat motion replay completed (2026-10-20): combat-motion-replay4/4,unarchived.
Offline replay matched657 native commands/656 comparable pairs;no new game or
training. When t6912 controlled,216 commands requested right;197 displaced<0.5
units and207 started beside the right boundary. Initial measured walking route
around geometry exists:17 edges to nearest enemy;all eight targets reachable on
the grid. Obstacles were present in policy inputs;absolute x clipped648/657.
This establishes captured positioning stagnation,not collision/LOS/range proof.
33 targeted tests and2028 full tests passed,zero skipped;OpenSpec38/38. Primary
verified159 frozen hashes and raw counts;models remain at08e0d262-s20-t6912.
Worker exact start/peak disk sampling missing;final size and receipt bounds retained.
Next:range/tear/projectile-blocker telemetry and comparable frozen combats before
more training or schema/reward changes. Globin/revival acceptance remains pending.
See [motion evidence](../reports/2026-10-20-combat-motion-replay.md).

Paired frozen diagnostic completed (2026-10-20): paired-frozen-combat-audit4/4,
unarchived.2011-test Windows gate passed,zero skipped;120 targeted. Retained one
failed gate(env lost) and one focus-blocked launch. Human focus assistance then
allowed Continue2/Isaac;657 decisions/six windows,129.63s,zero faults/deaths.
Exact paired replay passed;147 files and both in-memory model/normalizer hashes
unchanged;normal shutdown,approval/listener cleanup and default-off restore verified.
On657 identical inputs coarse direction proxy:t1536=0.76%,t6912=37.14%,random=21.77%.
Not hit accuracy or matched gameplay ranking. Eight visible vulnerable enemies
were exported;sampled HP stayed90,no damage/healing/credit suppression observed.
Player stayed in right-side x strip990..1090;648/657 absolute-x inputs clipped,
nearest-target distance350..597. Relative geometry remained available. Actual
revival/Globin coverage still pending6/7. Next:range/obstacle/approach diagnosis
and comparable frozen combats;training latest remains08e0d262-s20-t6912.
See [diagnostic results](../reports/2026-10-20-paired-combat-audit-results.md).

Longer conservative-v2 continuation completed (2026-10-20): explicit budget-only
artifact migration retained model/optimizer/normalizer/RNG from t1536;source roots
unchanged. New config08e0d262,target12288,at most3sessions/45min/30deaths.
Actual:one session,746.47s including startup/cleanup,12min live wall cap;three
deaths/three restarts,5597 decisions,5376 new saved steps,221 unsaved. Latest
08e0d262-s20-t6912,21 new checkpoints,PPO24→108,all20 policy tensors changed.
No next session:time stop did not meet the predeclared tenth-death repetition rule.
Zero recorded faults,16 accepted handoffs;normal shutdown/approval/listener/source
and all83 frozen hashes verified.1995 tests passed,zero skipped,OpenSpec36/36;
synthetic smoke passed. Target12288 not reached;no improved gameplay claim.
Three consecutive completed minute-scale segments had no enemy HP removed;
accepted actions varied rather than locking permanently to one command.
Next:combat stagnation/target visibility and comparable frozen evaluation;preserve
extended latest6912. See [plan](../reports/2026-10-20-extended-conservative-plan.md)
and [results](../reports/2026-10-20-extended-conservative-results.md).

Independent conservative reward baseline completed (2026-10-20): explicit fresh
development model,not a legacy resume fallback. Steam/New Run2/Isaac startup and
five natural deaths/four structured restarts completed without operator input.
1777 decisions,1536 checkpointed,241 unsaved;latest92969b7f-s20-t1536,new config
92969b7f/reward live-conservative-v2. Six checkpoints,PPO updates4→24,all20 policy
tensors changed between first/last. No improved gameplay claim. Nine accepted
handoffs,zero recorded faults;282.88s,61.4MB,normal shutdown and approval cleanup.
Primary independently verified models/normalizers/source/lineage and untouched
legacy t8960. Full gate1995 passed,zero skipped,OpenSpec36/36;synthetic smoke passed.
Revised phase journal also passed native sampling (eight NPC lifetimes,no budget
exhaustion,champion_color=-1);actual revival/champion scenario still pending6/7.
Next: ship finite session wrapper and resume this exact new t1536 lineage under a
new bounded plan;current baseline cap4096. See [plan](../reports/2026-10-20-conservative-baseline-plan.md)
and [results](../reports/2026-10-20-conservative-baseline-results.md).

Explicit post-death startup accepted (2026-10-20): post-death-new-run4/4,
unarchived. New Run requires positive fresh absence of file2 Continue and explicit
entry mode; existing/unknown state is protected. Final gate exit0:1995 tests,
zero skipped,OpenSpec36/36;63 targeted tests. Native startup exit0,25.55s,eight
guarded keys;fresh [New,2],seed JBMH Z9CS,active Isaac(type0),epoch1/frame0,
session5ce8ec25824d4b5eb791556463c55fdb. Normal shutdown,source hashes,approval
absence and unchanged t8960 independently verified. No gameplay or learning.
Primary self-review/OpenSpec verification passed. Next: revised phase/champion
audit,then explicit compatible reward lineage and bounded five-death learning.
See [New Run evidence](../reports/2026-10-20-post-death-new-run.md).
Earlier entries below retain their historical scope.

Target phase follow-up (2026-10-20): live-target-phase-audit6/7,unarchived. Automatic
file2 Continue and structured random check completed863 combat decisions/two
handoffs before the configured single natural death;runtime/wrapper exit0,119.55s.
No learning or checkpoint writes. Journal stopped after38.033s because122 passive
effects plus six NPC lifetimes exhausted128 labels. No sampled vulnerable target
was excluded from both exports,but actual revival-phase coverage remains pending.
User identified a red elite;do not equate its modifier with Globin species.
Diagnostic now excludes passive effects unless explicitly opted in,still includes
all NPC/enemy/vulnerable forms,and logs optional champion-color index locally.
Final Windows gate exit0:1984 pytest tests,zero skipped,OpenSpec35/35;20 targeted.
Primary verified hashes/normal shutdown/approval cleanup/unchanged t8960 and deployed
tested default source with both diagnostic flags false while closed;preflight passed.
Revised diagnostics native acceptance still pending. Next:explicit bounded New Run
entry after death,then a correlated revival/champion sample and explicit compatible
reward-contract lineage before learning. See
[native audit and refinement](../reports/2026-10-20-automatic-target-phase-audit.md).

Automatic local menu entry accepted (2026-10-20): local-menu-entry4/4 and
screenless-steam-launch4/4,unarchived. Start-IsaacAgent.cmd now launches via Steam,
uses bounded local menu-only scan codes,verifies fresh file2/Continue log evidence
and one bridge snapshot;no screenshots or agent desktop tools. Final gate exit0:
1977 tests,zero skipped,OpenSpec35/35,lint/format/mypy/pip clean;52 targeted tests.
One earlier native timeout exposed intro-before-menu ordering and is retained.
Final native check exit0,23.34s,seven keys;Continue2 seedF4C7 BB19,session
ed1d607a7cd44c7fa2994da2ed3a6b63,epoch1/frame16743 active. Normal shutdown,
no process/listener/approval and unchanged t8960/observer independently verified.
No learning or new-run fallback. Primary self-review/OpenSpec verification complete.
See [menu evidence](../reports/2026-10-20-local-menu-entry.md).
Next: finish correlated revival/pile membership evidence,then explicit compatible
reward-contract lineage before further training. Entries below are historical.

Repository synchronization (2026-10-20): user requested publishing accumulated
project changes and routine commit/push after verified milestones. Primary checked
the existing origin/main (no divergence), reviewed source/specification/evidence
scope and retained local logs,checkpoints and approvals outside publication.
The latest1952-test Windows gate is passing; current native limitations below
remain explicit and no change is archived by publishing this snapshot.

Screenless launcher (2026-10-20): active screenless-steam-launch3/4,unarchived.
Start-IsaacAgent.cmd launches through existing Steam options, waits for one bridge
snapshot and returns without a pause; no screenshots or desktop input. Python
launcher tests27 passed; full Windows gate1952 passed,zero skipped,OpenSpec34/34.
Source hashes independently verified. Native CMD request launched the expected
installed game process; no peer arrived before the bounded deadline,exit2,
listener released. Game intentionally left open. File2/Continue remains manual;
successful native first-snapshot readiness and fully automatic entry are unverified.
PowerShell5.1 rejected the alternate PS wrapper under its execution policy; no
policy settings changed. Test temporary output exceeded the20MiB assignment cap
(86,104,567 new temp bytes); checks passed but budget compliance failed.
See [launcher evidence](../reports/2026-10-20-screenless-steam-launch.md).

Target phase audit: offline1950 passed; native attempt captured128 random actions
before operator-assisted entry lacked the helper's required menu proof and the
worker closed normally. Native log proves Continue,file2; no correlated revival
pile observed. Cleanup and unchanged t8960 verified; diagnostic restored off.
live-target-phase-audit4/5; actual pile membership remains pending. Next: resolve
whether local menu-only key dispatch is acceptable for the requested launcher;
until clarified, no desktop input. Then finish phase evidence and explicit
compatible reward-contract lineage before further training.

Conservative live reward correction completed (2026-10-20): active change
live-reward-continuity6/6,unarchived. Absence no longer pays HP/kill bonuses;
bounded session/epoch HP floors survive software segments and rebaseline gaps.
live-conservative-v2 manifests reject legacy live resume before env creation;
t8960 remains readable and byte-identical for frozen analysis. Luna6/high final
Windows gate1937 passed,zero skipped,plus lint/format/mypy/pip/OpenSpec32/32;
16-step synthetic RL smoke passed. Separate primary self-review/verification done.
Luna native random check1200 decisions/three handoffs crossed1800-update boundary
in the same session/epoch/visit. Reappearing entity4 credited17.5HP total from20,
with no later reset/reappearance credit or kill labels. No deaths/restarts/faults.
Runtime exit0; wrapper numeric exit not retained. Native shutdown/process/listener/
approval and unchanged model/source hashes independently verified;disk353046519.
Operator observed a pile/revival enemy. Temporary empty gate exit suggests visible
phase acquisition/gating needs audit; exact phase/ID linkage unverified. Next:
bounded structured visible-target phase audit,then explicit compatible warm-start
lineage before more learning. No model reset/new training or archive. See
[implementation and native evidence](../reports/2026-10-20-live-reward-continuity.md).

Delegation expanded (2026-10-20): user authorized gpt-6-luna/high to execute
prepared offline checks, game checks and bounded training, including Steam/menu
setup and normal shutdown. AGENTS.md supersedes the earlier offline-only scope;
docs/SCRIPT_RUNNER.md records existing commands and the finite handoff contract.
Primary retains code, experiment/budget decisions and evidence acceptance. No
new runtime dispatched: reward-accounting correction remains the next prerequisite.
Documentation-only update; whitespace/link/command inventory review performed.

Reward diagnosis (2026-10-20): native derived trace marks entity45 killed at7223
then respawned at7225 in the same session/epoch/visit. Source review and synthetic
witness reproduce absence-derived remaining-HP/kill reward and renewal of HP
allowances across1800-update software truncations (5.6 versus intended2.0 cap).
Exact enemy mechanics/geometric cause remain unknown: raw snapshots/actions were
not recorded. Luna6 high ran supplied offline audit and38 tests,exit0,zero skips;
primary verified logs and before/after/current tested-file hashes. No production
fix or runtime was performed; t8960 hashes/latest unchanged. Next concrete work:
small OpenSpec reward-provenance/continuity correction with explicit compatibility
and behavioral regressions before further learning. Existing spec currently
requires disappearance-based kills and must be changed deliberately. See
[diagnosis and acceptance](../reports/2026-10-20-live-reward-diagnosis.md).

Workflow update (2026-10-20): user authorized routine offline test/script execution
by one bounded gpt-6-luna/high subagent. AGENTS.md defines scope and required primary
log/result verification; game/training and acceptance remain primary-owned.
Documentation-only change; git diff --check passed, no tests or game run needed.

Larger training experiment completed (2026-10-20): seed20 resumed t5120->t8960,
3840 new learned steps,15 verified checkpoints,PPO updates80->140; normalizer
count8966.0001. Full reload/hash/finite-weight/parent-chain/latest checks passed.
Global experiment4028 decisions (188 earlier unsaved),19m40s within30min,
two observed deaths/two restarts including startup; five-death cap not reached.
Eight fresh combat handoffs,zero resume races/observation gaps/cleanup errors.
Step budget stopped the surviving run in its first fight; no full-run or policy
improvement claim. Immediate normal shutdown,process/listener absent,exact approval
removed,disk353032593 bytes. Offline Windows gate1920 passed,zero skipped plus
lint/format/mypy/pip/OpenSpec31/31. New explicit death/navigation bounds and
accepted-release no-input settling passed tests. New accepted-release branch and
fifth-death native stop unobserved. Active bounded-combat-navigation17/18 tasks;
4.3 end-to-end post-clear checkpointed continuation remains pending. Shapes2/3/5
still user-deferred. No archive or further runtime renewal. Next: offline diagnosis
of prolonged surviving fight,then a newly budgeted experiment. Keep development
model; any later clean baseline starts in a separate lineage. See
[experiment and verification](../reports/2026-10-20-five-death-training.md).

Earlier entries below are historical and their prepared budgets are superseded.

Navigation-training attempt (2026-10-20): user deferred narrow native shapes
2/IH,3/IV,5/IIV and approved512 new steps from t5120,10 minutes,two restarts.
One Steam launch/seed20 --resume invocation reached fresh combat and21 decisions,
then stopped about0.15s after last-enemy disappearance: empty/room_clear=false,
no open ordinary exit. No complete rollout/PPO update/new checkpoint;21 unsaved,
zero checkpointed. Normal immediate closure, no process/listener, exact approval
removed, full parent identity/model/normalizer reload/latest unchanged: t5120,
80 PPO updates,count5125.0001,disk202291492. No runtime budget renewal.
Offline correction adds <=2s context-bound no-action exit settling under original
caps, including clear-flag-before-door timing, damage/pause/frozen/deadline guards.
Targeted28 passed; final Windows Check passed1902 tests,zero skips,44.92s plus
lint/format/mypy/pip/OpenSpec31/31. Separate self-review/verification passed
offline; bounded-combat-navigation12/13 tasks, new runtime4.3 pending. No Lua
deployment/model-schema change. Next: new finite post-fix training attempt from
t5120; remaining goal512 checkpointed steps, not491. Narrow shapes user-deferred
stay not_run. See [experiment/fix](../reports/2026-10-20-navigation-training-512.md).

User deferred native narrow-shape checks2/IH,3/IV,5/IIV (2026-10-20): remain
not_run, offline covered; no all-layout acceptance claim. Authorized next experiment:
resume seed20 t5120 to5632 (512 new combat steps),10 minutes,two natural death
restarts,maxfaults0,disk512MiB,gate90s. Original cumulative navigation limits
remain256commands/90pulse seconds/four transitions. Closed-game preflight/config
hash/source/full parent reload/latest passed; parent80 PPO updates,count5125.0001.
Fresh approval/Steam launch prepared, startup cap120s; runtime not yet started.
No deployment or fresh model initialization. See
[experiment](../reports/2026-10-20-navigation-training-512.md).

Native vertical1x2 check passed (2026-10-20): shape4/index98/grid15x16,room clear
with two oracle entities still listed, five initial half-hearts. Bottom-to-upper-
left slot0 route completed; three native transitions through neighbors.55
movement/release pairs, three bounded release races reconciled;15.391s wait,
zero stalls/health-change stops/faults/cleanup errors. Fresh combat readiness,
one permitted random decision then immediate normal closure, no restart/model
update. Process/listener absent, approval removed, full t5120 model/normalizer
reload/identity/latest/source match unchanged; disk202284729. No exact final-
health snapshot or harmless-entity inference. Native nine of twelve families
(1/4/6/7/8/9/10/11/12), observed exits only; remaining2/IH,3/IV,5/IIV. No code/
full-suite changes; prior1893-test gate retained, strict validation/whitespace
passed. No automatic next run/archive. See
[1x2 evidence](../reports/2026-10-20-1x2-route-check.md).

Native horizontal2x1 check passed (2026-10-20): actual shape6/index97/grid28x9,
clear/active,five initial half-hearts. Cross-room route from left side to upper-
right slot5 completed, then neighbor/LBR travel: four native transitions,
44 movement/release pairs, four bounded release races reconciled.13.218s wait,
zero combat actions/reward/restarts/stalls/faults/cleanup errors. Transition-cap
exit0 then immediate normal closure. No process/listener/approval, full t5120
model/normalizer reload/identity/latest/source match unchanged; disk202251767.
No exact final-health snapshot. Native1/6/7/8/9/10/11/12 observed routes only;
shape6 slot7 not_run, remaining native shapes2..5(IH,IV,1x2,IIV). No production/
full-suite change; previous1893-test gate retained, strict validation/whitespace
passed. No automatic next run/archive. See
[2x1 evidence](../reports/2026-10-20-2x1-route-check.md).

Native LBR check passed (2026-10-20): actual shape12/index71/grid28x16, clear/
active, six initial half-hearts. Lower slot3 route, return/second exit and onward
travel completed four transitions;45 movement/release pairs, four bounded release
races reconciled.12.594s wait, zero stalls/faults/cleanup errors. Fresh combat
readiness/one permitted random decision, normal step-limit exit0 then immediate
normal closure. No training/restart/model update. Process/listener absent, exact
approval removed, full t5120 model/normalizer reload/identity/latest/source match
unchanged; disk202224891. No final-health snapshot. Observed routes for all four
L rotations plus2x2/1x1/IIH now passed; other layouts/exits not implied. Native
remaining shapes2..6(IH,IV,1x2,IIV,2x1). No production/full-suite changes; previous
1893-test gate retained, strict validation/whitespace passed. No automatic next
run/archive. See [LBR evidence](../reports/2026-10-20-LBR-route-check.md).

Native LTL check passed (2026-10-20): new shape9/index71, measured28x16 mask,
clear/active with six initial half-hearts. Route from upper-right area to lower
slot3 completed; exit/return/second exit and neighbor travel gave four native
transitions.36 movement/release pairs, two bounded transition races reconciled,
11.156s wait; zero combat decisions/reward/restarts/stalls/faults/cleanup errors.
Transition-cap stop0 then immediate normal closure. Process/listener absent,
approval removed, full t5120 model/normalizer reload/identity/latest and source
comparison unchanged; disk202195327. No final-health snapshot or learning claim.
Native shapes1/7/8/9/10/11 observed routes only; next LBR12 and narrow2..6.
No production/full-suite changes, previous1893-test gate retained; strict
validation/whitespace passed. No extra runtime or archive. See
[LTL evidence](../reports/2026-10-20-LTL-route-check.md).

Native2x2 check passed (2026-10-20): actual shape8/index109, measured28x16 mask,
paused/clear at setup. Guarded Escape refused input; user asked to unpause and
active bridge frames followed under original deadline.64 navigation movement/
release pairs completed lower-left slot4, return and cross-room upper-right slot5,
four transitions total. Two bounded release races reconciled;42.203s wait, zero
faults/stalls/cleanup errors. Fresh combat readiness then one permitted random
combat decision, step-limit exit0 and immediate normal close. No training/restart/
model update. Process/listener absent, approval removed, full t5120 identity/
model/normalizer reload/latest and source match unchanged; disk202171859.
No final-health snapshot. Native shapes1/7/8/10/11, observed routes only; next
LTL/LBR and remaining narrow2..6. No code/full-suite changes, prior1893 tests
retained; strict validation/whitespace passed. No automatic next run or archive.
See [2x2 evidence](../reports/2026-10-20-2x2-route-check.md).

LBL secondary-exit check passed (2026-10-20): user-prepared room was again
shape11/LBL, with only secondary slot6 open.24 movement/release pairs crossed it
twice, returned once, then reached an adjacent fight on the fourth transition.
Fresh readiness accepted; one combat decision under predeclared limit, then
immediate normal game closure.8.5s wait, three bounded release races reconciled,
zero faults/cleanup errors/restarts/model updates. No exact final-health readback;
initial three half-hearts. Process/listener absent, approval removed, full t5120
identity/model/normalizer reload/latest/source comparison unchanged, disk202134072.
No code changes/full-suite rerun; prior1893-test gate retained; strict validation/
whitespace passed. Native shapes1/7/10/11, LBL upper1/secondary6 observed only.
Next:2x2 or LTL/LBR, then other unobserved narrow shapes; no automatic next run.
See [secondary-exit evidence](../reports/2026-10-20-LBL-secondary-exit-check.md).

Cleared LBL check passed (2026-10-20): prior in-process action authority was absent,
so normal close/Steam relaunch, fresh approval and user file2/Continue completed
within63s startup cap. Actual shape11/LBL, measured28x16 mask, clear, four initial
half-hearts.46 movement/release pairs, four native transitions: upper exit from
LBL, neighboring cleared ordinary rooms, return to LBL. Three release races
reconciled;14.015s wait, zero combat decisions/reward/restarts/faults/cleanup
errors. Stopped at transition cap, immediate normal closure before evidence
processing, process/listener absent. Exact approval removed, full t5120 model/
normalizer reload/identity/latest unchanged, source match, disk202115498. No final
health snapshot; no exact final-health claim. Native shapes1/7/10/11, only observed
exits;2x2/LTL/LBR/other narrow shapes still not_run. No production changes/full-suite
rerun, previous1893 tests retained; strict validation/whitespace passed. Next:
targeted remaining native geometry, no automatic retry or archive. See
[cleared-L evidence](../reports/2026-10-20-cleared-L-check.md).

Large-layout check (2026-10-20): actual user-prepared LTR/shape10, v2 grid28x16,
index71. Eleven navigation action/release pairs crossed upper slot1; one release
transition race safely reconciled. Fresh combat readiness/resume passed;64 random
combat decisions then normal step-limit exit0, no runtime faults/cleanup errors
or model updates. Recovery limitation: after disconnect the character died in
the still-active battle; later successful Escape capture showed main menu with
Continue disabled. No living-player pause/recovery claim; post-probe timed out.
Approval removed by exact hash, no listener, full t5120 reload/identity/latest
unchanged, disk202088043. Game left at menu. Native coverage now shapes1/7/10,
shape10 upper exit only; other L rotations/2x2 remain not_run. No code changes or
full-suite rerun; previous1893 tests retained. Next: another large geometry with
immediate normal close after any combat-ending test, before evidence processing.
See [large-layout evidence](../reports/2026-10-20-large-layout-check.md).

Navigation-to-combat acceptance passed (2026-10-20): user prepared scenario;
one bounded random-policy test traversed three doors to fresh combat, accepted
context-bound readiness and resumed. After one natural death restart, a fourth
transition reached a second fight with a new readiness token/epoch.503 combat
decisions, two deaths, no room clears, no PPO/model update. Final90-second gate
wait stopped within three-minute budget; zero faults/cleanup errors. Game closed
normally, process/listener absent, approval absent/cached authority gone. Full
t5120 identity/model/normalizer reload/latest and source match passed unchanged;
disk202076442 bytes. OpenSpec bounded-combat-navigation task2.2 satisfied,10/10
tasks; separate self-review/verification passed for representative acceptance.
Prior1893-test/zero-skip gate retained; strict validation/whitespace passed now,
no production changes or full-suite rerun. Native shapes1/7 only; remaining
2x2/L/narrow families still not_run. No archive/extra runtime/training started.
Next: targeted native layout checks; further training needs its own experiment.
See [handoff evidence](../reports/2026-10-20-combat-handoff-check.md).

Fresh-process door check completed (2026-10-20): user Continue, one random-policy
invocation, successful v2 handshake. Four real transitions,37 accepted movement
pulses including six two-frame corrections;35 accepted releases/two transition
rejections safely reconciled. Long narrow obstacle route and far door crossed;
no repeat of prior stationary stall. Stopped at four-transition cap after11.437s,
zero combat decisions/readiness/updates, zero cleanup errors. Shape1/7 native
coverage only; task2.2 still open. Escape focus refused without input; user asked
to pause, not confirmed. Post-probe alive/active index82/shape7 at(1080,280), four
red half-hearts unchanged. Exact approval removed, no listener, full t5120 reload/
identity/latest unchanged, disk202044690. No new production changes or full-suite
rerun; previous1893-test result retained. Next: a separately budgeted traversal
to fresh combat; no manual room repositioning required. See
[fresh-process results](../reports/2026-10-20-fresh-door-check.md).

Fresh-process check prepared (2026-10-20): user launched PID35824, v1.9.7.17;
latest log confirms file2 and menu capture shows Continue selected. Fresh finite
approval prepared before attach; full t5120 reload/identity/latest and observer
source comparison passed. Guarded menu Enter refused focus, no input sent.
Awaiting user Continue; production runtime not started, no gameplay commands or
listener. Approval expires after15 minutes, no automatic renewal. Budget: one
random512-step/three-minute test, gate90s, maxfaults0/restart1, disk512MiB;
navigation256commands/90pulse seconds/four transitions. See
[fresh-process evidence](../reports/2026-10-20-fresh-door-check.md).

User closed Isaac after the failed attach (2026-10-20). Process absence and
`Isaac has shut down successfully` / `Observer unloaded` log entries verified;
temporary authorization remains absent. The prior process's cached lease is no
longer active. No relaunch or new runtime budget started in this closure check.
Next action remains a fresh bounded Steam launch with approval present, file2/
Continue and corrected door-crossing/combat handoff verification.

Door-correction attach (2026-10-20): failed during handshake, CLI exit2; zero
gameplay commands or model updates. Lua reports Too many capabilities. Source
inspection supports expired authorization cached in the surviving game process:
replacement approval files are not reloaded. Initial probe success does not prove
the new lease was loaded. Next finite check requires normal close/Steam relaunch
with approval present, file2/Continue, then corrected crossing/combat handoff.
No retry or authority renewal. Visible pause confirmed, exact approval removed,
no listener, full t5120 identity/model/normalizer/latest unchanged; disk202020838.
No production changes; prior1893-test gate not rerun for documentation. Runtime
task2.2/native per-shape coverage remain open. See
[door-correction evidence](../reports/2026-10-20-door-correction-check.md).

Settling/navigation recheck (2026-10-20): one user-requested finite test crossed
two real doors, index81 -> 80 -> 81, using production v2 pathfinding. User assisted
room entry after a guarded menu focus refusal. 36 movement/release pairs, all
accepted releases, unchanged four half-hearts, 7.072 pulse seconds. Far-door
approach stalled on ineffective one-frame corrections; stationary guard stopped
after 9.891 seconds, zero combat decisions/readiness and zero cleanup errors.
Offline fix sets navigation leases to 2..6 frames and continues outward inside
the observed open-door corridor instead of recentering backwards; no blocked-cell
fallback or weaker stall limit. Added reference/ack/position/shape logs. Full final
Windows gate passed 1893 tests, zero skips, lint/format/mypy/pip and OpenSpec31/31;
separate self-review/verification passed offline. Runtime acceptance remains 9/10
tasks: corrected next-combat handoff not verified. Game left open on verified
pause, exact approval removed, no listener, full t5120 identity/reload unchanged;
installed/source byte comparison passed without deployment. Next: a new finite
attach from this paused doorway and verify alignment, crossing and fresh combat.
No extra run or renewal under this completed budget. See
[settling evidence](../reports/2026-10-20-layout-settling-check.md).

All-layout navigation extension (2026-10-20): implemented v2 measured walkability
and four-neighbor pathfinding for all twelve room shapes, including narrow/long,
2x2 and all rotated L rooms, using all eight measured door slots. Routes avoid
blocked/hazard/void cells, replan each pulse and remain outside combat learning.
Legacy v1/default peers stay compatible. Finite navigation limits now 256 commands,
90 pulse seconds/four transitions, original run/gate caps retained. Final Windows
gate passed 1884 tests, zero skips, lint/format/mypy/pip and strict OpenSpec 31/31;
all twelve Lua/topology/steering families tested offline. One real Steam/file-2/
Continue test negotiated v2 and captured shape-7 28x9 grid (72 safe cells), but
first pulse lacked timely frame progress; zero transitions/combats. Read-only
native-mask replay finds a 30-cell obstacle detour to the far door. Added offline
two-frame-advance settling guard and accurate pulse-timeout labeling afterward;
these are not rerun in Isaac. Game closed normally, exact approval removed,
listener/process absent, full t5120 identity/reload and source/installed preflight
passed. 9/10 OpenSpec tasks; runtime 2.2 and native per-shape coverage remain open.
Next: bounded post-settling narrow-room traversal and fresh combat handoff. No
automatic retry, checkpoint update or archive. See
[all-layout evidence/coverage](../reports/2026-10-20-navigation-all-layouts.md).

1x1 navigation check (2026-10-20): user supplied active clear ordinary room 80,
shape 1. Nine accepted bounded pulses crossed its right door. Separate read-only
post-stop data confirms room 81/visit 2 versus initial visit 1, unchanged four
half-hearts. The manager stopped early because release rejection arrived before
the new-room snapshot; no combat readiness/decisions followed. Added bounded
<=0.5s no-action reconciliation requiring same session/epoch, later visit and
unchanged health, preserving original budgets. Final full Windows gate passed
1821 tests, zero skips, lint/format/mypy/pip and strict OpenSpec 31/31; separate
self-review/OpenSpec verification passed offline. 5/6 tasks: post-fix runtime
acceptance still pending. Destination shape 7 remains unsupported. Normal game
closure, exact approval removal, process/listener absence and full unchanged
t5120 reload/identity passed; pause was not confirmed because focus guard refused
input. No second gameplay run or renewal. Next: narrow geometry extension and a
bounded post-fix transition-to-combat check. See
[1x1 evidence](../reports/2026-10-20-navigation-1x1-check.md).

Manual navigation attach (2026-10-20): real combat_navigation_v1 telemetry and
automatic fresh readiness accepted. Random controller ran 483 combat decisions,
then the segment ended empty. Current ordinary room is shape 7 (narrow geometry),
outside the implemented 1x1 scope: second reset stopped explicitly with zero
navigation actions/transitions, no fault/cleanup errors, no training update.
OpenSpec bounded-combat-navigation remains 5/6; task 2.2 still needs an actual
transition and subsequent combat. Final pause attempts refused focus without
injecting input, so game was closed normally; process/listener absent, exact
approval removed, full t5120 identity/reload and installed/source preflight passed.
Next: explicitly scope/test narrow-room support, or use a supported 1x1 scenario
in a later bounded check. No extra invocation/budget renewal. See
[manual navigation evidence](../reports/2026-10-20-manual-navigation-check.md).

Bounded combat navigation (2026-10-20): production opt-in `--combat-gate
--auto-navigate` now negotiates separate door management telemetry, routes through
open ordinary-room exits inside reset, and uses existing fresh readiness checks.
No navigation samples/reward enter learning. Ordinary 1x1 rooms only; fixed
command/time/transition/stall limits, no obstacle pathfinding. Final Windows full
gate passed 1819 tests, zero skips, lint/format/mypy/pip and strict OpenSpec 31/31.
Separate self-review/OpenSpec verification completed; 5/6 tasks, runtime acceptance
still open. After closed-game backup/deployment, one Steam launch overlapped Cloud
timeouts; the 60-second attach wait expired before Isaac appeared. Zero gameplay
or training ran. Late-starting game closed normally; exact approval removed,
process/listener absent, full t5120 identity/reload and installed/source preflight
passed. Next: a fresh bounded attach test after normal Steam startup, demonstrating
actual navigation and subsequent combat readiness. No archive or automatic retry.
See [evidence](../reports/2026-10-20-bounded-combat-navigation.md) and
[usage/limits](COMBAT_NAVIGATION.md).

Manual paused-combat continuation (2026-10-20): user prepared file 2/combat/pause.
Bridge paused/alive verification and parent reload passed; manager unpaused and
fresh combat readiness was accepted. One bounded learner invocation completed
256 new combat decisions in 29.594 learner seconds, saved all 256 with zero
unsaved, and advanced latest t4864 -> t5120. Full child model/normalizer reload,
parent lineage/identity, finite changed policy weights and PPO update counter
76 -> 80 passed. No terminal outcome, navigation or restart was needed/claimed.
Zero gate cleanup errors; exact temporary approval removed, listener absent.
User-launched game remains open on verified pause with three hearts. No further
training is running. Full offline suite was not rerun for this runtime/report
update; production runner acceptance and episode-lifecycle remain open. Next:
bounded next-room planning and separate evaluation of gameplay quality. See
[manual continuation evidence](../reports/2026-10-20-manual-paused-training.md).

Same-client assisted rollout (2026-10-19): one bounded attempt reached combat
through nine structured-bridge navigation pulses, collected 94 policy decisions,
then observed natural death and one successful bounded restart. Eleven further
pulses reached an empty room in epoch 2. A third room plan was not supplied before
the original 90-second handoff cap; planning latency is part of the remaining
runner gap. No false readiness, cleanup errors, PPO update or new checkpoint:
94/256 samples were unsaved, latest t4864 unchanged. Five private behavioral tests
passed; full suite was not rerun for this private experiment/report update. Agent
pause-menu recovery, normal closure, exact approval removal, full parent reload/
identity and installed/source preflight passed. Next: bounded prompt room planning
across empty rooms in the learner connection, with management excluded from
learning. Production runner acceptance remains open; no extra run or budget
renewal occurred. See [assisted rollout evidence](../reports/2026-10-19-assisted-rollout-attempt.md).

Paused-handoff v2 (2026-10-19): the corrected pinned PowerShell runtime passed.
One Steam/file-2/Continue route resumed combat; no navigation actions were needed.
Bridge paused/alive same-room evidence and pause-menu capture preceded learner
setup. The local manager unpaused, waited for fresh same-context combat, and the
gate accepted readiness and resumed the t4864 policy. It collected 104 combat
decisions before an empty-room end, then observed cleared. Second handoff expired
at its original minute cap with no false readiness. Zero faults/cleanup errors,
but no full 256-sample rollout: 104 unsaved, zero checkpointed, no PPO update or
new checkpoint. Normal close, exact approval removal, unchanged parent identity/
reload and post-close preflight passed. The pause/setup/resume gap is verified
for one encounter; next is bounded navigation between encounters inside the
learner's existing connection so a rollout can span several fights. No additional
run or renewed approval under this completed budget. See
[v2 evidence](../reports/2026-10-19-paused-handoff-v2.md).

Paused-handoff attempt (2026-10-19): after the prior natural death, agent selected
file 2/New Run/Isaac/Normal. Two bridge movement commands reached room visit 1;
fresh bridge data classified combat at frame 393. Automatic pause failed before
key injection because the private helper selected Windows PowerShell 5, whose
ExecutionPolicy refused the script. Final bridge release was accepted. No learner,
readiness acknowledgment or training invocation followed this infrastructure
failure. Normal closure, exact approval removal, unchanged t4864 identity/reload
and installed/source preflight passed. No ExecutionPolicy/setting bypass or change.
Offline fix: both private helpers now require the existing pinned PowerShell 7.6.5
runtime (RemoteSigned) and a fresh per-attempt directory; syntax checks pass, but
the corrected pause/resume path is not yet runtime-verified. Next is that bounded
pause/alive/room check, then coordinated unpause and fresh combat readiness.
See [attempt evidence](../reports/2026-10-19-paused-training-handoff.md).

Bridge navigation attempt (2026-10-19, new user request): the agent repeated the
Steam/file-2/Continue route and issued five bounded down/no-shoot commands through
LiveClient. Observed positions and room visit 0 -> 1 establish movement and one
room transition; the destination screenshot contains enemies. Navigation stopped
on a paused transition snapshot; final release was rejected, then the navigation
client disconnected (no neutral acknowledgement claimed). The one-heart character
subsequently died during the gap before learner readiness; Game Over and a native
kill log were observed. A single t4864 resume invocation connected but its gate
stayed paused and expired at 60.016 seconds: zero decisions/updates/new checkpoints,
no readiness ack, no restart dispatch, no cleanup error. Normal game exit, exact
temporary approval removal, parent identity/reload and post-close preflight passed.
Next: close the handoff gap with prompt verified menu pause, learner setup, and
coordinated unpause/fresh combat readiness; no automatic extra run is authorized
by this completed budget. See
[navigation evidence](../reports/2026-10-19-bridge-navigation-attempt.md).

Held menu-input attempt (2026-10-19): a private foreground-guarded scan-code
helper with 300 ms holds successfully passed startup, visibly selected FILE 2,
and used Continue. One Steam launch retained --luadebug; observer/source hashes
matched. Read-only attach returned 10 active initial-load snapshots (same frame,
not advancing-frame proof). One bounded live train invocation resumed t4864 and
negotiated live_loop_v1, but the gate observed a cleared room and accepted no
readiness: zero combat decisions, zero PPO updates and no new checkpoint. Its
original one-minute handoff cap expired cleanly (1239 wait snapshots, no cleanup
errors); the 256-new-step target was not achieved. A final held Escape opened
the pause menu; the agent then closed Isaac normally, verified process absence,
removed only its exact temporary approval and reloaded unchanged t4864 artifacts.
The menu blocker is resolved for this agent-inspected route; a general unattended
runner is still absent. Next: bounded structured-bridge navigation to combat and
fresh readiness outside the rollout. No renewed approval or second training run.
See [runtime evidence](../reports/2026-10-19-held-menu-input-check.md).

Agent-driven startup readiness (2026-10-19): checkpoint t4864 and saved
normalizer reload/hash checks pass; installed/source observer preflight passes.
One Steam launch produced Isaac v1.9.7.17 with effective --luadebug and observer
0.5.0-dev loaded; Computer Use window capture works. Ordinary menu inputs did
not leave Press Start, so automatic file-2/Continue selection is NOT verified.
One read-only listener expired at its 90-second accept deadline (zero snapshots,
no active run); this is not evidence of a broken in-run bridge. Alt+F4 closed
the title-screen game normally; process absence, port cleanup and post-close
preflight passed. No training, approval, gameplay action, restart or deployment.
Model/normalizer hashes and latest t4864 remain unchanged. Next: implement and
verify bounded menu input and state confirmation before claiming unattended
startup; no dedicated session/menu runner exists yet. See
[readiness evidence](../reports/2026-10-19-autonomous-start-readiness.md).

Coverage-aware outcomes (2026-10-19): offline task 3.15 accepted after primary
Windows review and one correction. Missing terminal coverage remains unknown;
coverage gaps cannot be repaired by later intervals. Summary death/clear facts
are tri-state, unresolved clears/limits truncate as `unknown`, and evaluation
report v2 counts unknown separately from faults and known outcomes. LiveBackend
keeps its existing approximate events without an exhaustive coverage claim.
Review found that a terminal initial result still allowed actions; start now
faults and releases before any action, with six reproduced regressions fixed.
Windows Check.ps1 passed 1802 tests, zero skips, Ruff, format, mypy (44 sources),
pip consistency and strict OpenSpec 30/30. The change remains open (20/27 tasks).
No game launch, deployment, approval, real training or Git commit was performed.
See [review and verification](../reports/2026-10-19-terminal-outcome-coverage.md).
Next: establish the remaining native event semantics, attach baseline, delivery
and consumed-update/endpoint evidence before implementing tasks 3.6/3.8. Passive
callback facts alone cannot close that gate. No successor executor is assigned.
Earlier statuses below are historical where they conflict with this entry.
The overlapping Windows review was resolved by waiting for the frozen handoff
at 2026-10-19T19:15:53Z and rerunning the full gate afterwards: 1802 passed in
44.22 seconds with all nine implementation/test/spec/design hashes unchanged.
The Mac-owned ready_for_review status remains historical handoff evidence;
Windows acceptance is recorded here and in the task and final report.

Firing cadence diagnostics (2026-10-19): offline implementation and one bounded
real safe-room comparison accepted. The default-off trace adds bounded
cooldown/native-tear facts and sparse once-per-frame sampling; a bounded private
log parser summarizes records without claiming firing rate or causality. The
single 30-second/16-command comparison recorded native tears every 12 game frames
in both the three-frame and six-frame phases, with `FireDelay=10` on tear events.
This does not establish a maximum rate or causal effect. The user confirmed
manual control and normal exit; the temporary approval was removed and the
default-off build restored. Task 4 is complete. Strict validation passed 31/31
before archive and 30/30 after; the change is archived at
`../openspec/changes/archive/2026-10-19-firing-cadence-diagnostics`. See
[implementation evidence](../reports/2026-10-19-firing-cadence-diagnostics.md),
[parser evidence](../reports/2026-10-19-firing-trace-parser.md),
[runtime evidence](../reports/2026-10-19-firing-cadence-runtime.md), and the
[diagnostic protocol](FIRING_CADENCE_DIAGNOSTICS.md).

Offline shooting analysis (2026-10-19): 117/512 commands selected no shooting;
509 within-combat release/reissue gaps had median 17 ms/p95 51 ms. One 902 ms
(27 game-frame) gap occurred at the first 256-sample learner boundary. The later
single cadence trace adds descriptive cooldown/tear observations but still does
not establish maximum-rate loss. No stats or expiry changed. See
reports/2026-10-19-shooting-duty-cycle-analysis.md and the runtime evidence above.

Passive oracle callback probe (2026-10-19): one user-directed read-only attach on
0.5.0-dev recorded actual damage, later-frame HP, NPC death/kill/removal,
clean-award and room callbacks during normal play. The 1024-record cap stopped
diagnostics after 109.861 seconds; player death/revival, floor and game-end
semantics were not observed. This is candidate callback evidence only, not
OracleEvent delivery or an outcome barrier. Episode-lifecycle tasks 3.6 and 3.8
remain open; no training or control was run. See
reports/2026-10-19-oracle-probe-live-runtime.md.

Passive floor-progression follow-up (2026-10-19): one read-only attach collected
585 advancing snapshots across 10 room visit IDs and 1,024 contiguous native
diagnostic records, stopping at the existing count cap after 99.511 seconds.
Records included damage, NPC initialization/HP/death, entity kill/removal,
clean-award, and room callbacks. The operator reported defeating a boss and
reaching the next floor; the observer does not identify bosses, floors, or save
slots, so that remains operator-reported. These raw callbacks do not establish
OracleEvent delivery, identity/order, death/revival, terminal outcome, or an
episode barrier. Tasks 3.6 and 3.8 remain open; no input or training was run.
Windows `Check.ps1` passed 1,248 tests with 14 optional Lua-runtime skips;
OpenSpec strict passed 30/30. See
reports/2026-10-19-oracle-probe-floor-runtime.md.

Current continuation result (2026-10-19): approved v2 completed all 512 new
combat samples, two real PPO updates t4352 -> t4608 -> t4864, zero unsaved steps.
One natural-death restart, three fresh readiness handoffs, no logged faults or
cleanup errors. Native actions/releases 512/512, 127 tears. Parent hashes and
both child model/normalizer reload pass. Operator confirmed working controls/no
intervention and normal exit; exact temporary approval removed after absence.
No gameplay improvement claim. Report: reports/2026-10-19-gated-training-continuation-v2.md.
Next: offline shooting duty-cycle inspection, then separate bounded diagnostic
or frozen evaluation decision; no automatic additional training/approval.
Historical results below retain the earlier partial target and blockers.

Current runtime result (2026-10-19): approved five-minute gated recheck collected
266 combat decisions; one completed real PPO update saved t4096 -> t4352, with
10 unsaved samples. Minimum pipeline success passes; 512-new-step target PARTIAL.
Three fresh handoffs, one natural-death restart into epoch 2, then second death
with restart budget exhausted. Neutral fourth handoff expired before global cap;
no logged infrastructure faults, cleanup errors or resumed stale readiness.
Native evidence: 266 accepted actions/releases and 69 tears. Child model and
normalizer reload passed; all parent hashes unchanged. Operator confirmed control
and no combat intervention, then exited; exact temporary approval removed after
process absence. Default-off mod unchanged. No gameplay improvement claim.
See reports/2026-10-19-gated-training-recheck.md. Next is a separate finite
experiment decision from t4352; no automatic extension. Historical preparation
and blocked attempts below do not override this result.

Current result (2026-10-19): primary Windows implementation of windows-gate-ipc
passes offline acceptance. Windows Check.ps1: 1451 passed, zero skips/xfails,
Ruff/100 formatted files, mypy 42 sources, pip consistency, OpenSpec strict 30/30.
Bounded sharing recovery (250 ms/26 attempts, clipped to original deadlines),
atomic publication and original-error/stop cleanup now pass real concurrency
and full Lua/socket/gate/CPU learner tests. Delivered async-regression coverage
is accepted after this primary remediation. Executor writes are closed and
monitor paused. No real game, approvals, model/config/reward changes or training.
Draft five-minute/512-new-step experiment remains NOT AUTHORIZED / NOT RUN;
separate budget/current-parent/current-slot readiness is the next runtime step.
Original double-start cause remains unknown. See reports/2026-10-19-windows-gate-ipc.md.
All earlier blocked/assignment notes below are historical.

Feedback-1 check (2026-10-19): executor is needs_input for bounded Windows IPC
production scope. Coupled Lua/socket/gate/CPU learner coverage is now present,
with direct learner-call instrumentation. Windows new-file rerun: 31 passed,
2 failed, 1 xfailed (12.00 s); loopback and coupled learner both fail on the
same request.json WinError 5 race. Xfail is documented as unresolved, not passed.
No acceptance, commit/push, game work or approval. Monitor stays paused; existing
executor assignment cannot edit production IPC. See the feedback-1 follow-up
in reports/2026-10-19-async-restart-training-primary-review.md.

Latest review (2026-10-19): async-restart-training-regression is NOT accepted.
Fresh matching report reviewed and monitor paused. Windows Check.ps1 reports
1431 passed/1 failed, zero skips; strict OpenSpec 29/29. Loopback gate test
exposes WinError 5 replacing request.json during a concurrent operator read;
isolated production _write_atomic reproduction confirms the Windows sharing
race. Cleanup can encounter the same write error. Also, the learner uses a
scripted AsyncWorld rather than the assigned complete Lua/socket/gate chain.
Feedback 1 in subagent.md requests explicit blocker evidence and missing coupled
coverage without hiding concurrency or changing production outside scope.
No commit/push/acceptance or real game/approval/training. A production IPC remedy
and any runtime follow-up need a separate primary decision. See
reports/2026-10-19-async-restart-training-primary-review.md.

Current offline assignment (2026-10-19): user requested one larger sequential
task, async-restart-training-regression-20261019-01 in subagent.md. Stages cover
the real asynchronous callback order, failure/deadline/identity regressions,
production-Lua-to-Python gated synthetic learning and a NOT AUTHORIZED draft
512-new-step runtime recheck. Tests/docs only; no production fixes or real game
work. Old executor status is stale until its task ID matches. The primary has
not launched an executor or resumed monitoring; user launches it manually.
Existing game build is default-off, no temporary approval installed. Primary
review/Windows gates required before acceptance or a separate live decision.

Current runtime result (2026-10-19): diagnostic death/restart capture PASSED.
Fresh operator-requested invocation completed 46 native actions/12 tears/46
releases, actual death, one dispatch, preserved approval and epoch-2 live
reconnect. Then two minutes neutral wait ended at the original handoff cap;
zero faults, no extra start/actions. Operator confirmed no input/menu activity,
working control and full normal exit. Default-off source restored, preflight
passed, temporary approval removed. Tasks 3.1-3.3 complete; unarchived pending
final archive review. Prior paused/cleared attempts retained. Original unexplained
two-start failure was NOT reproduced or fixed; no further training authorized
by this success. See reports/2026-10-19-restart-authority-runtime.md.
All preparation/earlier result notes below are historical.

Second diagnostic attempt preparation (2026-10-19): user requested another enemy
room to exercise death/restart. Closed-game source preflight, backups, flag-only
deployment and staged readback passed. Random seed 28, 2048 decisions/three
minutes, one-minute waits, max_restarts=1; deliberate ten-minute approval.
Awaiting manual file-2 paused-room readiness; no connection/actions. Installed
diagnostics temporarily ON; cleanup/restoration required after this invocation.
No kill command, scripted damage, health edit or forced reset is planned.

Latest runtime result (2026-10-19): bounded random diagnostic trial completed
82 native actions, 20 tears and 82 releases; room cleared after the conservative
empty gate boundary. No death/restart occurred. The one-minute handoff cap
stopped Python, with no additional actions. Operator confirmed working manual
control/no intervention and full normal exit. Native normal-exit records show
actual approval_drop and auth=none, but prior restart cause remains UNKNOWN.
Default-off repository files restored and exact source preflight passed;
temporary capture approval removed. Tasks 3.1/3.3 complete; 3.2 remains blocked,
change unarchived. No training/model change or automatic repeat. See
reports/2026-10-19-restart-authority-runtime.md. Preparation notes below are historical.

Runtime preparation (2026-10-19): operator confirmed full exit; two closed-game
guards, private backups, diagnostic flag-only installation and staged preflight
passed. One ten-minute approval expires 06:00:35Z (08:00:35 CEST), max_restarts=1.
Plan: random seed 27, at most 2048 decisions/three minutes, one-minute gate waits,
zero faults, no training. Awaiting manual file-2 launch and paused combat-room
readiness. No connection/actions yet. Task 3.1 complete; 3.2-3.3 remain open.
The installed lifecycle flag is temporarily ON; restore reviewed default-off
source only after the operator exits normally. See
docs/EXPERIMENT_RESTART_DIAGNOSTICS_V1.md and
reports/2026-10-19-restart-authority-runtime.md.

Current result (2026-10-19): restart-authority-diagnostics is accepted OFFLINE
after feedback 1. Windows Check.ps1 passed 1401 tests, zero skips, Ruff/98
formatted files, mypy 42 sources, pip consistency and OpenSpec strict 29/29.
Portable full-message comparisons retain types/order/values; the delayed second
exit after live rearm records live=1, awaiting=na and the actual approval drop.
Diagnostics ship disabled, with unchanged authority/restart guards. Executor
writes are closed. Runtime tasks 3.1-3.3 remain unfinished and unarchived; actual
engine cause is unknown. No game connection, deployment or approval change
occurred in review. Next: a separately budgeted operator-present capture after
closed-game preparation. See reports/2026-10-19-restart-authority-primary-review.md.

Historical first-review and preparation notes follow; the result above supersedes them.

Latest primary review (2026-10-19): restart-authority-diagnostics is NOT accepted.
Windows Check.ps1: 1388 passed, 10 new parity tests failed due to raw JSON object
field ordering across Lua instances; parsed semantic comparisons pass 10/10.
Strict OpenSpec validation passes 29/29. Feedback 1 in subagent.md requests
portable full-message comparisons, deterministic clocks and a delayed second
exit after live reconnect. Same bounded executor task; no new runtime authority.
Task 2.1 and runtime section 3 remain unchecked; no commit/push or archive of
the implementation. See reports/2026-10-19-restart-authority-primary-review.md.

Updated: 2026-10-18. All project artifacts are English.

User-requested offline assignment: restart-authority-diagnostics-20261018-01 is
written in subagent.md for one manually launched executor. Scope is default-off
Lua diagnostics, callback-order/failure/parity tests, documentation and evidence.
No executor has been launched by the primary; old agent-status.json is stale
until its task ID matches. No game work, monitoring or approval changes. Primary
review and Windows gates are required before accepting implementation.

Active next change: restart-authority-diagnostics, planning complete and strict
change validation passed. No implementation or deployment yet. Source review
confirmed that the restart stub models only one synchronous exit/start pair;
additional callbacks and authority invalidation ordering need explicit tests.
The plan preserves normal-exit invalidation, original expiry and restart limits.
Next: apply the bounded diagnostic change, then review offline before scheduling
another real-game capture. No executor assignment, monitor or game connection
was started. See reports/2026-10-18-restart-authority-investigation.md and
openspec/changes/restart-authority-diagnostics/.
Windows Check.ps1 passed on this planning revision: 1362 tests, zero skips,
Ruff/format, mypy and pip consistency; OpenSpec strict validation 29/29.

First real gated-training experiment failed before a completed update: 12 combat
steps, death, automatic restart, then live capability refusal during operator
wait. The two-minute handoff cap stopped safely; 12 unsaved samples were lost,
zero new checkpoints, latest t4096 and its hash unchanged. Operator confirmed
manual control works and explicitly denied menu/New Run/Continue after death.
The native log shows two new starts but one bridge restart dispatch; root cause
is UNKNOWN. Do not blame manual input or renew/reload authority as a workaround.
Private logs are preserved. Next: narrow offline lifecycle/authority diagnostics
before another training run. See reports/2026-10-18-combat-gated-training.md.

Historical preparation (the failed attempt above supersedes this):
operator-approved combat-gated-continuation-v1 resumes t4096
to at most t6144 (2048 NEW samples), ten-minute training cap including waits,
two-minute handoffs and zero faults. User confirmed full game exit to load a
deliberate new bounded approval. At that preparation point no training had started. See
docs/EXPERIMENT_COMBAT_GATE_V1.md and reports/2026-10-18-combat-gated-training.md.

Combat gate real acceptance passed: final remaining enemy defeated in the seed-25
bounded trial. One invocation recorded timeout handoff, a fresh second readiness,
91 further combat steps, empty-room release then clear flag, and no further
actions through the original global deadline. Total 667 decisions, 170 tears,
three handoffs/two accepted acknowledgments, zero faults; operator confirmed
room clear and manual control. No training. Task 5.2 is complete for the narrow
gate; real gated PPO updates and learning quality remain unverified. See final
acceptance in reports/2026-10-18-combat-gate-runtime.md. All prior attempts retained.

The completed narrow change is archived as 2026-10-18-combat-experience-gate-v1
with baseline spec combat-experience-gate. Next work is a separately budgeted
gated learning experiment with operator navigation; no additional run is active.

Latest gate check (seed 24): 512 accepted random actions, 129 tears, three initial
enemies, two kill estimates/8 HP damage; no clear before the decision cap. Paused
readiness/handoff start and cleanup passed again; operator confirmed no manual
input during combat and responsive control afterward. No training. Post-clear
handoff/new readiness remains unverified, task 5.2 open and unarchived. See the
fourth-attempt runtime evidence; original authority was not renewed.

Latest real combat-gate slice passed: paused-room readiness accepted within about
0.117 s after unpause; 256 automatic combat decisions, 82 tears, no faults,
final expiry release and operator-confirmed manual control. Waiting consumed
751 snapshots and zero combat steps. No training. The room had ten enemies and
did not clear within the cap, so post-battle handoff/new readiness is still
unverified; task 5.2 remains unfinished and unarchived. Next: small 1–3-enemy room
staged paused under a new explicit bounded trial. See the third-attempt section
of reports/2026-10-18-combat-gate-runtime.md. Earlier failed attempts are retained.

Combat-gate second attempt was refused at hello before control: actual Lua
reported Too many capabilities and Python peer closure. The disk approval still
had 440 seconds, but the observed manual new-run lifecycle is consistent with
in-memory authorization cleared on normal run exit. Full normal process restart
is requested; no automatic retry, authority renewal, mod change or action was
performed. Task 5.2 remains open. See the second-attempt runtime report.

First real combat-gate attempt ended at its three-minute operator-wait cap:
zero accepted acknowledgments/actions, zero combat samples and reward. Waiting
in the empty room and refusing implicit takeover passed. The operator reached
combat, but primary output-poll delay preceded death/restart; stale readiness
was refused. Combat acceptance/after-battle handoff remain unverified, task 5.2
open, no archive or automatic retry. See
reports/2026-10-18-combat-gate-runtime.md. Next attempt should stage a paused
enemy room and avoid long blocking polls during readiness exchange.

Latest combat-gate outcome: feedback 1 accepted offline after primary Windows
review. Both original defects are fixed; Check.ps1 passes 1362 tests, zero skips,
strict OpenSpec 28/28. Eligibility veto prevents further commands after combat
is lost; handoff/global deadlines propagate through resume/reconnect and stale
readiness is rejected. Valid short-fight rollout/checkpoint tests pass. Executor
writes are closed and temporary one-minute monitoring is paused. No real gate
test occurred; task 5.2 remains open and the change is unarchived. Next is a
separate bounded operator-present runtime check, not more automatic training.
See reports/2026-10-18-combat-gate-primary-review.md. Prior rejection below is
historical.

Combat gate review: Windows Check.ps1 passes 1344 tests, zero skips, strict 28/28,
but acceptance is blocked by two reproduced implementation defects: action
continues after observed empty combat, and resume can exceed the operator-wait
cap. Feedback 1 in subagent.md requests regression fixes. No runtime gate test
or implementation commit occurred. See
reports/2026-10-18-combat-gate-primary-review.md.

Current offline handoff: combat-experience-gate-20261018-01 in subagent.md.
One manually launched executor prepares opt-in combat-only data collection,
bounded neutral operator handoffs and fresh readiness before control resumes.
Tests must preserve valid short-encounter rollout experience while excluding
manual navigation/wait from policy inputs, normalizer updates and rewards.
No game, training, reward change or approval renewal is authorized by this task.

Completed live-continuation-4096-v1: training reached 4096 total steps, saved 15
new checkpoints and passed lineage/reload checks. Separate frozen inference
completed 256/256 actions, zero faults, unchanged artifact identity and operator-
confirmed cleanup. All frozen actions were down/down. Only two completed training
segments had enemies; five later segments were empty timeouts. Improvement is
inconclusive, and no longer unchanged training is started. Next design priority:
combat-experience gating and operator-prepared segments under a new offline
OpenSpec task; no forced resets/scenario injection. See the final experiment
report in reports/2026-10-18-training-4096.md. Original authority was not renewed.

4096-step continuation completed in 421.203 trainer seconds: 15 new checkpoints,
valid parent lineage and reload, unchanged t256 parent, no logged faults. One
natural death/restart/reconnect occurred. Seven completed segments include only
two combat-bearing segments and five empty timeouts; gameplay improvement is
inconclusive under the predeclared rule. No clear occurred. A separate frozen
256-decision check awaits fresh operator readiness; authority was not renewed.
See reports/2026-10-18-training-4096.md. No automatic additional training.

Current experiment preparation: user approved proceeding and confirmed normal
exit. Predeclared live-continuation-4096-v1 targets 4096 total timesteps from the
256-step parent, max ten minutes, then a separate 256-decision/two-minute frozen
check. One planned 20-minute approval allows at most three natural-death restarts;
no renewal on reconnect. No training or further game launch has happened yet.
See docs/EXPERIMENT_4096_V1.md and reports/2026-10-18-training-4096.md.

Latest runtime result: eval-live completed 256/256 frozen-model decisions with
zero faults in about 28 seconds. Actual Lua records show 66 tears and input
release; checkpoint identity stayed unchanged and no training occurred. The
operator confirmed no manual keys during the pilot and responsive manual control
afterward. Task 4.3 passes. Model behavior was mostly left movement/up shooting
(244/256); no quality improvement or combat success is claimed. See
[runtime evidence](../reports/2026-10-18-frozen-live-runtime.md).

The completed runner change is archived as 2026-10-18-frozen-live-pilot-v1;
its baseline spec is frozen-live-pilot. Comparative evaluation tasks in the
separate frozen-policy-evaluation-v1 change remain open. No further run is started.

Frozen pilot preparation: game was closed; installed hashes, launcher preflight
and offline model readback passed. User-authorized 256-decision/two-minute frozen
inference check awaits manual launch/file-2 readiness. Private approval expires
2026-10-18 17:53:37 CEST with at most one natural-death restart. No connection or
actions started. See reports/2026-10-18-frozen-live-runtime.md. No training or
comparative performance test is authorized by this pilot.

Latest accepted offline result: frozen-live-runner-20261018-01 is reviewed on
Windows. Check.ps1 passes 1329 tests, zero skips, strict OpenSpec 27/27. The
attach-only eval-live CLI supports a frozen explicit checkpoint or random policy,
one absolute deadline, partial-segment reporting and final artifact verification.
Existing observation/training modes are preserved. No game connection, approval
renewal or runtime pilot occurred during review; task 4.3 remains not_run and
the change is unarchived. Executor writes are closed. Next: operator-approved
short frozen-model pilot after current game/slot/approval checks. Action repeat
is fixed at 3 and not attested by old checkpoint manifests; no performance claim.
See [review](../reports/2026-10-18-frozen-live-primary-review.md) and
[operator guide](FROZEN_LIVE_PILOT.md). Earlier handoff notes below are historical.

Current handoff: user-requested task frozen-live-runner-20261018-01 prepares an
attach-only frozen/random pilot runner, private summaries and offline tests.
See subagent.md. One external executor is launched manually by the user. No
real-game inference, training, approval renewal or new delegation is authorized.
Primary review/Windows checks and a later separate runtime gate are required.

Latest review outcome: frozen-policy-evaluation-20261018-01 is accepted offline
after feedback 1. Check.ps1 passed 1276 tests, zero skips, strict OpenSpec 26/26.
The prior NaN-normalizer reproduction is rejected and the original private
checkpoint still reloads with unchanged hashes. CheckpointPolicy provides frozen
deterministic recurrent inference and identity verification. The training Monitor
fix prevents SB3 logging failures after finished episodes. Executor writes are
closed. Real pilot/confirmatory evaluation remains blocked; the change is not
archived and no improvement claim is made. Next: a separately scoped frozen-policy
live runner before an operator-approved descriptive pilot. See
[review](../reports/2026-10-18-frozen-policy-primary-review.md) and
[plan](LIVE_EVALUATION_PLAN.md). Earlier pending-review notes below are historical.

Primary review of frozen-policy-evaluation-20261018-01: Windows Check.ps1 passes
1254 tests, zero skips, strict OpenSpec 26/26. Existing private checkpoint reload
through the adapter passed offline. Acceptance is pending feedback 1: a private
copy with NaN normalizer mean was incorrectly accepted at construction. Correction
and behavioral regressions are requested in subagent.md. No runtime run occurred.
See reports/2026-10-18-frozen-policy-primary-review.md.

Current development handoff: user-requested offline executor task
frozen-policy-evaluation-20261018-01 is defined in subagent.md. It prepares a
frozen checkpoint policy adapter and a predeclared comparison plan. The user
launches the executor manually; primary review and Windows checks are required.
No new game run, approval renewal, training or performance claim is authorized.

## Latest accepted result: live training pipeline

The `live-training-loop` change is accepted and archived at
`openspec/changes/archive/2026-10-18-live-training-loop`. All tasks 5.1-5.5 pass:
Windows gate, guarded 0.5.0-dev installation, actual live negotiation, two
2000-action random checks (operator-assisted navigation), one natural death and
automatic restart/reconnect, then a real 256-step RecurrentPPO run. The latter
completed in 27.812 trainer seconds within its two-minute budget and saved
`1f4a187e-s20-t256`; model and normalizer reload plus offline prediction passed.
No additional run/approval renewal is authorized by this result. Isaac remains
available for normal operator use. Exact native steps, policy improvement,
autonomous navigation and achievement eligibility remain unverified.
Check.ps1 passed again: 1224 tests, zero skips, strict 25/25 before archive.
See [training evidence](../reports/2026-10-18-live-training-checkpoint.md) and
[assisted integration evidence](../reports/2026-10-18-live-loop-runtime.md).
Next: predeclare a comparable baseline/training experiment before longer runs.
The sections below are historical checkpoints and do not override this result.

## Latest deployment gate

Second real random check completed: another 2000 accepted actions, 513 tear
records, damage labels, one death and automatic restart from epoch 1 to 2 with
continued actions and zero logged faults. The operator confirmed manual control
works after disconnect. Both recordings had operator-assisted room navigation;
neither proves autonomous navigation or learning. Live-loop task 5.4 is accepted
for assisted integration; 5.5 (short training checkpoint) remains not_run. Original
approval was not renewed. See the second-check section of the runtime evidence.

First real 0.5.0-dev live-loop check completed normally: 2000 accepted native
actions, 517 tear records, no logged faults, five completed segments plus 17
steps in the final unfinished segment. Real oracle labels include damage and
room clears; no natural death/restart occurred. Task 5.3 is accepted; 5.4/5.5
remain open. Input expiry is logged for the last command and Python/listener
closed. Manual-control confirmation is pending. Do not infer learning or
autonomous clears. See [runtime evidence](../reports/2026-10-18-live-loop-runtime.md).

Observer 0.5.0-dev is now installed after closed-game guards, prior 0.4.5-dev
hash verification and private backup. Both deployed files match source; launcher
preflight passed. Check.ps1 passed again: 1224 tests, zero skips, strict 25/25.
Live-loop task 5.2 is accepted. A private 15-minute approval with at most three
natural-death restart attempts was prepared; current manual file-2 confirmation
is required before any live attach. Planned first check: random policy, seed 18,
2000 steps / six minutes, zero tolerated infrastructure faults. No game launch,
attach, action or training occurred during deployment. Tasks 5.3-5.5 remain open.
See [deployment evidence](../reports/2026-10-18-live-loop-deployment.md).

## Live training loop (macOS, 2026-10-18, offline only)

User decisions of 2026-10-18: approximate reward events from frame deltas,
autonomous death restarts within a bounded approval, training on save file 2.
OpenSpec change `live-training-loop` (unarchived; Windows tasks 5.x open)
implements source observer 0.5.0-dev (`live_loop_v1`, training approval, oracle
block, rejected acks, restart budget), `live.py` (LiveClient reader thread,
EventDeriver, LiveBackend, FaultTolerantEnv), CLI `approve-training`/`live`,
`configs/training-live-v1.yaml` and `Start-Live.cmd`. Guide: [LIVE_LOOP](LIVE_LOOP.md).

Checks (macOS `scripts/check.sh`): ruff, format, mypy (win32) passed; 1219 tests
passed including 31 Lua live tests and an end-to-end test of the real `main.lua`
in lupa over a loopback socket (actions, damage/kill/clear rewards, death,
autonomous restart, reconnect, RecurrentPPO checkpoint); OpenSpec strict 25/25.
Primary Windows review subsequently passed Check.ps1: 1224 tests, zero skips;
Ruff, 91 formatted files, strict mypy 39 sources, pip consistency and OpenSpec
25/25. Three reproduced live-mode defects were corrected: overflow history growth,
retry after fatal reader protocol failure, and reset/pause/fault waits outliving
the run budget. Five new unit regressions cover those fixes and interrupted
training logging. Deployment, private training approval and real-game checks
remain not_run. See [Windows review](../reports/2026-10-18-windows-live-review.md). Evidence:
[report](../reports/2026-10-18-live-loop-offline.md).

Next runtime work is a separate operator-directed gate: verify applicable live-mode
authorization, current profile/slot and closed-game deployment before any training
approval or live run. This review installed nothing and started no real game.
A passing synthetic PPO checkpoint is not real Isaac acceptance.

## Current outcome

Roadmap items 03 and 04 are accepted and archived:

- bridge-safe-actions: 8/8 tasks; 50/50 real movement/shooting sequences,
  disconnect/Python-failure release and responsive manual control.
- observation-and-event-contract-v1: 14/14 tasks; 250 real entity frames across
  eight room visits, all four native kinds, bounded recording and replay.

Evidence: [safe actions](../reports/2026-10-17-safe-actions-runtime.md),
[entities](../reports/2026-10-17-entity-observation-v1.md).

Two bounded read-only recordings completed on manually launched observer
0.4.2-dev. The first produced 599 diagnostic records but no combat/lifecycle
candidates; the second captured 595 entity snapshots during manual play across
21 room visits. Reconnect did not renew the exhausted diagnostic window.
The user then closed normally. Both diagnostics are now OFF, no approval exists,
installed/source hashes match and launcher preflight passed. No game is left
launched by the agent. See [runtime evidence](../reports/2026-10-18-oracle-probe-runtime.md).

The subsequent manual-combat probe completed: 592 entity snapshots in two minutes;
1024 diagnostic records stopped at the count limit after 71.629 s. It recorded
153 damage attempts, 33 matched kill/remove/NPC-death groups and seven award
candidates followed by clear=true samples. A later NPC-update still exposed the
old HP before a kill callback showed negative HP, so NPC-update cannot serve as
an applied-damage barrier. No accepted damage/outcome event is emitted.
The operator closed normally; default-off hashes and launcher preflight passed.
See [combat evidence](../reports/2026-10-18-oracle-combat-runtime.md).

The last live-verified installed/source observer was 0.4.4-dev. It activates diagnostics only
through explicit oracle_probe_v1 negotiation from Python; ordinary attach does
not consume the one-shot window. Mode switching uses the same installed files,
without a patched build or cleanup copying. Closed-game backup/hash comparison
and normal launcher preflight passed. Explicit activation now passed in Isaac;
see [negotiation evidence](../reports/2026-10-18-negotiated-oracle-probe.md).
The post-update extension stages at most 16 targets, coalesces repeated callbacks,
logs raw HP or explicit unavailable status, and releases references on all stop/
transition/fault paths. 27 new Lua cases include weak-reference/GC evidence.
Installation/preflight passed. The one on-demand launch awaited a Steam custom-
parameters confirmation, which the operator approved before selecting file 2.
Live observer 0.4.4-dev then delivered 530 snapshots and 106 deferred HP samples.
Diagnostics stopped at 1024 records after 91.316 s; the observation ended early
at 107.375 s with PeerDisconnected following logged game over/run exit. No control,
reset, restart or reconnect was sent. The game process remains open; no mod file
restoration is needed and installed/source hashes still match.
The first post-update retained attempted-callback HP in all 103 paired samples; 20 later
kill records showed changed HP. It is not an applied-damage or completion barrier.
No diagnostic death/revival/floor coverage or new whole task is accepted.
See [preparation](../reports/2026-10-18-post-update-hp-probe.md) and
[runtime evidence](../reports/2026-10-18-post-update-hp-runtime.md).
Next offline work: specify bounded later-frame settlement observations and their
unavailable/transition semantics before requesting another runtime scenario.

Offline subtask 4.4 (2026-10-18, executor implementation and primary review): source observer
0.4.5-dev adds bounded later-frame raw HP sampling (at most three samples per entry,
four post-update callbacks, 16 entries, shared budgets) as `post_update_hp_later` and
`post_update_hp_expired` records. The reviewed 0.4.5-dev is now installed with
matching source hashes; the prior 0.4.4-dev is backed up privately. This is timing investigation only: no
applied-damage, settlement, reward or completion claim. New live evidence is below.
Primary review fixed a reproduced frame-getter reentry bug that could log an old
target in a new room. Six frame-read fault/reentry cases protect this path; two
source-string version tests were replaced. Strict specification length and
conflicting historical hash statements were corrected. 92 targeted Lua tests and
the full 983-test Windows gate passed with zero skips; strict OpenSpec is 24/24.
The original 12/19 tasks remain unchanged; added offline subtask 4.4 is accepted,
so the current OpenSpec checklist is 13/20. No runtime acceptance or archive.
The operator confirmed game closure; process guards, prior/source hash checks,
private backup, two-file deployment and launcher preflight passed. No action
approval exists. No game was launched or attached during deployment.
The subsequent manual-combat attach on 0.4.5-dev completed: 593 snapshots in
120.125 seconds, 99 first/197 later records, 87 windows with changed later HP and
16 removed facts without HP. Diagnostics stopped at 1024 records after 57.825 s;
normal observation continued and the client disconnected normally, with no retry.
One floor callback and eight room callbacks were recorded, but death/revival were
absent. No control/reset/restart was sent, files still match and no restoration
is needed. Whole-task acceptance remains 13/20; no archive. Next offline work:
define conservative frame/event ordering and terminal/partial-step semantics
without assuming later samples guarantee settled damage.
See [runtime evidence](../reports/2026-10-18-later-frame-hp-runtime.md).
See [deployment](../reports/2026-10-18-later-frame-hp-deployment.md).
See [report](../reports/2026-10-18-later-frame-hp-offline.md).

Offline subtask 3.9 is accepted after primary Windows review. The pure,
unwired native_step_lifecycle.py produces local readiness decisions from
acceptance, exact interval, release and sealed endpoint facts. Review reproduced
12 failing regressions and fixed stale cleanup, overflow blocking cleanup,
post-READY transport/context conflicts and reset frame identity. Four additional
context-cleanup tests and two follow-up cases cover the strengthened contract.
150 reducer cases and 391 targeted native cases pass; the full gate passes 1133
tests, zero skips. No existing client, receipt validator, Lua or installed mod
changed. READY remains provisional and supplies no engine evidence or authority.
Original tasks stay 12/19 plus offline 3.9 and 4.4 (actual checklist 14/21).
See [review evidence](../reports/2026-10-18-native-step-lifecycle-offline.md).

Offline subtask 3.10 is accepted after primary review on macOS (2026-10-18): bounded
acceptance, post-update and release/input records inside the default-off `callback_trace`
in source 0.4.6-dev; review fixed unformatted sequence scalars in `release_superseded`.
`scripts/check.sh` passed: ruff, format, mypy (win32), 1167 tests with zero skips using a
non-game JSON shim, and strict OpenSpec 24/24. Windows Check.ps1 is not_run. Installed
stays 0.4.5-dev; no runtime check ran. Checklist 15/22. See [evidence hooks](NATIVE_STEP_EVIDENCE.md)
and [report](../reports/2026-10-18-lua-step-evidence-offline.md).

## Active change: episode-lifecycle (roadmap item 05)

12/19 original tasks plus offline subtasks 3.9, 3.10, 3.11, 3.12, 3.13, 3.14, 3.15 and 4.4 accepted (OpenSpec 20/27); the change stays open. Offline lifecycle/toy backend,
combined negotiation models, step/event models, bounded active waiting, completion
watermarks, receipt assembly/reader and explicit unsupported start/reset pass.
NativeStepClient.step/start/reset remain unsupported. There is no real GameBackend,
Gymnasium-connected Isaac, trained Isaac model or accepted achievement automation.
Later roadmap implementations remain offline backlog contracts, not gameplay proof.

The real callback probe recorded one bounded left pulse, 115 callback records,
stationary post-disconnect snapshots and user-confirmed manual control. It showed
repeated input queries around post-update at the same frame: query counts do not
prove consumed engine updates. No native step or oracle outcome was accepted.
See [runtime trace](../reports/2026-10-17-callback-trace-runtime.md).

The unshipped experimental Lua ledger records bounded facts only (68 offline
cases); it is not imported by the observer and emits no completion or outcome.
The new primary-source oracle audit distinguishes attempted damage from actual
health loss and leaves spawn/kill/clear/death timing and healing attribution
unverified. See [audit](../reports/2026-10-17-native-oracle-api-audit.md).

Native event-export gate (2026-10-19): task 3.6 remains open. The offline design
review chose exact per-kind capabilities, negotiated only with the existing
`entity_action_v1` native-step transport; an aggregate all-kinds capability is
rejected. No kind is eligible for Lua export. The installed callback identifiers
and source audit provide candidate signals, but no complete verified Lua producer
for the seven `OracleEvent` kinds. Runtime evidence is still required for
semantics, identity, attach baseline, ordering, delivery and cleanup. Raw
diagnostic facts are not oracle events. See [contract review](../reports/2026-10-19-oracle-event-contract-review.md)
and [gate evidence](../reports/2026-10-19-native-oracle-export-gate.md). No game
was connected or launched for this offline change.

Python per-kind negotiation groundwork (task 3.12) is accepted: the opt-in requires
exact kind names with `entity_action_v1` and fails closed for old or partial peers.
This does not provide a Lua producer or establish event coverage, delivery or runtime
eligibility. See
[offline evidence](../reports/2026-10-19-oracle-kind-negotiation-offline.md).

Native receipt kind enforcement (task 3.13) is accepted after Windows review: the
client passes exactly its configured kind set, and the receipt assembler rejects
unrequested events before committing the cursor or receipt. Extra `hello_ack`
capabilities do not widen that set. This is Python-only; it adds no Lua producer,
coverage claim, recording-format change or runtime eligibility. Tasks 3.6 and 3.8
remain open. See
[offline evidence](../reports/2026-10-19-native-oracle-kind-receipt-offline.md).

Native recording provenance (task 3.14) is accepted after Windows review. New
`native_oracle_events` manifests persist the exact requested kind list; writers
and replay reject out-of-list events, while legacy manifests without the field
remain unknown (`None`) and replay unchanged. Non-native manifest bytes stay
unchanged. This is offline Python/specification work only: it establishes no Lua
producer, event coverage, delivery or runtime eligibility. Tasks 3.6 and 3.8
remain open. See
[offline evidence](../reports/2026-10-19-native-oracle-recording-provenance-offline.md).

A bounded passive follow-up probe (2026-10-19) attached to observer 0.5.0-dev,
received 599 advancing snapshots, and ended at its deadline with listener cleanup.
Its native log contained only attach, post-update, and stop records; it observed
no combat or lifecycle callback facts. All snapshots reported an unpaused, clear
room with no room transition. Source review shows that post-update is periodic,
while other probe records require their corresponding game callback; NPC HP reads
are filtered to targets previously queued by damage or NPC initialization. This
matches the clear-room capture and is not a logger failure. It is not negative
event evidence and does not change task 3.6/3.8 eligibility. See
[follow-up evidence](../reports/2026-10-19-oracle-probe-deadline-followup.md).

NativeEventOutbox now retains post-baseline events, including neutral time, until
explicit delivery acknowledgement. It bounds pending records/bytes, stages
watermarks and permanently faults on late/regressing/foreign events, overflow or
invalid delivery acknowledgement. Offline producer-to-receipt tests pass. It has
no engine emitter, sender, action authority or callback-completeness proof.
Task 3.8 remains incomplete. See [outbox evidence](../reports/2026-10-17-native-event-outbox.md)
and [protocol](NATIVE_EPISODE_PROTOCOL.md).

Latest Windows `Check.ps1` (2026-10-19 task 3.14) passed 1248 tests with 14
optional isolated-Lua tests skipped, plus Ruff, formatting, mypy (44 source files),
pip consistency and embedded strict OpenSpec. Explicit
`./scripts/OpenSpec.ps1 validate --all --strict` passed 30/30. The successful
check used an isolated `TEMP`/`TMP` directory after a default-temp pytest cleanup
permission error. No dependency or lock changes. Offline success does not establish
Isaac acceptance.

Offline native-step evidence refinement (2026-10-19): the active specification,
design and protocol now classify reducer facts as caller assertions and define
ReleaseFact as bridge-held-override removal only. Acceptance/input/hold/release
callbacks, post-update observations and frame deltas do not prove engine-consumed
updates, neutral final input or endpoint callback quiescence. READY remains a local,
unverified candidate; no live completion is supported. Windows Check.ps1 passed
1644 tests with zero skips; strict OpenSpec passed 30/30. No game was launched and
no runtime probe or approval was used. The installed `resources/scripts/enums.lua`
documents when the input callback is requested and that post-update runs after a
game update, but it does not define input-consumption order or an endpoint-seal
signal. The local API audit therefore found no documented evidence source that
supports live stepping. See
[evidence](../reports/2026-10-19-native-step-evidence-contract.md).

## Working mode

Work is sequential. The user manually delegates bounded offline tasks via
subagent.md; prior later-frame-hp-20261018-01 and native-step-lifecycle-20261018-01
assignments are accepted and closed. New task lua-step-evidence-20261018-01 adds
default-off production-Lua diagnostic hooks for acceptance, update and bridge
release state, without claiming engine consumption or physical neutralization.
It is assigned, not executed or accepted. Only its explicit offline source/test
writes are authorized; no deployment or game access.
agent-status.json must match the current task ID; old status is historical.
The isaac-remote-handoff heartbeat remains PAUSED; no automatic monitoring or
successor delegation is authorized by this assignment.
See [workflow](AGENT_WORKFLOW.md).

## Runtime permissions and limits

Standing permission covers ordinary-profile observation, bounded after-natural-
death restart and bounded movement/shooting tests. Current instance and selected
slot must still be confirmed before live actions. Confirmation is not automatic
slot attestation or training isolation; file 2 alone is not isolation.

Default action authority is nil. Private approval is at most 30 minutes; the
per-mod-load action lease is nonrenewable 120 seconds. Preserve 500 ms heartbeat,
15-frame/250 ms hold bounds, explicit neutral and failure cleanup. Actions and
post-death restart stay mutually exclusive; restart stays three attempts per ten
minutes per mod load, without reconnect renewal. No forced resets, save/Steam
Cloud changes, REPENTOGON, unattended startup/supervisor or training authorized.

## Accepted earlier evidence

- Steam Repentance+ v1.9.7.17.J460/build 22878971; original minimal adapter using
  bundled socket/json, no REPENTOGON requirement.
- Item 02: real Lua/Python observations, user-correlated positions/health/rooms,
  approximately ten-minute 3000-snapshot soak and bounded reconnect.
- Observer 0.2.0: PauseOnFocusLost=0 background operation and one verified
  natural-death restart; archived. Do not repeat or reimplement this work.
- Seven legacy mods were reversibly disabled at the user's request while closed;
  four already-disabled mods were preserved. The original soak used the earlier
  mixed-mod profile; later short probes used observer-only configuration.

## Workspace, blockers and next action

Active checkout: D:/isaac. Preserve the old Documents compatibility junction,
linked dependencies and local rollback. See [relocation](../reports/2026-10-17-project-relocation.md).
Private logs, recordings, approval files, saves and backups stay ignored.
errors.txt is unrelated untracked material and excluded from commits.

The passive oracle probe is implemented with 27 isolated Lua cases; see
[evidence](../reports/2026-10-18-passive-oracle-probe.md) and
[manual procedure](ORACLE_PROBE.md). Raw attempted damage, later HP samples,
kill/remove/clear candidates and lifecycle readings remain diagnostic facts.
Partial/terminal steps continue to fault; no terminal receipt is enabled.

Next: keep native stepping unsupported unless authoritative engine documentation
or a separately authorized bounded probe establishes independently verifiable
consumed-update and event-seal evidence. Callback telemetry and frame deltas are not
substitutes. This status grants no runtime authority. Later-frame raw sampling and a floor callback slice are recorded; task 4.1 still
lacks death/revival and broader transition coverage. Attempts, concurrent effects,
negative death HP and realized damage remain distinct. Exact step application,
attach/event ordering, death/revival/transition delivery and outcome attribution
remain unresolved. Repeated real episodes additionally require verified training
isolation, active-slot identity and explicit start/reset authority. One hundred
real episodes, achievement eligibility and sustained learning remain unverified;
no archive or progression claim is justified.

Latest readiness attempt: the 15-minute approval had expired before the game
started (readback -2084 seconds). No live connection or control was attempted.
The operator must exit normally before a deliberate bounded approval refresh and
manual relaunch; live tasks 5.3-5.5 remain unfinished.

The operator subsequently closed Isaac and explicitly requested continuation.
Closed-game guard, installed/source hashes and preflight passed. The bounded
approval was deliberately refreshed to expire at 2026-10-18T16:32:47+02:00 with
at most three natural-death restarts. Awaiting manual relaunch/file-2 readiness;
no live connection or actions yet.

Following explicit full-exit confirmation, combat-gate recheck preparation passed:
closed-game guard, matching mod files and preflight. A deliberate 15-minute
replacement approval expires at 2026-10-18 21:12:14 CEST, max_restarts=1. Awaiting
manual file-2 launch and paused-room confirmation before the 256-action/three-
minute random check. No training, game launch or connection occurred here.
