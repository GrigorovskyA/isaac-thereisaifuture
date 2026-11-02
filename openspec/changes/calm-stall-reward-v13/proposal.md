## Why

The E3B lineage (reward v12, contract `db85924f...`) ran 273408 steps (1877 episodes; reports
`reports/2026-11-01-e3b-*.md`). It fought best so far (1.3-1.7 kills and 0.2-0.28 clears per
episode after 175k) but stayed at about 2.0 rooms per episode from 150k on, with 10-21% of the
episodes reaching 3+ rooms and floor 2 never reached.

In its last 900 episodes:

- 63% ended on a stall, and 89% of the stalls (500 of 564) were in a calm room (clear, no
  enemies): 41% a one-door dead end next to the start room, 20% the start room itself (2-3 open
  doors to unexplored rooms) and the rest a cleared room next to an open unexplored door.
- About 51% of all steps were the idle tail of a stall (30 s limit, 3.7 steps per second).
- The policy stayed near random: the mean per-step entropy was 4.0 of at most 4.6 nats (87%) and
  rose from 82% over the run (the reward v11 learner went from 83% to 73%).
- The use head drifted from 85% `none` to about 35%: 33-55 active item presses and 0.42 own bomb
  hits per episode (14% of all hits taken). It gets almost no advantage signal, so the entropy
  bonus walks it to uniform.

A one-door dead end needs no routing information: the only door is the way out. The agent does not
take it because the policy commits to little at all, and half of its experience is standing still.

## What Changes

- Reward v13 (`configs/reward-v13.yaml`; v9 to v12 stay loadable) equals v12 except: new key
  `stall.calm_seconds: 15`, the stall limit while the room is calm, and
  `stagnation.grace_seconds` 3 (was 12; per_second -0.39 unchanged). The run-wide stagnation floor
  is sized for the calm limit: -0.39 * (15 - 3) = -4.68. A room with enemies keeps 30 s.
- `StallWatchdog(calm_seconds=...)`: the limit is the calm one while the last active snapshot was
  calm (oracle `room_clear` with no enemy and no overflow). The stall-clock observation is idle
  time over the current limit. `make_live_env` passes the calm limit from the reward contract.
- New hyperparameter `use_entropy_scale` (pure learner only, not hashed, default 1.0 = upstream):
  the entropy bonus of the use head is scaled by it; move and shoot keep the full `ent_coef`.
  The shipped config sets 0.2.
- `configs/training-pure-v4.yaml`: `reward_version: 13`, `use_entropy_scale: 0.2`;
  `PURE_REWARD_VERSION = 13`. New contract hash `54be12af...`; the E3B run is kept as
  `runs/pure-v4-e3b` and its checkpoints are refused.
- The forever supervisor's disk sampling ignores files that checkpoint retention deletes during
  the walk (one E3B session faulted on `FileNotFoundError` for a pruned checkpoint file).

## Non-goals

- No Lua, observation schema, action or E3B change; no new reward term.
- No change of gamma, GAE lambda, learning rate or `ent_coef` (gamma 0.995 and `ent_coef` 0.01
  were tried earlier and were worse; see the training config comments).
- No routing hint in the observation: door slots already say whether the target was visited, and
  the dead-end case has a single door.

## Acceptance

- Offline gate (`scripts/check.sh` / `Check.ps1`) and strict OpenSpec validation pass.
- Native run against the E3B lineage at equal steps (75k and 150k), from `episodes.csv` and
  `train.csv`: 3+ room share at least 25% from 100k on, rooms per episode above 2.2, stall share
  below 55%, per-step entropy falling below 80% of the maximum, use `none` share above 60%.

## Impact

- `src/isaac_threrisaifuture/{rewards,stall_watchdog,live,learner,training,session_runner}.py`,
  `configs/`, tests, docs.
- Lineage `pure-v4` restarts with `--initialize` (done on Windows).
