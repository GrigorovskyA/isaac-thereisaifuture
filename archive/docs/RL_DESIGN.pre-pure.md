# RL design: observations, rewards, and evaluation

## Problem definition

Start with one character, a bounded combat-room set, an initial build, and
structured Lua API data. Learn without human demonstrations. A scripted baseline
is allowed for comparison but must not be presented as a trained policy.

Compare a small feed-forward PPO against RecurrentPPO/LSTM. LSTM does not replace
correct episode resets, and recurrent models are not assumed universally better.

Possible future hierarchy: combat for frequent decisions, navigation for local
goals, and strategy for rooms/items/resources. Do not build three policies before
the combat vertical slice works.

## Observation v1

| Group | Examples | Constraints |
|---|---|---|
| Player | Position, velocity, HP, cooldown, status | Fixed units and normalization |
| Enemies | Relative position/velocity, type, observable HP | Stable ordering, mask, capacity |
| Threats | Projectiles, lasers, dangerous regions | Proximity/danger priority, overflow diagnostics |
| Geometry | Walkable cells, obstacles, doors | Visible or legitimately revealed information only |
| Inventory | Bombs, keys, coins, active charge, item features | Add at the appropriate milestone |
| Map memory | Visited/revealed rooms | No hidden neighbors or contents |

A first environment can use a fixed float vector with masks. Add dictionary
observations or an entity encoder when justified. Every field defines source,
dtype, shape, range, and the meanings of zero and unknown. Arbitrary textual item
descriptions cannot directly become numerical MLP features without an encoder.

## Action v1

Proposed `MultiDiscrete([9, 5])`: neutral plus eight movement directions, and
neutral plus four shooting directions. Verify actual diagonal/input support during
the audit. Start with an experimental repeat of three game updates. Add bombs and
abilities after basic combat, with explicit rising-edge and cooldown semantics.

Fix the coordinate system and Y-axis direction. Diagonal movement must not gain
unintended speed from adding axes. Keep invalid-action handling consistent in
training and evaluation, and report its frequency.

## Initial reward hypotheses

`configs/reward-v1.yaml` records **engineering hypotheses**, not optimized or
learned weights. Only combat is enabled; later subsystems remain disabled.

| Event | Initial coefficient |
|---|---:|
| Fraction of an ordinary enemy's initial HP removed | Up to +2 for its full initial HP |
| Ordinary enemy killed | +0.5 |
| First room clear | +8 |
| Half-heart lost to enemy damage | -8 |
| Character death | -25 |
| Active combat second | -0.01 |

The ledger records initial HP at spawn and caps cumulative damage reward. Healing,
revival, and duplicate events cannot repeatedly earn the same reward. Splitting,
summons, boss phases, and transformations require explicit lineage/cap tests.
An entity ID without episode/spawn generation is insufficient for deduplication.

Distinguish enemy damage, deal payments, and special character mechanics. Red/soul
half-hearts, mantle hits, and Lost-style health differ. Restrict the initial
character rather than claiming a universal health reward. Measure time penalties
in active game time, not Python steps, so changing action repeat does not silently
change their magnitude.

Progress hypotheses: first room +1, treasure discovery +2, secret +7, super secret
+8, boss +20, floor +35, and target-run completion +250. Define overlaps before
activation, including whether boss rewards combine with ordinary kill bonuses.
Opening and entering secret rooms are separate events; the initial bonus is paid
once on confirmed first entry after a real opening.

## Resources and synergies

Bomb value 0.6, key value 0.8, and coin value 0.1 are early-floor reference points,
not permanent penalties on every use. A resource potential with diminishing
marginal value is a possible approach; test acquisition/spending cycles first.

Item bonuses of 0–3 and synergy bonuses of 2–4 remain disabled. Pickup alone does
not establish utility. A known item pair does not establish that this policy can
use it effectively. Marginal utility needs standardized scenarios covering defense,
mobility, and resources; displayed DPS is insufficient. Test counterfactual builds
outside live runs without rolling back a running episode.

Potential-based shaping, when justified: `gamma * Phi(next) - Phi(current)`.
Use the return discount consistently and handle terminal potentials explicitly.
Changing goals and partial observability require separate analysis; this formula
does not justify arbitrary bonuses.

## Initial bounded-experiment hyperparameters

`configs/training-v1.yaml` proposes learning rate 3e-4, gamma 0.995, GAE 0.95,
clip 0.2, entropy 0.01, rollout 1024, batch 256, five epochs, LSTM 256, one CPU
environment. This is an experiment template, not a runnable Isaac training command.
The actual trainer is a milestone M3 implementation.

Gamma depends on decision frequency. Changing repeat/step duration requires
reviewing the effective horizon, time rewards, and experiment comparability.
Measure rollout duration and expected wall time before long training.

## Evaluation and misleading progress

Split scenario seeds into train, validation, and test before tuning. Never include
test seed identifiers in policy features. For procedural rooms, also consider
layout/enemy/build separation for the intended generalization claim.

Predeclare episode counts, difficulty, character/build, initial health/resources,
action budgets, deterministic/stochastic inference, checkpoint selection, improvement
thresholds, and regression tolerance. Freeze normalization. Compare paired seeds
against baselines and repeat training with several seeds.

Show sample sizes and uncertainty. Binomial intervals can describe success rates;
paired bootstrap can describe appropriate paired differences. Three episodes do
not support strong claims. Count infrastructure faults separately and report their
frequency; do not selectively discard unfavorable episodes.

Required exploit scenarios: repeated entry, heal/damage loops, repeated pickup,
duplicate acknowledgments/events, revived enemies, endless summons, idle/stuck
behavior, paused game, and old IDs after reset. Higher reward with lower clear rate
requires investigation rather than milestone completion.

For secret rooms, match bomb budgets and use a random valid-wall baseline, first
discovery, and success per bomb on unseen maps. For items, compare contextual
outcomes against random and fixed ratings. For complete runs, report wins, depth,
time/resource use, and failure modes. All reports and experiment metadata use English.
