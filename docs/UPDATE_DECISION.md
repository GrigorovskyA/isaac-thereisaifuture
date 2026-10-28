# Decision update: change of course to pure self-learning

Date: 2026-10-22 (Europe/Amsterdam). Decided by the user in discussion.
Status: decided direction; implementation not started. No code was changed.
Audience: any agent that continues this project, including the agent that built
the scripted setups.

## Summary

The project changes course. The goal is a **purely self-learning** agent. The
network should learn combat, tear flight, targeting, pickups, item use and
synergies from experience and in-game rewards. It should not rely on scripted
positioning, hand-made geometry features or reward terms that describe *how* to
play.

The previous direction kept adding help: scripted setup, firing-position shaping,
clear-line and range features, boundary support. Each step was well engineered,
but play did not improve. The v4/v5 pilots stayed near a corner or wall (97%+ of
decisions), and STATUS records that correct feedback alone did not remove the
behavior. The user prefers a simpler, honest learning setup and is willing to
wait a long time for results.

## What we keep

- Steam, the native bridge, the Lua observer and the transport and safety rules.
  This includes stale-action rejection, input release, session/frame binding and
  fault versus outcome separation.
- The base entity observation in `src/isaac_threrisaifuture/encoding.py`: player
  position, velocity and health, plus enemies, projectiles, obstacles and pickups
  with position, velocity and HP. This is already raw state without hints.
- The simple combat reward in `configs/reward-v1.yaml`: enemy damage, kills, first
  room clear, health loss, death and a small time cost.
- Lineage, checkpoint, evidence and OpenSpec discipline from AGENTS.md.
- One game instance. Wall time is not a constraint for the user.

## What we stop or remove from the learning path

- Scripted setup before learning (`exposed-start-curriculum`, `exposed_start.py`).
- Geometry policy features (`policy_geometry.py`, observation 2/723 extension):
  clear line, in-range flag and movement clearance.
- Hand-shaped firing rewards (`live-firing-v4`, `live-firing-v5`, firing-position
  and boundary-support shaping).
- Diagnosing and patching the hinted lineage, including
  `docs/tasks/2026-10-22-wall-stagnation-offline.md`. That task is superseded by
  this decision unless the user reopens it.

These modules may stay in the repository as history and diagnostics. They must
not be enabled in the new pure profile. Old checkpoints (723 inputs) are not
compatible with the new profile; the pure profile starts a new lineage from a
fresh model, and old lineages stay preserved.

## Design principles for the pure profile

1. Rewards describe **outcomes**, never technique. Allowed: damage dealt, kills,
   room clear, health lost, death, progress through rooms and floors, pickups.
   Not allowed: "stand in line with the enemy", "keep away from walls" and similar.
2. Exploration comes from an intrinsic signal (for example RND or a visit-count
   bonus), not from scripted positioning. At most one potential-based term is
   acceptable, because it does not change the optimal policy.
   Used since reward v9 (2026-10-28, approved by the user): door shaping, the change in
   distance to the nearest open door into an unexplored room, paid only in a clear room
   as gamma * Phi(s') - Phi(s). It is the only potential-based term; the other v9 terms
   remain outcomes.
3. The agent must see what it needs to learn about, but the observation should
   carry facts, not advice. Pickup types and item IDs are facts; "good target
   here" is advice.
4. Every reward term gets an exploit test: repeated entry, healed damage, item
   drop and re-pickup cycling and resource farming.
5. Reward during training is not proof of better play. Better play is measured on
   frozen evaluation episodes with separate metrics.

## Item and pickup learning (planned)

The user wants the agent to pick up pickups and items and use items depending on
the room, and to learn this by itself.

- Observation needs a new version: pickup type, item ID, coin/bomb/key counts,
  active item ID and charge, held collectibles.
- Actions need a new version: bomb, active item (Space) and card/pill (Q). This
  needs Lua mod and protocol changes. Today actions are only move and shoot in
  four directions (`actions.py`).
- Reward rules:
  - Reward only the first pickup of a given object per run, so drop and re-pickup
    loops give nothing.
  - Coins, bombs and keys: small reward, only on a real counter increase, capped.
  - Hearts: reward only for health actually restored, never more than was lost,
    so the agent cannot profit from losing health and healing.
  - Pedestal items: one equal reward per pickup. Item quality and synergies are
    learned through combat outcomes, not encoded in the reward.
  - No direct reward for using an item. Its value shows up through combat reward.
- Native pickup/use events are not yet verified in the bridge
  (`resource-and-build-policy` task 3.1 is open).

## Watchdog and restarts (planned)

Two different situations, handled differently:

- **Game not responding** (no frames, disconnect). This is an infrastructure
  fault. Restart and mark the episode as a fault; do not use it as a learning
  outcome.
- **Agent stuck**: 90 seconds without enemy damage and without a room change
  while enemies are alive. This is a truncation, not a death. Exit the run and
  press Continue. A room that is not cleared can be retried this way. New Run is
  not used here, so run progress is kept.
- **Death**: start a New Run. The mechanism exists (`post-death-new-run`), but
  `docs/RUNTIME_AUTHORITY.md` currently allows at most 10 death restarts per
  session and requires New Run authority per experiment.
- Hard per-session limits on restarts and on consecutive faults, so a broken mod
  does not loop all night.

Note: Continue does not restore an identical world state, so retried rooms are
similar, not identical.

## Planned order of work

Each step is a separate, small OpenSpec change with measurable acceptance.

1. Pure profile: base observation without geometry, reward-v1, intrinsic
   exploration, no setup. New lineage from a fresh model.
2. Watchdog and restart policy, plus the runtime authority update for long
   sessions with New Run after death.
3. Long run of 1 + 2 and measurement: does the agent learn to damage and kill
   enemies in the first rooms? Compare against a random policy and, if useful,
   against the old hinted v5 profile at the same step count.
4. Observation v3: pickup types, inventory and items.
5. Action v2: bomb, active item, card/pill.
6. Pickup and item rewards with exploit tests.

Items come after combat on purpose: until the agent survives a room, items add
inputs and actions without much benefit.

## Honest expectations

- The game runs in real time at about 9 decisions per second (1606 decisions in
  176 seconds in the last pilot). One million steps is about 30 hours.
- The current models have only about 28 thousand steps. Agents on hard games
  usually need hundreds of millions, so early runs may show little.
- Learning combat in early rooms is plausible with enough time. Learning item
  synergies and reaching Dead God from pure RL on one real-time instance is
  unlikely. The user accepts this as a long experiment without guarantees.

## Open decisions for the user

- Death restart limit for long sessions: unlimited, or a specific number per
  session. Until decided, the current limit of 10 in `docs/RUNTIME_AUTHORITY.md`
  applies.
- Standing New Run authority after death for pure-profile experiments.
- Which first room or enemies to train on. The Basement is the easiest
  environment ([wiki](https://bindingofisaacrebirth.wiki.gg/wiki/Basement)); the
  specific easiest enemy was not confirmed.
- Whether to change the shooting action space. Changing it is a form of help and
  needs an explicit decision.
