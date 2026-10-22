# isaac-threrisaifuture roadmap

Milestones and acceptance, not an experiment log. Current execution, lineage and
blockers live in [STATUS](docs/STATUS.md). Requirements live in openspec/specs;
completed receipts remain in reports/. Historical roadmap text is preserved in
[the snapshot](docs/history/2026-10-21-workflow/ROADMAP.md).

## Immediate dependency order

1. The geometry warm-start pilot is closed and verified; no gameplay improvement
   was established. See [results](reports/2026-10-21-geometry-training-pilot-results.md).
2. Boundary-supported v5 feedback and bounded signed recovery are verified. Its
   five-minute child pilot still showed97.16% corner occupancy and observed damage/
   clear lower bounds0. See [results](reports/2026-10-21-boundary-progress-results.md).
3. Shot audit confirms sparse clear opportunities and inherited direction bias;
   [evidence](reports/2026-10-21-shot-selection-results.md). The scripted clear-shot
   [control passed](reports/2026-10-22-mixed-control-results.md):target HP10->6.5,
   no observed health loss. The [exposed-start pilot](reports/2026-10-22-ready-curriculum-pilot-results.md)
   qualified setup/handoff/optimization/reload:1536 saved steps,native HP-loss lower
   bound7,player loss2half-hearts,clears0. Play remains limited:97.883% of endpoints
   were near a new point on the left wall;both frozen phases recorded no progress.
4. Analyze target switching and reachable firing-position/movement feedback after
   the first target disappears before proposing longer training. Compare damage,
   taken damage,clears and stagnation,not weight/reward changes alone. A simpler-room
   control needs explicit New Run authority. No automatic extension or model promotion.
5. Establish held-out, multi-seed combat improvement before full-run claims.

## M0-M2. Foundation and native environment

Foundation, Python 3.12/CPU RL stack, local OpenSpec, typed bridge, bounded actions,
entity observations, native step evidence and live-training/checkpoint plumbing
have implementation and recorded acceptance at their individual declared scopes.
This does not mark every original environment/outcome scenario complete.
The user now permits training on file 2 and accepts its risks; isolation/achievement
eligibility remain evidence issues, not obsolete blanket training prerequisites.

| Original item | Acceptance to retain |
| --- | --- |
| 01 audit-game-compatibility | Installed build/API/license/provenance evidence, not README assumptions |
| 02 bridge-handshake-and-observation | Bounded validated native read, identity/version/timeouts and cleanup |
| 02a restart-after-game-over | Natural death evidence, bounded authorized restart/reconnect and new identity |
| 03 bridge-safe-actions | Session/episode/frame binding, expiry, stale/replay refusal, observed effect/release |
| 04 observation-and-event-contract-v1 | Versioned real entity coverage, fixed-shape encoding and oracle separation |
| 05 episode-lifecycle | Native step/reset/outcome evidence; distinguish unknown/truncated/faults from clears/deaths |
| 06 gymnasium-environment-v1 | Gymnasium contracts, bounded lifecycle and compatible native backend evidence |

See current STATUS, relevant main specs and named reports before reopening an item.
Unaccepted native scenarios stay open in their change tasks. A prior mock result
or old roadmap checkbox is not current integration proof.

## M3. Combat learning

### 07 РІР‚вЂќ `combat-baselines-and-reward-v1`

Add a random baseline and an explicitly labeled simple scripted baseline.
Implement event-driven rewards, exploit prevention, a bounded room pool, and
several difficulty levels. Fix train/validation/test splits before tuning.

**Acceptance:** metrics for both baselines; reward-exploit tests; equal episode
budgets; environment errors reported separately from gameplay defeats.

### 08 РІР‚вЂќ `combat-ppo-training`

Begin with a small PPO model; compare RecurrentPPO if experiments justify memory.
Provide a bounded training command, evaluation callbacks, checkpoint manifests,
RNG/normalizer persistence, and training resume.

**Acceptance:** several training seeds; the model beats random on validation;
improvement appears in room clear rate/damage, not just reward. Use a predefined
selection rule. Initial target: a 20 percentage-point clear-rate improvement over
random across at least 100 evaluation episodes. If random is near the ceiling,
increase difficulty and fix the revised criterion before the experiment. Report uncertainty.

### 09 РІР‚вЂќ `combat-curriculum-and-regression`

Gradually add enemies, bullets, obstacles, and room types. A curriculum extension
must not erase previously learned skills. Compare against the scripted baseline
and retain negative results.

**Acceptance:** the model beats random on held-out test scenarios and reaches the
predeclared task threshold without oracle leakage. Regression on the old task set
stays within a tolerance fixed before training. Supporting every boss is not yet required.

## M4. Spectator mode and navigation

### 10 РІР‚вЂќ `spectator-and-checkpoint-browser`

Run a selected checkpoint at ordinary game speed. Show seed, model version, events,
and gameplay metrics. Stop immediately releases actions. Do not train silently
while the user is watching inference.

**Acceptance:** select and replay a saved model, inspect the episode outcome,
stop and recover control; incompatible models are rejected.

### 11 РІР‚вЂќ `known-map-and-navigation`

Track visited and legitimately revealed rooms, doors, local goals, obstacles,
and deadlocks. Learn navigation without combat first, then combine with combat.

**Acceptance:** at least 100 unseen scenarios; goal success, stuck rate, and excess
transitions improve over random. Fix a threshold before implementation, such as
90% success in simple enemy-free rooms. Oracle data must not reveal hidden rooms.

### 12 РІР‚вЂќ `floor-policy-and-boss-routing`

Select rooms, backtrack, locate the boss, and change floors. Define interfaces
between strategic and combat policies. A heuristic router is allowed as an
explicitly labeled intermediate baseline.

**Acceptance:** autonomous exploration of a bounded floor set, no endless loops,
and measured success on unseen seeds. Report learned and scripted decisions
separately; a heuristic does not establish learned route planning.

## M5. Items, resources, and secret rooms

### 13 РІР‚вЂќ `item-knowledge-dataset-v1`

Start with 30РІР‚вЂњ50 items and 10РІР‚вЂњ20 verified interactions. Record sources, licenses,
versions, numerical effects/tags, provenance, and unknown fields. Extend actions
for active items, bombs, cards/pills, and interactions only after API verification.

**Acceptance:** item IDs confirmed in-game; reference data contains no hidden
contents for the current seed; unknown items handled explicitly; data is not
re-fetched on every policy step.

### 14 РІР‚вЂќ `resource-and-build-policy`

Learn item selection, shops, consumables, active items, build context, and resource
budgets. Start with controlled scenarios, then floors. Use bounded shaping and
check farming loops; evaluate counterfactual builds outside live episodes.

**Acceptance:** improve over random choices and a simple item-tier baseline on
predefined scenarios. Measure run outcomes and resource use. An automatic reward
for a known item pair is not evidence of a learned strategy.

### 15 РІР‚вЂќ `secret-room-discovery`

Derive wall candidates from known geometry, track attempted searches, manage bombs,
and record actual opening/entry events. Use oracle data only for labels/evaluation.

**Acceptance:** on unseen floors with equal bomb budgets, success per bomb beats
a random valid-wall baseline; repeated entry yields no reward; hidden maps never
reach the policy. Cover ordinary and exceptional layout constraints.

## M6. Complete runs and reliability

### 16 РІР‚вЂќ `full-run-integration`

Integrate combat/navigation/strategy, expand items and bosses, provide reliable
resets, and define the target character, difficulty, route, and final boss.

**Acceptance:** a series of complete autonomous runs without manual input; report
win rate, depth, damage, and exceptions across all episodes. Choose the success
threshold before test evaluation. One victory or seed cannot establish general competence.

### 17 РІР‚вЂќ `benchmark-and-training-optimization`

Measure the single-game bottleneck. Compare CPU/GPU, action repeat, and batch
sizes. Try multiple game instances only with isolated profiles, ports, and input.

**Acceptance:** reproducible throughput benchmark; acceleration preserves step and
reward semantics; compare steps/sec against quality, memory, and failure rate.

### 18 РІР‚вЂќ `bounded-session-runner` (optional)

A finite Python/PowerShell runner executes authorized game/training commands using
durable project state. Routine stepping/waiting does not require an LLM turn.
It does not make architecture decisions or bypass approvals. Distinguish completed,
blocked, failed and budget-exhausted states. No endless restarts or lease renewal.

**Acceptance:** interruption/resume, retry and duration limits, saved exit codes,
and no repeated application of a completed change. Skip this milestone if
interactive development is sufficient.

## M7. Persistent progression to Dead God

These are progression-evidence requirements, not superseded blockers on the user's
authorized file-2 training. Eligibility/progression acceptance still needs proof.

### 19 РІР‚вЂќ `save-slot-and-achievement-eligibility`

Verify a supported non-visual API for selecting and attesting file 2. Audit the
exact installed build's achievement eligibility with mods, debug options, special
seeds, challenges, daily and online modes. Training scenarios must not be counted
as legitimate progression. Do not use save editing or unlock commands.

**Acceptance:** fail before autonomous control when file identity is unknown or
wrong; actual evidence of a legitimate new unlock retained after normal exit and
restart on file 2. Verify that untouched files retain their progress. A separate
slot does not establish settings, Cloud or Steam achievement isolation.

### 20 РІР‚вЂќ `progression-ledger-and-goal-selection`

Track file-specific completion marks, challenges, collected items, achievements,
unlock dependencies and daily/time-gated objectives for the verified version.
Choose learning/campaign goals from remaining prerequisites while keeping the
gameplay policy learned and oracle data separated. Persist progress across sessions.

**Acceptance:** reconcile ledger with actual file-2 state across restart; show
remaining objectives and evidence provenance; do not substitute account-wide
Steam achievements for file-specific completion or replay earned rewards.

### 21 РІР‚вЂќ `dead-god-campaign-and-verification`

Integrate eligible campaign runs and reliable resume through the terminal
launcher, with explicit budgets and stop reasons. The publisher's 2024 FAQ states
new Repentance+ Dead God files require online achievements while online disables
mods; reverify this on the target build and design an eligible supported path.
Do not promise an entirely mod-driven online solution before resolving this gap.

**Acceptance:** the actual game recognizes Dead God on file 2, its required
progress is independently reconciled and persists after normal restart. No
unlock commands, imported completed saves or save editing can satisfy this goal.
Report autonomous and user-assisted objectives separately; one won run, a score
threshold or an account-level unlock does not complete this milestone.

## Shared definition of done

Proposal and specifications agree; tests and strict validation pass; required
real-game evidence exists; configurations and migration notes are current; STATUS
provides a handoff. Verify learning progress separately from software correctness.
Archiving never replaces evidence. Required external user actions remain explicit blockers.
