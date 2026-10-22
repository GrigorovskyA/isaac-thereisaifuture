# RL design: pure self-learning

Current since 2026-10-22 (`docs/UPDATE_DECISION.md`, OpenSpec change
`pure-self-learning-v1`). The hinted v1-v5 design is history in
`archive/docs/RL_DESIGN.pre-pure.md`.

## Problem definition

One RecurrentPPO agent (`MlpLstmPolicy`, CPU) plays Repentance+ on file 2 through
the Lua bridge and learns from experience only. It is trained continuously as one
lineage (`pure-v1`). The long-term goal is Dead God; the honest near-term goal is
learning to damage and kill enemies, survive rooms, pick up items and progress.

Principles:

- Rewards describe outcomes, never technique.
- Observations carry facts, never advice (no clear line, in-range, target choice).
- Exploration comes from an intrinsic novelty bonus, not scripted positioning.
- Every reward term has an exploit test.
- Training reward, optimizer updates and synthetic smoke do not prove better play.

## Observation schema 3 (1837 floats)

| Block | Features |
| --- | --- |
| Player | position, velocity, red/max red/soul hearts, bone containers (9) |
| Inventory | coins, bombs, keys, active item present/ID/charge fraction, card, pill, trinket held (9) |
| Room | room type one-hot (32), stage, stage type, clear flag, 8 open doors (43) |
| Enemies, projectiles, obstacles | nearest-first slots: present, position, velocity, HP fraction (16/32/24 x 8) |
| Pickups | base slot plus variant class one-hot (12), subtype, shop flag (8 x 22) |
| Collectibles | multi-hot of held collectible IDs 1..1024 |

Positions are relative to the player and scaled; values are clipped with a
counter. Oracle data (`room_index`, hidden enemy HP) is used only for reward and
novelty keys and never enters the policy vector, normalizer or recurrent state.

## Actions v2

`MultiDiscrete([5, 5, 4])`: move (none/left/right/up/down), shoot (same), use
(none/bomb/active item/pill-card). Each action holds for 3 game updates. Use
buttons are a one-shot press per accepted command. Commands are bound to
session, epoch, room visit and frame; stale or replayed commands are refused and
input is released on expiry, disconnect, fault and stop.

## Reward v2 (`configs/reward-v2.yaml`)

| Term | Value | Rule |
| --- | --- | --- |
| Enemy damage | 2.0 per full enemy HP | monotonic per enemy |
| First room clear | 3.0 | per (stage, room) per run |
| First room visit | 1.0 | per (stage, room) per run; start room free |
| First floor entry | 10.0 | per stage per run; start floor free |
| Health lost | -2.0 per half-heart | |
| Death | -10.0 | terminal |
| Time | -0.005 per second | active time only |
| Coin / bomb / key | 0.05 / 0.1 / 0.1 | only above the run's peak count; shared cap 3.0 per run |
| New collectible | 1.0 | per item ID per run |
| Healing | 0.5 per half-heart | only up to health lost earlier in the run |
| Novelty | 0.02 / sqrt(n) | per (stage, room, 40-unit cell) per run |

There is no reward for using items; item value and synergies must show up through
combat and progress. Ledger columns are logged separately.

## Episodes and restarts

One episode is one run. Death terminates it and the mod starts a New Run. The stall
watchdog truncates it after 90 active seconds without progress (damage, room
entry, clear, pickup, floor) and sends a `restart` command. Missing snapshots and
disconnects are infrastructure faults, never stalls, and are not learning outcomes.

## Continuous training

`configs/training-pure-v1.yaml`: the `contract` section (seed, algorithm, LSTM
size, action repeat, observation/action/reward versions) is the lineage hash;
`hyperparameters` may be tuned between sessions and are recorded per checkpoint.
Weights, optimizer state, normalizer and RNG always resume from `latest`. A
checkpoint is published after every rollout; retention keeps the 5 newest plus
every 50th. Each episode appends a row to `metrics/episodes.csv`.

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
