# Design

## Reward v3

| Term | v2 | v3 |
| --- | --- | --- |
| enemy_hp_fraction_total | 2.0 | 5.0 |
| room_clear_first | 3.0 | 10.0 |
| room_first_visit | 1.0 | 3.0 (doors stay closed while enemies live, so room hopping cannot replace fighting) |
| floor_first_entered | 10.0 | 10.0 |
| player_damage_half_heart | -2.0 | -1.0 |
| death | -10.0 | -10.0 |
| stall_restart | none | -5.0 (new column `stall`) |
| time_second | -0.005 | -0.005 |
| pickups | unchanged | unchanged |
| novelty | 0.02/sqrt(n) every visit | 0.02 on the first visit of a cell per run (about 1.8 for a full 1x1 room) |

The stall term is paid once on the final step of an episode truncated with reason
`stall` (the env asks the ledger when it ends the episode). Truncation stays a
truncation for PPO bootstrapping. Ledger v3 replaces v2 in the live env; contract
`pure-v3`, `reward_version: 3`. Reward v2 files move to `archive/`.

With these values a synthetic idle 90 s in an empty start room returns about
-5 + novelty of the cells it reaches (bounded by the room's cell count) - time,
while one full enemy kill plus one heart lost returns about +1 and a first clear
adds 10.

## Episode summary additions

`use_bomb`, `use_active`, `use_pillcard` (steps whose policy action requested that use, not acknowledged presses, per
episode), `half_hearts_lost`, `steps_to_first_exit` (empty if none),
`steps_to_first_damage` (empty if none). Appended to `metrics/episodes.csv`.

## Training statistics

An SB3 callback appends one row per optimizer update cycle to `metrics/train.csv`:
`wall_time`, `timesteps`, `rollout_index`, `learning_rate`, `entropy_loss`,
`policy_gradient_loss`, `value_loss`, `loss`, `approx_kl`, `clip_fraction`,
`explained_variance`, `n_updates`, and the rollout action mix: for each head the
share of each choice (`move_none..move_down`, `shoot_none..shoot_down`,
`use_none, use_bomb, use_active, use_pillcard`). Values come from the model logger
and `rollout_buffer.actions`; missing values stay empty. Writing never blocks or
fails training: errors are logged and the row is skipped.

## Lineage

`configs/training-pure-v2.yaml` = `pure-v1` contract with `reward_version: 3`;
`Start-Pure.cmd` defaults to `runs\pure-v2`. The first session needs
`--initialize`.
