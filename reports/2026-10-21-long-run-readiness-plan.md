# Plan: readiness for reliable long training

Date:2026-10-21,Europe/Amsterdam. User stopped the four-hour attempt and requested
planning. No further launch,New Run,training or scheduled supervision is active.
Do not resume the overnight experiment without a new user request.

## Current verified state

- Latest continued checkpoint:7d53f55f-s20-t7424,seed20,conservative-v2.
  Original08e0d262-s20-t6912 remains intact. No fresh-model initialization.
- Corrected startup ran161.23seconds outer,725 combat decisions,512 new saved
  steps,two checkpoints(t7168,t7424),213 unsaved decisions.17.5HP credited damage,
  two player-damage events,zero infrastructure faults/deaths/restarts.
- Stop reason:Navigation budget exhausted after20 room transitions. This was an
  early management stop,not a completed four-hour experiment or a training crash.
- First new checkpoint independently confirmed PPO108->112,20/20 policy tensors
  changed,normalizer continued. These prove updates,not improved gameplay.
- Separate scripted comparator:224 decisions,66.5HP damage. It is a positive
  control,not a learned policy or an independently sampled room-clear result.
- Full Windows gate:2048 passed,zero skipped;OpenSpec40/40. This does not establish
  long unattended readiness. Initial pre-game lease-rounding failure was retained
  and corrected;the later navigation stop exposed a different practical limit.
- Primary verified game/learner/supervisor absent,port9528 free,approval JSON/tmp
  absent and installed default-off observer unchanged. No requested New Run was
  performed before cancellation. Local receipt:reports/local/overnight-user-stop-verified.json.
- Untested time-only navigation/explicit replacement sketch is saved separately
  in reports/local/deferred-time-only-navigation-and-reset.patch;production source
  restored to the committed,previously tested behavior. Do not treat the sketch
  as implemented or apply it without review/tests.

## Objective and order

First make a short combat learning session reproducible,observable and resumable.
Then qualify autonomous duration. Full-floor/boss/progression work remains the
larger project goal;it must not be silently assumed to exist in the combat MVP.
Do not spend another four hours merely to test startup or discover a count cap.

### 1. A durable session runner with honest states

Move the experiment-only orchestration contract into a reviewed versioned runner,
retaining the existing Steam/menu/bridge guards. Use one fixed monotonic training
deadline and derive lease expiry from that deadline and one explicit clock read.
Separate startup,combat learning,navigation,checkpointing,early_stop,fault,
completed and user cancellation. A live process or active timer alone is never
reported as learning. Show latest completed checkpoint,last update time,actual
combat decisions and time spent navigating/waiting.

Acceptance:
- Fractional-clock/startup-delay cases cannot create a lease beyond the deadline.
- Focus refusal,foreign process/approval,missing or incompatible parent stop
  before gameplay;no automatic fallback to a fresh model or another save slot.
- A clean budget exit before the target duration is labeled early_stop,with its
  exact reason. Final status is durable even if optional metrics parsing fails.
- User stop and wall-time stop release input,close only the owned game,remove
  only the owned lease and release temporary sleep prevention. No auto-relaunch.

### 2. Navigation without hidden session-length caps or empty-room loops

Add explicit time-dominant navigation for an approved finite training window.
Remove binding cumulative command/transition/pulse-time counters in that mode;
retain each action/release/identity/health/path/freshness timeout and the global
wall deadline. Keep the current bounded default for short diagnostics.

A larger transition number alone is insufficient. Track legitimately observed
room/door visits and progress so the runner can distinguish searching for a new
fight,an exhausted observed ordinary-room component,an unreachable door and a
transport fault. Do not infer a full hidden floor layout from partial visits.
Do not spend four hours circling already cleared rooms while showing training.

For the initial combat MVP,define an explicit experiment-level choice when no
new fight can be found:stop with a clear reason,or start a fresh ordinary New Run
through a separately authorized menu action. Preserve model/optimizer/normalizer
on game reset. Boss/floor traversal is a later alternative,not implied by current
ordinary-room navigation. The user authorized one new run during the stopped
attempt;it was not executed and must not become a standing reset permission.

Acceptance:
- Simulated travel beyond20 transitions can reach another fight without the old
  count cap;the global deadline still wins and release/focus guards still work.
- Known repeat routes produce an observable no-progress result rather than an
  endless silent loop. A fight resumes learning without navigation frames entering
  the policy normalizer or learner rollout.
- New Run cannot replace Continue by default. A future explicit replacement mode
  verifies selected file2,declared replacement intent,native [New,2] and active
  Isaac;retains a finite menu key/time budget and stops on unexpected state.

### 3. Checkpoint and data integrity before longer runs

Make model/normalizer/manifest/latest publication transactional enough that a
reader or interrupted writer sees the prior complete checkpoint or the new
complete one. Test interruption during save and strict compatible resume. Preserve
lineage across game deaths and New Runs;never equate a game reset with model reset.

Continue conservative reward accounting:missing enemies are not kills,healed HP
cannot be farmed,software time boundaries are not deaths,empty exports are not
verified clears. Record active combat,management,withheld and unsaved decisions
separately. Finish native revival-phase coverage when a relevant enemy is
encountered;Gusher evidence does not verify Globin mechanics.

Acceptance:
- Interrupted-save and concurrent-read tests never select partial state or
  initialize a new policy silently;old completed artifacts remain loadable.
- A resumed checkpoint preserves optimizer,normalizer and RNG where declared;
  fresh PPO updates and completed/partial rollout counts are auditable.
- Native damage/clear evidence is sourced from raw state transitions,independent
  of training reward. The pending revival scenario stays explicitly pending.

### 4. A comparable learning evaluation

Declare a small validation suite of ordinary combat scenarios:room shape,enemy
composition,character/build,entry history and decision/wall budgets. Where normal
seed entry is supported,verify the seed through the native log;do not restore or
edit saves. Use separate training/validation/test scenarios and several seeds
before general claims. An identical-input shadow replay tests decisions only;
one mixed-control trajectory is not matched gameplay evaluation.

Compare frozen original t6912,current t7424 and a future continued checkpoint,
plus random and explicitly scripted controls. Freeze normalization/recurrent
reset rules for evaluation. Report damage dealt/taken,verified room-clear rate,
active-combat versus navigation time,near-wall stationary movement,deaths and
infrastructure faults. Include every episode and failure. Decide from comparable
play rather than changed tensors,training reward or one successful encounter.

Audit large-room absolute-coordinate clipping before changing the observation.
If a schema repair is needed,version it and plan an explicit compatible lineage
or fresh development model;never silently reinterpret t7424 inputs.

### 5. Qualify duration in stages

| Stage | Purpose | Acceptance before increasing duration |
|---|---|---|
| Offline gate | New runner/navigation/reset/save contracts | Behavioral regression cases and full Windows gate,zero unexplained skips |
| 5-minute supervised native pilot | Startup,resume,real learning,manual stop | Positive compatible checkpoint update,correct identity/raw damage readback,owned cleanup |
| 15-30-minute autonomous pilot | Multiple encounters/resets/travel | Demonstrate an episode boundary followed by more combat learning;no hidden count stop or empty-room loop;all stops explained |
| 60-minute finite pilot | Duration/resource/deadline reliability | Sustained auditable combat/update progress and timer-driven stop with verified checkpoint/input/approval/process cleanup |
| 4-hour experiment | Gather actual learning evidence | Fresh user request,declared plan/lineage/evaluation;earlier stages accepted;final completion and frozen comparison recorded |

Encounter-dependent conditions must be actually observed or remain pending;time
passing and a running process do not substitute. For each stage declare its
wall-time and emergency disk/fault limits,source/config hashes,compatible parent,
stop conditions and exact cleanup. There are no forced deaths,save edits or
unlock shortcuts. If the same approach fails three times,stop and revise it.

## First concrete implementation task

Start with the durable runner/deadline/status contract and its regression tests,
then explicit time-dominant navigation plus no-progress handling. Keep the
learning algorithm,reward and observation unchanged while diagnosing orchestration.
Do not resume training or apply the deferred patch merely because this plan exists.
The next live action should be a separately declared five-minute qualification,
not another overnight run.
