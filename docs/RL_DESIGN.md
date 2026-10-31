# RL design: pure self-learning

Current since 2026-10-22 (`docs/UPDATE_DECISION.md`, OpenSpec change
`pure-self-learning-v1`). The hinted v1-v5 design is history in
`archive/docs/RL_DESIGN.pre-pure.md`.

## Problem definition

One RecurrentPPO agent (`MlpLstmPolicy`, CPU; a shared structured features extractor with 512 outputs feeds the 256-unit actor and critic LSTMs) plays Repentance+ on file 2 through
the Lua bridge and learns from experience only. It is trained continuously as one
lineage (`pure-v4`; `pure-v3` and older are preserved, not resumed). The long-term goal is Dead God; the honest near-term goal is
learning to damage and kill enemies, survive rooms, pick up items and progress.

Principles:

- Rewards describe outcomes, never technique.
- Observations carry facts, never advice (no clear line, in-range, target choice).
- Exploration comes from an intrinsic novelty bonus, not scripted positioning.
- Every reward term has an exploit test.
- Training reward, optimizer updates and synthetic smoke do not prove better play.

## Observation schema 9 (11691 floats)

| Block | Features |
| --- | --- |
| Player | position, velocity, red/max red/soul hearts, bone containers (9) |
| Inventory | coins, bombs, keys, active item present/ID/charge fraction, card, pill, trinket held (9), then the active item block: quality / 4, 8 tag bits and a one-hot of 64 buckets of the item ID, all zero without an active item (73) |
| Room | room type one-hot (32), stage, stage type, clear flag, 8 door slots x 15 (exists, open, locked, target visited, class one-hot of the room behind, 11 classes), room shape one-hot (12) (167) |
| Enemies | nearest-first slots (32 x 78): the 8 slot features plus identity valid, boss, champion, flying, invulnerable, log-scaled max HP and a one-hot of 64 buckets of a stable hash of (entity type, variant); the one-hot into the first linear layer is a learned embedding per kind (a few kinds may share a bucket); current enemy HP stays unknown |
| Projectiles | nearest-first slots: present, position, velocity, HP fraction (64 x 8) |
| Obstacles | nearest-first slots (64 x 24): the 8 slot features plus a class one-hot (rock, marked rock, bomb rock, block, pit, spikes, poop, TNT, fire, trapdoor, crawlspace, pressure plate, lock block, teleporter, wall, other); fireplaces included, wall cells never exported (`wall` unused); the trapdoor is the floor exit; a pressure plate's pressed state is not exported |
| Pickups | base slot plus variant class one-hot (12), subtype, shop flag, then the item block (24 x 99): only for a pedestal collectible, quality / 4, type one-hot (passive, active, familiar), max charges / 12 (clipped), 8 tag bits and a one-hot of 64 buckets of the item ID (zeros for other pickups and empty pedestals) |
| Collectibles | multi-hot of held collectible IDs 1..1024 |
| Stats | damage, tears per second, range, shot speed, move speed, luck (6, scaled) |
| Tear flags | 16 booleans: spectral, piercing, homing, slow, poison, freeze, split, growing, boomerang, persistent, wiggle, explosive, charm, confusion, burn, bouncing |
| Weapons | 15 weapon-type booleans (tears, Brimstone, laser, knife, bombs, rockets, ...) |
| Held tags | 8 counts of held collectibles per item tag (below), count / 3 clipped to 1 |
| Own attacks | nearest-first slots for own tears, lasers and knives (48 x 8) |
| Bombs | nearest bombs with age (8 x 9) |
| Interactables | nearest-first slots (16 x 16): base features plus a class one-hot (slot machine, beggar, blood donation, fortune teller, restock box, crane, other slot, heaven door) |
| Minimap | 13 x 13 level cells x 14 channels (known, visited, current, room class one-hot) plus an off-grid flag for the current room; only rooms the in-game minimap shows or the player visited, the class only when visited or its icon is shown |
| Stall clock | seconds without progress / stall limit, from the environment (0 without a watchdog) |
| Visited cells | 26 x 14 novelty cells (40 px) of the current room, 1.0 where the player stood during this run, row-major (364) |

Schema 4 had 2038 floats; schema 5 added obstacle classes, room shape, the minimap and the stall
clock (3499); schema 7 appended the visited-cells block (3863); schema 8 (9762) adds door facts,
room classes, floor-feature obstacle classes, interactables, enemy identity and larger caps (below); schema 9 (11691) adds item identity and
catalog facts (below) (schema 6 had the same block on a grid
that cut every tile in half and was replaced after its native check). Cells are the 40 px floor
tiles counted from the room interior corner (60, 140), so the largest room (2x2) is 26 x 14 cells
and a 1x1 room exactly 13 x 7; smaller rooms and L shapes use the same grid, and positions in
door frames are clipped to the edge cells. Novelty reward cells use the same tiles. The environment builds it from the
player position, the stage and the current minimap room only (never the oracle), keeps it per
(stage, room) for the run, and clears it when a new session or game epoch starts. A room without
a grid position starts empty on every visit.

Schema 8 caps equal the observer caps (enemy 32, projectile 64, obstacle 64, pickup 24, own
attack 48, bomb 8, interactable 16; the encoder capacity is the same table, nearest first, cut
counts in `source_overflow`). Room classes group `RoomType` values and serve doors and the
minimap: normal (1), boss (5), treasure (4), shop (2), secret (7, 8, 29), curse (10), challenge
(11, 17), devil_angel (14, 15), sacrifice (13), arcade (9), special (all others, such as library,
planetarium, miniboss). A door is a fact the player sees: a door to a secret room that is still
closed is a hidden wall and reads as absent. The wire frame is schema 7 and messages are bounded
at 128 KiB (worst case measured: 81 KB Lua entity frame, 85 KB live snapshot, 111 KB Python
extreme-number case). Episode rows carry `max_<kind>` and `overflow_<kind>` per kind for tuning
the caps (metrics only). Positions are relative to the player and scaled; values are clipped with a
counter. Oracle data (`room_index`, hidden enemy HP, door targets) is used only for reward and
novelty keys and door labels and never enters the policy vector, normalizer or recurrent state.

Schema 9 item identity (OpenSpec change `item-identity-observation-v9`): before it a pedestal
item was one scalar (ID / 1024) and the active item likewise, so the policy could not tell items
apart. Now every pedestal collectible and the active item carry a one-hot of 64 buckets of
`(item_id * 2654435761 mod 2^32) >> 26` (the top bits; never Python's `hash()`; distinct items may
share a bucket, about 11 of 729 per bucket) and facts from the game's ItemConfig: quality 0-4, type
(passive, active, familiar), max charges and eight tag bits. These are catalog facts, not predicted
effects or advice; what each item does is learned. The tags are the transformation sets of the
game, in bit order: GUPPY, FLY, MUSHROOM, SYRINGE, BOB, SPIDER, BABY, MOM (`ItemConfig.TAG_<NAME>`,
read from the game; a missing name reads as no tag). The held tag counts are the number of held
collectibles per tag, the quantity the game itself counts for a transformation. A blind pedestal
(curse of the blind) hides its item: it exports subtype 0 and no facts if `IsBlind()` exists.

## Actions v2

`MultiDiscrete([5, 5, 4])`: move (none/left/right/up/down), shoot (same), use
(none/bomb/active item/pill-card). Each action holds for 6 game updates
(0.2 s; pure-v2 held 3, which made random movement jitter in place). Use
buttons are a one-shot press per accepted command. The use head starts at
P(none)=0.85 and 0.05 for each press (initial logits only, set at fresh model
creation and never on resume; learning may move it anywhere). Commands are bound to
session, epoch, room visit and frame; stale or replayed commands are refused and
input is released on expiry, disconnect, fault and stop.

## Reward v12 (`configs/reward-v12.yaml`; v9 to v11 stay in `configs/`)

| Term | Value | Rule |
| --- | --- | --- |
| Enemy damage | 5.0 per full enemy HP | monotonic per enemy; a reported kill of a listed enemy pays its remaining HP once |
| First room clear | 10.0 | per (stage, room) per run |
| First boss room clear | 20.0 | on top of the room clear, on the first clear of a boss room (`room_type` 5) per (stage, room) per run |
| First room visit | 5.0 | per (stage, room) per run; start room free |
| First floor entry | 30.0 | per stage per run; start floor free |
| Health lost | -0.5 per half-heart | |
| Death | -11.0 | terminal (v11: -10.0) |
| Stall restart | -4.0 | once, on the final step of an episode truncated by the stall watchdog; never with death |
| Time | -0.005 per second | active time only |
| Coin / bomb / key | 0.3 / 0.5 / 0.5 | only above the run's peak count; shared cap 10.0 per run |
| New collectible | 5.0 | per item ID per run (reward v3 paid 1.0) |
| Healing | 0.5 per half-heart | only up to health lost earlier in the run |
| Stagnation | -0.39 per second | stall watchdog idle seconds past a 12 s grace, charged in the step that adds them; none after progress resets the clock, for a dead player or without a watchdog (at most -7.02 per episode with the 30 s limit of `stall.seconds`) |
| Novelty | 0.1 | first visit only, per (stage, room, 40-unit cell) per run (about 9 for a full 1x1 room); v11: 0.1 / sqrt(N), N = runs that first visited the key |
| Door shaping | coefficient 4.0 | potential-based, see below; ledger column `door_shaping` |

There is no reward for using items; item value and synergies must show up through
combat and progress. Ledger columns are logged separately.

Reward v10 (openspec change `graph-door-reward-v10`) equals v9 except that door shaping
(`door_shaping: {coefficient: 2.0, max_hops: 5}`) is graph-aware. After 105k steps under v9, 92%
of the stalls happened in a cleared room and 40% of those had no open door to an unvisited room,
where the v9 term was silent. Phi(s) = -coefficient * cost(s). The ledger keeps, per episode and
floor, the visited rooms (level grid indexes), the usable doors seen from them (not locked, not a
closed secret door; oracle `target`, `usable`, `room_grid`, labels only) and the boss room once
entered. The hop distance H of a room is 0 for an unvisited target of a usable door and for the
boss room, else 1 + the best neighbour, capped at `max_hops`. Outside the boss room cost = the
minimum over usable doors of in_room + H(target), with in_room the distance share d / D to an
open door in a clear room without enemies and the constant 1 otherwise; with no such door cost =
1 + max_hops (no gradient). In the boss room cost = 1 while it is not clear, else the trapdoor
distance share (0 without a trapdoor). Cost 0 without doors data, for a dead player and off the
grid. Max |Phi| = 12. The step formula, terminal handling and the exploit analysis (discounted
sum = -Phi(s0)) are as below and in the change design. A v9 config keeps the v9 potential:

Reward v11 (openspec change `door-entry-fix-reward-v11`) equals v10 plus `door_shaping.blocked_cost`
(0.0), which replaces the constant 1 above (blocked in-room term and live boss room; v10 is 1.0).
After 61k steps under v10, 73% of the stalls (135/184) were in a cleared room within 0.1-0.45
diagonal of an open door to an unvisited room, because entering an uncleared room paid about
-coefficient. Under v11 entering a frontier room costs nothing, a dead end still drops Phi by
coefficient * H, and clearing a room lowers Phi by at most coefficient * d / D (<= 2).

Reward v11 also changes three things, still without a new version number. A stall is terminal
for learning: `env.step` returns terminated (not truncated) for a stall, because a New Run
follows and the stall clock is observed, so SB3 must not bootstrap `gamma * V(s')`; the
terminal Phi = 0 now belongs to a real end. Summaries and `episodes.csv` still say truncated /
stall; other truncations keep bootstrapping. Novelty counts across runs (`novelty.cross_run`):
a first visit pays 0.1 / sqrt(N), N the runs that first visited the (stage, room, cell) key
(0.1, 0.071, 0.058 ...), stored in `novelty_counts.npz` in each checkpoint (reward state, never an
observation). Evidence from v10: 111 of 191 stalls (58%) never left the start room; returns were
-9.0 (1 room, n=111), +4.5 (2 rooms, n=153), +19.3 (3 rooms, n=25). Hyperparameters:
n_epochs 10, batch_size 128, target_kl 0.03 (about 5x more gradient steps per sample).

Reward v12 (openspec change `door-pull-and-short-stall-reward-v12`) equals v11 except door
shaping coefficient 4.0 (was 2.0; max |Phi| = 24), death -11 (was -10), stall restart -4 (was -5),
stagnation -0.39 per second (was -0.25, grace 12 s) and a new required section `stall: {seconds:
30}`, the stall watchdog limit, which is now part of the reward contract (the training config's
`watchdog.stall_seconds` must equal it). After 254k steps under v11 (1180 episodes) exit from the
start room was 88.6% but 64% of the episodes still stalled, floor 2 was never reached, and 56% of
all steps were the idle tail of a stall. Balance: a full stall costs -4 - 0.39 * 18 = -11.02, a
death -11.5 with one half heart of hits and -14 from full health, so a death never pays better
than a stall (under v11 a death at one half heart, -10.5, was cheaper than a stall, -12.3).

Full-batch structured learner (openspec change `full-batch-structured-learner`; reward v12 and
observation schema 9 unchanged). Rewards v9-v12 all plateaued at about 2 rooms per episode
(7-12% of the episodes reached 3+ rooms) although the returns ranked rooms correctly (1 room
-9.9, 2 rooms +3.7, 3 rooms +16.1, 4+ rooms +41.2), so the learner, not the reward, was the
bottleneck. Three changes: `batch_size` = `n_steps` = 1024 (sb3-contrib keeps recurrent
minibatches as contiguous slices, so batch 128 was part of one episode: the per-minibatch
advantage normalization erased the differences between episodes and target_kl stopped after 2-3.5
epochs); `observation_normalization: continuous_only` (`normalization.py`: binary and one-hot
features, listed per index in `encoding.FEATURE_BLOCKS`, are not centred, scaled or clipped, so a
rare bit no longer jumps to about +10); and `policy_features: structured_v1` (`policy.py`: one
MLP shared by all slots of an entity kind with masked mean and max pooling, small CNNs over the
13 x 13 x 14 minimap and the 14 x 26 visited-cell grid, an MLP over the other features, then
Linear -> 512 + ReLU).

Door shaping (the one term that is not an outcome, approved explicitly) follows Ng et al. 1999.
In reward v9: Phi(s) = -coefficient * d / D, with d the distance from the player to the nearest open door
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

`pure-v4` restarts with reward v12, observation schema 9 and a 30 s stall limit (OpenSpec changes
`door-pull-and-short-stall-reward-v12`, `item-identity-observation-v9`, `door-entry-fix-reward-v11`, `graph-door-reward-v10`, `dense-exploration-reward-v9` and `rich-room-observation-v8`); the reward v11 schema 9 run (254k steps) is kept as `runs/pure-v4-reward-v11-schema9`, the reward v10 run (61k steps) as `runs/pure-v4-reward-v10`, the reward v8 run as
`runs/pure-v4-reward-v8`, the reward v9 schema 7 run as `runs/pure-v4-reward-v9-schema7` and the
reward v9 schema 8 run as `runs/pure-v4-reward-v9-schema8`. Their
checkpoints are refused (different contract hash).
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
size, features extractor width `features_dim` and kind `policy_features`, observation
normalization, action repeat, observation/action/reward versions, use-head prior) is the lineage
hash; `hyperparameters` (n_steps 1024, batch size 1024) may be tuned between sessions and are
recorded per checkpoint. The extractor exists because each LSTM applied its input matrix to the
whole observation for every padded step: at observation size 7522 one update took 55 s on CPU.
One full-batch update with the structured extractor takes about 19 s on the development Mac
(`policy.py`, one helper for training, resume, evaluation and the checkpoint policy; the
continuous-only normalizer is saved as `vecnormalize.pkl` and checked on resume and frozen
evaluation). The `live` section (`pause_during_updates`, not
hashed) makes the live backend pause the game with Esc while each update and checkpoint run
(`update_pause.py`); a failed pause is recorded in `events.jsonl` and never faults the session.
Weights, optimizer state, normalizer and RNG always resume from `latest`. A
checkpoint is published after every rollout; retention keeps the 5 newest plus
every 100th (about one per 7 h at n_steps 1024; kept for rollback and frozen comparison). Each episode appends a row to `metrics/episodes.csv` (including use presses,
half-hearts lost, steps to first room exit and first enemy damage). Each optimizer
update appends a row to `metrics/train.csv`: SB3 train statistics (entropy,
policy/value loss, approx KL, clip fraction, explained variance, learning rate,
`n_updates`), the rollout action share per head and the timing (`rollout_seconds`, and `update_seconds` for the gap since the previous rollout, optimizer and checkpoint, and `pause_seconds` / `pause_ok` for the game pause around the update). Episode rows also carry `enemies_killed` and `hits_*` (player hits by source), counted by the observer as metrics only.

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
