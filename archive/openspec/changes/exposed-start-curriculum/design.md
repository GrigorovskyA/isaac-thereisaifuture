# Design

## Context

See proposal.md for motivation. Native mixed-control evidence at 743a655 confirms
one-frame positioning/braking and three-frame shooting in room 83. Existing
`LiveBackend` provides bounded commands, `live._train_run` constructs the gated
collector, `training.train` resumes complete PPO/normalization state and publishes
256-step checkpoints, and `CheckpointPolicy` provides immutable named inference.
The current trainer closes its environment/client on exit; phase orchestration
must account for that instead of reusing a closed transport.

## Goals / Non-Goals

Qualify an unscored exposed-start handoff and a small learned continuation. Keep
reward, observation/action schemas, hyperparameters and the segment-refresh
contract unchanged. No imitation, teacher action mask, reward tuning, save-state
restore, New Run, death reset or automatic longer stage. Implementation is opt-in;
the first native attempt refused setup before gameplay actions. See the Windows
review evidence report.

## Decisions

### 1. Separate setup from the collector

Add an explicit opt-in setup seam before the learning environment/normalizer
starts collecting. Reuse the qualified short-step route/braking logic over the
structured backend; do not advance a training env while discarding its returns.
The latter would still consume novelty, damage credit and normalization state.
Setup uses move/neutral only, never shooting, and remains separately logged.

Require fresh file-2 Continue, ordinary Isaac, room 83, compatible measured grid,
door within 20 units of (560,280) and a visible target near (80,200). Traverse
(560,200),(320,200), require speed <=0.1 and recheck position after coasting.
Use one-frame movement; first-stage setup stops at any player health loss.
After release obtain a newer same-context snapshot with a clear target within
8 transverse units and measured range. Stale success is not a handoff token.

The no-action capture on 2026-10-22 showed 60 initial snapshots with oracle
enemies but no visible enemies; the unchanged target became visible at sample61,
3.031 wall seconds later. Before movement, permit an initial command-free wait
only when all other preconditions pass and the visible enemy set is empty.
Cap it at 5 seconds and 100 snapshots, including the initial one, inside the
existing 30-second setup and shared lease. Read every queued sample in order;
stop on health loss, context/grid/weapon/door or oracle-membership changes.
Once any enemies are visible, require the same fixed target immediately; no
target substitution, repeated positioning or renewed budget. Preserve initial
and ready snapshots separately. This is readiness waiting, not a retry after
setup refusal. Its native movement/handoff remains unverified.

Create fresh reward/health/HP baselines at the learner boundary. Existing
`EventDeriver.begin` establishes current HP without crediting earlier damage;
test this with a wounded target. Start recurrent inference at an episode boundary
and apply the saved observation normalizer exactly once. Keep target HP, route
goals, phase labels and all oracle bookkeeping outside policy inputs and info
that could later be reused as model input.

Only the first learning segment gets this scripted exposed start. Normal cleared
room navigation may use the existing opt-in gate/navigation path within the same
budget; its actions remain unscored as today. Do not repeatedly teleport, reset
or reposition the learner whenever it makes a poor move.

### 2. Branch the exact saved state

Source is the explicit named checkpoint a0a93c29-s20-t26368 under
`runs/live-boundary-v5-pilot-20261021/seed-20/checkpoints/`.
Prepare `runs/live-exposed-start-pilot-20261022/seed-20/checkpoints/` only if absent.
Copy the named checkpoint and a local latest pointer transactionally, verifying
model, Adam, normalizer, manifest and RNG identities before learning. The copied
initial ID remains t26368 and is not a new trained model. Record the protected
source path/hashes and the new run root in a versioned branch receipt.

Retain config training-live-boundary-v5-pilot.yaml and hash
a0a93c29b588fb2ee4b23e3c19f16c5e4124b97fb312503978a6ada405f13f15,
seed 20, schema 2/723, reward live-firing-v5, three-frame learned actions and
collector live-segment-refresh-v1. Add experiment metadata exposed-start-v1,
not a checkpoint-format mutation. All parent/ancestor artifacts and pointers
are immutable; only the child run may publish later checkpoints and change its
own pointer. A missing/incompatible parent stops; no fresh-model fallback.

### 3. One bounded pilot, then optional frozen observations

The implementation produces an exact frozen run plan before execution:

| Limit | Proposed value |
|---|---|
| Total native startup, setup, learning and evaluation | 300 seconds, one absolute lease |
| Startup | At most 45 seconds within the total |
| Initial setup | At most 30 seconds and 240 one-frame commands |
| Initial visibility readiness | At most 5 seconds and 100 snapshots inside setup; zero commands |
| Learning | At most 180 seconds and 2048 new steps; cumulative target 28416 |
| PPO | n_steps 256, batch 64, 4 epochs; unchanged |
| Frozen observations | Parent then saved child; at most 20 seconds and 64 decisions each, including model loading/setup |
| Evaluation setup | At most 240 one-frame commands per phase, inside its 20-second cap |
| All action commands | At most 3000; releases tracked separately |
| Learning/evaluation no-progress gate | 9000 game updates, explicitly retained |
| Environment segment ceiling | 1800 game updates; truncation does not reset the game |
| Shared output / trace | 2 GiB including child artifacts / 128 MiB across phases |
| Faults / retries / death restarts / New Run | 0 |
| Training health stop | First death, health <=1 half-heart, or 4 half-hearts cumulative observed loss |
| Setup health stop | First observed health loss |
| Frozen phase health stop | First observed health loss; no reset |
| Final cleanup | At most 45 seconds separately; no gameplay lease renewal |

Training stops before any automatic reset/restart on observed death. Gate this
before the vector environment can ask for its next episode; test the absence of
restart commands. The legacy approval format's minimum max_restarts=1 is not
authority to dispatch one. Time, count, disk, trace, transport freshness and
native 15-frame/250ms expiry guards remain independently effective.

Run learning first so a parent baseline does not consume the only available
training encounter. After learning, freeze the exact saved child and attempt
short parent/child native observations only with compatible eligible combat.
Use deterministic `CheckpointPolicy` instances with frozen statistics and fresh
recurrent state; training remains stochastic. Phase-start configuration,
player/enemy health, positions, grid, weapon and context fingerprints are logged.
If state or the learned checkpoint is unavailable, mark the phase not_run.
Never substitute the copied initial child or start a new run to obtain a sample.

Manage phase connections explicitly: phase views suppress client close while the
pilot retains one reader and releases before transfer. A lost connection makes
later phases not_run: owned-instance reconnect has no implemented provenance
proof and is refused. No second Steam launch or menu reentry recovers a phase.
An opt-in reader-level death latch disconnects immediately, including during PPO
optimization, to cancel the bridge's delayed death restart before it can dispatch.

### 4. Separate descriptive evidence from improvement

Game update spans use the existing 30-updates-per-second contract; command frame
and wall-clock expiry limits remain independent. Each phase reports observed
HP-loss lower bounds, half-hearts lost, clear/death
events and coverage, active seconds, counts, faults and initial/final fingerprints.
Report time near the old corner and windows of >=10 active seconds with position
bounding-box diameter <20 and no registered enemy HP loss/clear. These are report
metrics only, not new rewards or policy features. Record clear-line exposure and
aim proxies as secondary diagnostics, never hits.

Continue cannot clone the world: the order is fixed and enemies/resources may
change. Label all native parent/child results observational, even if measured
start fingerprints happen to match. Report unavailable phases and all attempts;
do not call this paired, held-out or multi-seed evaluation. A later controlled
comparison requires a separate plan/authority. No weight/return/update count can
promote a model. Pilot qualification requires learner-attributed native damage,
at least one real update and a reloadable learned checkpoint; otherwise leave
native qualification unfinished without extending the run.

## Risks / Trade-offs

- Setup still fails in changed native state -> strict identity/geometry refusal;
  the offline convergence model does not replace live guards.
- Setup/game continues during optimizer work -> existing release, reader drain
  and segment refresh; verify the first actual learner action against fresh state.
- Death or rapid clear occurs before 256 samples -> retain valid event evidence
  and unsaved accounting; do not manufacture a checkpoint or force a restart.
- The learner leaves the firing lane -> record its behavior; do not steer or mask
  its actions to make learning look successful.
- Post-training comparison has no comparable combat -> not_run/observational
  limitation, not a reset or an improvement claim.

## Migration Plan

Implement and test the opt-in seam and exact copy/readback before any native run.
Run the focused gates then the full project gate on final source. Freeze a fresh
assignment and all protected inputs; use Steam and guarded file-2 Continue.
No diagnostic Lua deployment is required: default-off observer already records
native tear callbacks; structured action/damage traces provide the main evidence.
Release, close observer/game normally, remove only the unchanged owned approval,
verify listener/process absence and reload all saved children. On failure preserve
the exact parent, child checkpoints, unfinished accounting and raw local evidence;
disable the opt-in path. No source/dependency or save rollback is necessary.
