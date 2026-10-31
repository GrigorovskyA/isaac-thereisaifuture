## 1. Implementation

- [x] 1.1 `level_replay.py`: seed validation, `SeedBank` (rank and staleness sampler, plan per
  New Run, runs, eviction, score attribution, save/load).
- [x] 1.2 `learner.py`: per-step run ids from the step info; seed scores from the raw rollout
  advantages before the rollout normalization.
- [x] 1.3 `training.py`: contract `level_replay` (none left out of the hash), `plr_*`
  hyperparameters, the bank saved and restored with checkpoints (`checkpoints.py`).
- [x] 1.4 Wire and client: `seeded_restart_v1`, oracle `run_seed`, command `seed` and kind
  `next_seed` (`live_wire.py`, `actions.py`, `observer_client.py`).
- [x] 1.5 `live.py`: the bank in `LiveBackend` (run seeds, arming, seeded stall restart),
  `make_live_env(level_replay=...)`, the training run negotiates seeded restarts under `plr_v1`.
- [x] 1.6 Lua: capability, `run_seed`, validated seed on `restart`, `next_seed` for the death
  restart, the same guarded dispatch.
- [x] 1.7 `env.py` and `episode_metrics.py`: step info `level_replay_run`, `run_seed` and
  `seed_replayed` columns with the one-time upgrade.
- [x] 1.8 Tests: `tests/test_level_replay.py`, `tests/test_lua_seeded_restart.py`.
- [x] 1.9 Docs: RL_DESIGN, RUNTIME_AUTHORITY, OBSERVATION_PROTOCOL, UPDATE_DECISION, one line in
  STATUS and TRAINING_SESSION.

## 2. Verification

- [x] 2.1 Offline gate (two known macOS-only failures), `scripts/smoke_rl.py`, strict OpenSpec
  validation; the shipped contract hash is still `0399c37d...`.
- [ ] 2.2 Windows: `scripts/Check.ps1` and `scripts/Smoke-RL.ps1`.
- [ ] 2.3 Native: verify the `seed` console command from Lua (`Isaac.ExecuteCommand("seed XXXX
  XXXX")`): it starts the requested seed, `MC_PRE_GAME_EXIT` then `MC_POST_GAME_STARTED` with
  `continued == false` within the 5 s confirmation, `GetStartSeedString()` reports it, no console
  window or prompt stays open, and file 2 is unharmed.
- [ ] 2.4 Native: verify that a plain `restart` after a seeded run starts a fresh random seed (if it
  repeats the seed, the bank counts such runs as replays and the fresh runs must be redesigned).
- [ ] 2.5 Native: verify `GetStartSeedString()` on Repentance+ returns the "XXXX XXXX" form in a
  normal run, and that a seeded death restart and a seeded stall restart both confirm.
- [ ] 2.6 Redeploy the observer mod; plan and launch a `plr_v1` lineage, then compare it with the
  `none` lineage at equal steps (proposal acceptance).
- [ ] 2.7 Archive after acceptance.
