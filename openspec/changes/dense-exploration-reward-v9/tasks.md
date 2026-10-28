## 1. Implementation

- [x] 1.1 Lua: `oracle_doors` in the live oracle block (pcall per door, unreadable target is
  explored, unreadable position skips the door); `OracleDoor` and `LiveOracle.doors` (max 8,
  slot 0..7, unique slots, finite coordinates). Lua tests: doors with positions and flags,
  missing target, no doors, worst-case snapshot size.
- [x] 1.2 `configs/reward-v9.yaml`; `configs/reward-v8.yaml` moved to `archive/configs/`;
  `DEFAULT_CONFIG_V9`; loader requires `door_shaping` and `outcome.boss_room_clear_first` for v9
  only; ledger: boss clear bonus, potential-based door shaping with `gamma`, terminal handling,
  `door_shaping` column; env passes doors, enemies and the terminal flag.
- [x] 1.3 Observation schema 6: `VisitedCells` and the 405-float block in `encode`; the env keeps
  the state per run; `OBSERVATION_SCHEMA_VERSION` 6 with `FRAME_SCHEMA_VERSION` 5 for the wire.
- [x] 1.4 Contract: `training-pure-v4.yaml` (schema 6, reward 9, `ent_coef` 0.005);
  `PURE_REWARD_VERSION = 9`; reward contract `pure-v9`; `make_live_env` pays reward 9 with the
  training gamma.
- [x] 1.5 Tests: `tests/test_reward_v9.py`, `tests/test_observation_schema6.py`, door tests in
  `tests/test_lua_live_loop.py`; v4-v8 tests pinned to the archived v8 file; pure-v8 checkpoints
  refused.
- [x] 1.6 Docs: RL_DESIGN, ENTITY_OBSERVATION_PROTOCOL, RUNTIME_AUTHORITY lineage line, README,
  ARCHITECTURE.

## 2. Verification

- [x] 2.1 Full offline gate and strict OpenSpec validation.
- [ ] 2.2 Windows `scripts/Check.ps1`; redeploy the observer mod; rename `runs\pure-v4` to
  `runs\pure-v4-reward-v8`; one-hour native session with `--initialize`; check that
  `col_door_shaping` is nonzero only in cleared rooms without enemies, that the sums over loops
  are near zero, that a boss clear pays 20 once on top of the room clear, and that live
  snapshots stay below the 49152-byte cap.
- [ ] 2.3 Acceptance: the training-side comparison of the first 8 h session, the frozen
  evaluation (two 3600 s sessions of the checkpoint and two of `random-prior` under this
  config, `compare_eval.py --baseline random-prior`) and the `rooms_visited` comparison with the
  reward v8 frozen evaluation (1.89).
