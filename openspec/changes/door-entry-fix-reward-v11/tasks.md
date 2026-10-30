## 1. Implementation

- [x] 1.1 `rewards.py`: `door_shaping_blocked_cost` (>= 0, default 1.0), loader keys for v11,
  version sets, `DEFAULT_CONFIG_V11`, `_graph_cost` uses it for the blocked in-room term and the
  live boss room.
- [x] 1.2 `configs/reward-v11.yaml` with `blocked_cost: 0.0`.
- [x] 1.3 Contract: `training-pure-v4.yaml` `reward_version: 11`; `PURE_REWARD_VERSION = 11`;
  reward contract `pure-v11`; `make_live_env` accepts 1, 9, 10 and 11, default 11.
- [x] 1.4 Tests: `tests/test_reward_v11.py` (blocked cost, room entry, dead end, boss room,
  telescoping, loader); pinned versions and contract hash updated.
- [x] 1.5 Docs: UPDATE_DECISION, AGENTS, RL_DESIGN, TRAINING_SESSION.

- [x] 1.6 `env.py`: a stall returns `terminated=True, truncated=False` to the learner and is the
  reward `terminal`; reports unchanged. Tests in `tests/test_stall_terminal_and_novelty.py`;
  `test_reward_v4.py` expectations updated (the old truncated flag on a stall was a bug).
- [x] 1.7 `novelty_counts.py`, `RewardV4Coefficients.novelty_cross_run`, `cross_run` in
  `reward-v11.yaml`, checkpoint `novelty_counts_file` and hash, load on resume, live wiring
  (frozen table in evaluation). Tests: decay, no reset by cycling, resume, v10 ignores, size.
- [x] 1.8 `Hyperparameters.target_kl`; `training-pure-v4.yaml` n_epochs 10, batch_size 128,
  target_kl 0.03.

## 2. Verification

- [x] 2.1 Offline gate and strict OpenSpec validation.
- [ ] 2.2 Windows `scripts/Check.ps1`; rename `runs\pure-v4` to `runs\pure-v4-reward-v10`;
  one-hour native session with `--initialize`.
- [ ] 2.3 Native 150k steps: exit-start share > 0.8, stall share < 50%, rooms per episode > 2.5.
- [ ] 2.4 Acceptance: compare `episodes.csv` of the reward v11 run with the reward v10 run and
  the reward v9 schema 8 run at equal steps: share of stalls near an open unvisited door
  (`stall_goal_hops` < 1), exit-start share, `rooms_visited` per episode, episodes reaching
  stage 2.
