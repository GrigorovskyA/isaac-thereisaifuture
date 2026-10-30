## 1. Implementation

- [x] 1.1 Lua: `oracle_doors` adds `target` and `usable`; the live oracle adds `room_grid`
  (pcall everywhere, -1 when unreadable or off the grid). Lua tests for target, unusable doors
  and `room_grid`.
- [x] 1.2 `OracleDoor.target/usable` and `LiveOracle.room_grid` required; synthetic and test
  producers updated.
- [x] 1.3 `room_graph.py` and the graph potential in `RewardLedgerV4`; `max_hops` in the loader
  (required for v10, forbidden for v9); `configs/reward-v10.yaml`; env passes `room_grid`.
- [x] 1.4 Contract: `training-pure-v4.yaml` `reward_version: 10`; `PURE_REWARD_VERSION = 10`;
  reward contract `pure-v10`; `make_live_env` pays reward 10 with the training gamma.
- [x] 1.5 Metric `stall_goal_hops` with the legacy header upgrade.
- [x] 1.6 Tests: `tests/test_reward_v10.py` (graph potential, telescoping, exploit checks,
  config), Lua door tests, stall column tests; v9 tests unchanged except the pinned version.
- [x] 1.7 Docs: UPDATE_DECISION, AGENTS, RL_DESIGN, TRAINING_SESSION.

## 2. Verification

- [x] 2.1 Offline gate and strict OpenSpec validation.
- [ ] 2.2 Windows `scripts/Check.ps1`; redeploy the observer mod; rename `runs\pure-v4` to
  `runs\pure-v4-reward-v9-schema8`; one-hour native session with `--initialize`; check that
  `target` and `room_grid` are real grid indexes (13 x 13 grid), that locked and secret doors
  read `usable` false, and that live snapshots stay below the 49152-byte cap.
- [ ] 2.3 Acceptance: compare `episodes.csv` of the reward v10 run with the reward v9 schema 8
  run at 30k, 60k and 100k steps: share of stalls in cleared rooms, dead-end share,
  `rooms_visited` per episode, episodes reaching floor 2.
