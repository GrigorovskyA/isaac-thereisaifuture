# RL design: pure self-learning

Current since 2026-10-22 (`docs/UPDATE_DECISION.md`, OpenSpec change
`pure-self-learning-v1`). The hinted v1-v5 design is history in
`archive/docs/RL_DESIGN.pre-pure.md`.

## Problem definition

One RecurrentPPO agent (`MlpLstmPolicy`, CPU) plays Repentance+ on file 2 through
the Lua bridge and learns from experience only. It is trained continuously as one
lineage (`pure-v4`; `pure-v3` and older are preserved, not resumed). The long-term goal is Dead God; the honest near-term goal is
learning to damage and kill enemies, survive rooms, pick up items and progress.

Principles:

- Rewards describe outcomes, never technique.
- Observations carry facts, never advice (no clear line, in-range, target choice).
- Exploration comes from an intrinsic novelty bonus, not scripted positioning.
- Every reward term has an exploit test.
- Training reward, optimizer updates and synthetic smoke do not prove better play.

## Observation schema 7 (3863 floats)

| Block | Features |
| --- | --- |
| Player | position, velocity, red/max red/soul hearts, bone containers (9) |
| Inventory | coins, bombs, keys, active item present/ID/charge fraction, card, pill, trinket held (9) |
| Room | room type one-hot (32), stage, stage type, clear flag, 8 open doors, room shape one-hot (12) (55) |
| Enemies, projectiles | nearest-first slots: present, position, velocity, HP fraction (16/32 x 8) |
| Obstacles | nearest-first slots (24 x 19): the 8 slot features plus a class one-hot (rock, marked rock, bomb rock, block, pit, spikes, poop, TNT, fire, wall, other); fireplaces included, wall cells never exported (`wall` unused) |
| Pickups | base slot plus variant class one-hot (12), subtype, shop flag (8 x 22) |
| Collectibles | multi-hot of held collectible IDs 1..1024 |
| Stats | damage, tears per second, range, shot speed, move speed, luck (6, scaled) |
| Tear flags | 16 booleans: spectral, piercing, homing, slow, poison, freeze, split, growing, boomerang, persistent, wiggle, explosive, charm, confusion, burn, bouncing |
| Weapons | 15 weapon-type booleans (tears, Brimstone, laser, knife, bombs, rockets, ...) |
| Own attacks | nearest-first slots for own tears, lasers and knives (16 x 8) |
| Bombs | all bombs with age (4 x 9) |
| Minimap | 13 x 13 level cells x 7 channels (known, visited, current, boss, treasure, shop, other special) plus an off-grid flag for the current room; only rooms the in-game minimap shows or the player visited |
| Stall clock | seconds without progress / stall limit, from the environment (0 without a watchdog) |
| Visited cells | 26 x 14 novelty cells (40 px) of the current room, 1.0 where the player stood during this run, row-major (364) |

Schema 4 had 2038 floats; schema 5 added obstacle classes, room shape, the minimap and the stall
clock (3499); schema 7 appends the visited-cells block (schema 6 had the same block on a grid
that cut every tile in half and was replaced after its native check). Cells are the 40 px floor
tiles counted from the room interior corner (60, 140), so the largest room (2x2) is 26 x 14 cells
and a 1x1 room exactly 13 x 7; smaller rooms and L shapes use the same grid, and positions in
door frames are clipped to the edge cells. Novelty reward cells use the same tiles. The environment builds it from the
player position, the stage and the current minimap room only (never the oracle), keeps it per
(stage, room) for the run, and clears it when a new session or game epoch starts. A room without
a grid position starts empty on every visit. The wire frame stays at schema 5. Messages are bounded at 48 KiB (the larger frames need it). Positions are relative to the player and scaled; values are clipped with a
counter. Oracle data (`room_index`, hidden enemy HP, door targets) is used only for reward and
novelty keys and door labels and never enters the policy vector, normalizer or recurrent state.

## Actions v2

`MultiDiscrete([5, 5, 4])`: move (none/left/right/up/down), shoot (same), use
(none/bomb/active item/pill-card). Each action holds for 6 game updates
(0.2 s; pure-v2 held 3, which made random movement jitter in place). Use
buttons are a one-shot press per accepted command. The use head starts at
P(none)=0.85 and 0.05 for each press (initial logits only, set at fresh model
creation and never on resume; learning may move it anywhere). Commands are bound to
session, epoch, room visit and frame; stale or replayed commands are refused and
input is released on expiry, disconnect, fault and stop.

## Reward v9 (`configs/reward-v9.yaml`)

| Term | Value | Rule |
| --- | --- | --- |
| Enemy damage | 5.0 per full enemy HP | monotonic per enemy; a reported kill of a listed enemy pays its remaining HP once |
| First room clear | 10.0 | per (stage, room) per run |
| First boss room clear | 20.0 | on top of the room clear, on the first clear of a boss room (`room_type` 5) per (stage, room) per run |
| First room visit | 5.0 | per (stage, room) per run; start room free |
| First floor entry | 30.0 | per stage per run; start floor free |
| Health lost | -0.5 per half-heart | |
| Death | -10.0 | terminal |
| Stall restart | -5.0 | once, on the final step of an episode truncated by the stall watchdog; never with death |
| Time | -0.005 per second | active time only |
| Coin / bomb / key | 0.3 / 0.5 / 0.5 | only above the run's peak count; shared cap 10.0 per run |
| New collectible | 5.0 | per item ID per run (reward v3 paid 1.0) |
| Healing | 0.5 per half-heart | only up to health lost earlier in the run |
| Stagnation | -0.25 per second | stall watchdog idle seconds past a 12 s grace, charged in the step that adds them; none after progress resets the clock, for a dead player or without a watchdog (at most -7.0 per episode with the 40 s limit) |
| Novelty | 0.1 | first visit only, per (stage, room, 40-unit cell) per run (about 9 for a full 1x1 room) |
| Door shaping | coefficient 2.0 | potential-based, see below; ledger column `door_shaping` |

There is no reward for using items; item value and synergies must show up through
combat and progress. Ledger columns are logged separately.

Door shaping (the one term that is not an outcome, approved explicitly) follows Ng et al. 1999:
Phi(s) = -coefficient * d / D, with d the distance from the player to the nearest open door
whose room behind it has not been visited this run (oracle doors, reward label only) and D the
diagonal of the room's bounding box (by room shape; the ratio is clipped to 1). Phi is 0 when
the room is not clear or has enemies, when no such door exists, for a dead player and without
door data. A step pays gamma * Phi(s') - Phi(s), with gamma from the training config; a
terminal step (death, truncation) ends in Phi(s') = 0, and the episode start sets the first
Phi(s). On a room change Phi(s) is the old room's last value and Phi(s') the new room's, as
the formula says. A loop that returns to its start nets (gamma - 1) times the sum of Phi over
the loop, at most (1 - gamma) * coefficient per step, and stagnation outweighs that at once.
Reward v9 equals reward v8 except the denser terms above (room visit 5, floor entry 30, boss
clear 20, pickups 0.3 / 0.5 / 0.5 with cap 10 and new collectible 5, novelty 0.1) and door
shaping; stagnation and the 40 s stall limit are unchanged, so a full stall costs at most -12.
After 580k steps under v8, kills and clears per 1000 steps had plateaued, 60-70% of episodes
stalled, 1.9 rooms were visited per episode and floor 2 was never reached; the sum of exploration
terms was small next to damage and penalties. Reward v8 equals reward v7 except for a shorter stall limit (40 s, was 90 s) with the stagnation rate -0.25 per second (was -0.1) and grace 12 s (was 20 s); the cap stays -7.0, so a full stall costs at most -12. After 477k steps the v7 policy was still at random level and 82% of all steps were spent in stalled episodes. Reward v7 equals reward v6 except for the stagnation cost, stall restart -5 (was -10) and health lost -0.5 (was -1); the frozen evaluation showed pure-v4 policies stalling more than random play. Reward v6 keeps the reward v5 coefficients and adds kill credit: a one-shot kill used to pay nothing, because an enemy that dies between snapshots only leaves the oracle list. The observer reports `killed` identities and the event deriver pays the remaining HP once (never more than max HP per enemy). Reward v5 equalled reward v4 except that a stall restart costs -10 (equal to death; was -5, which paid better than fighting in `pure-v3`). Reward v4 to v8 are archived. Reward v2 paid most
for idling (novelty grew like 2*sqrt(n) and a stall restart was free), so it
was replaced and its lineage `pure-v1` retired; its config is in `archive/configs/`.

## Lineages

`pure-v4` restarts with reward v9 and observation schema 7 (OpenSpec change
`dense-exploration-reward-v9`); the reward v8 run is kept as `runs/pure-v4-reward-v8`. Its
checkpoints are refused (reward contract `pure-v8`, schema 5, different contract hash).
`ent_coef` returns to 0.005: the 0.01 trial did not raise entropy and did not help.

`pure-v4` replaces `pure-v3` (OpenSpec change `pure-v4-map-hazards-and-stall`). After 15 hours
and 243k steps `pure-v3` explored more but cleared 0.1-0.2 rooms per episode: stalling paid
better than fighting, the stall clock, obstacle types and the minimap were invisible
([report](../reports/2026-10-23-pure-v3-overnight.md)). `pure-v3` is preserved under `runs/pure-v3`,
its config is in `archive/configs/`, and its checkpoints are refused (schema 4, reward 4,
different contract hash). `gamma` 0.995 and `ent_coef` 0.005 carry over.

`pure-v3` replaced `pure-v2` (OpenSpec change `pure-v3-observation-and-control`). After 23k
`pure-v2` steps (45 updates) the policy was still about 96% of maximum entropy, the
agent could not see its own attacks, bombs, stats or weapon, decisions every 3 game
updates made random movement jitter, and the uniform use head pressed bomb/item/card
on 75% of decisions. `pure-v2` is preserved under `runs/pure-v2` and its config is in
`archive/configs/`; its checkpoints are refused (different contract hash, schema 3).

## Episodes and restarts

One episode is one run. Death terminates it and the mod starts a New Run. The stall
watchdog truncates it after 90 active seconds without progress and sends a
`restart` command. Progress means enemy damage, a room clear, or a fact new for the run:
an unseen room or floor, a counter above its run peak, a new collectible. Walking
between known rooms does not count. Missing snapshots and
disconnects are infrastructure faults, never stalls, and are not learning outcomes.

## Continuous training

`configs/training-pure-v4.yaml` (lineage `pure-v4`): the `contract` section (seed, algorithm, LSTM
size, action repeat, observation/action/reward versions, use-head prior) is the lineage hash;
`hyperparameters` may be tuned between sessions and are recorded per checkpoint.
Weights, optimizer state, normalizer and RNG always resume from `latest`. A
checkpoint is published after every rollout; retention keeps the 5 newest plus
every 200th (about one per 3 h; kept for rollback and frozen comparison). Each episode appends a row to `metrics/episodes.csv` (including use presses,
half-hearts lost, steps to first room exit and first enemy damage). Each optimizer
update appends a row to `metrics/train.csv`: SB3 train statistics (entropy,
policy/value loss, approx KL, clip fraction, explained variance, learning rate,
`n_updates`), the rollout action share per head and the timing (`rollout_seconds`, and `update_seconds` for the pause since the previous rollout). Episode rows also carry `enemies_killed` and `hits_*` (player hits by source), counted by the observer as metrics only.

## Measuring progress

Use `metrics/episodes.csv` trends (damage, rooms cleared, floor reached, deaths,
stall truncations) and separate frozen evaluation (`eval-live`, watchdog off) for
claims. Report denominators, faults and missing coverage. Continue does not
restore identical worlds, so native comparisons are observational.

## Expectations

The game runs in real time at about 9 decisions per second: one million steps is
about 30 hours. Early sessions may show little. Learning item synergies or reaching
Dead God from pure RL on one real-time instance is unlikely; the user accepts this
as a long experiment without guarantees.
