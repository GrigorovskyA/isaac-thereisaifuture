# Evidence: async-restart-training-regression-20261019-01

- Date/time and timezone: 2026-10-19, UTC (stages 1-4 status published 06:37:29Z; the earlier "finished 06:40Z" line was wrong and is corrected per feedback 1)
- Git revision and dirty status: HEAD 9d14744; dirty only by this task's test files plus
  untracked user file errors.txt (preserved). No commit, push or archive.
- Change scope and acceptance criteria: test-only regression coverage of existing restart,
  gate and training contracts in the real asynchronous exit/start order (subagent.md,
  stages 1-4). No production, mod, config, lock or OpenSpec change.
- Game/mod/bridge versions: not applicable; no game was launched. Production
  mod/observer/main.lua runs in lupa with synthetic stubs.
- Python/package versions: Python 3.12.13, torch 2.14.1 (CPU), stable-baselines3 2.9.0,
  sb3-contrib 2.9.0, lupa 2.8 (macOS arm64).
- Scenario, seeds, budget: synthetic fixtures only; training seed 7, RAW_CONFIG from
  tests/test_checkpoint_policy.py (n_steps 32, 2 updates total, temporary directories).

## Changed files

| File | Change |
|---|---|
| tests/test_lua_observer.py | STUBS: optional deferred scheduler (`DEFERRED_EVENTS`, `SCHEDULE`, `run_due()`); `AUTO_START`/`DISPATCH_EVENTS` unchanged |
| tests/test_async_restart_training.py | New: 31 tests (stages 1-3) |
| docs/EXPERIMENT_GATED_TRAINING_RECHECK_V1_DRAFT.md | New: NOT AUTHORIZED / NOT RUN draft |
| reports/2026-10-19-async-restart-training-regression-offline.md | This report |
| subagent_report.md, agent-status.json | Summary prepend; status |

## Fake/real boundaries

| Component | Real | Synthetic |
|---|---|---|
| Lua observer | production main.lua bytes | Isaac API stubs, fake clock, deferred exit +15 ms / start +111 ms |
| Transport | real LiveClient over loopback ephemeral port (asserted != 9528) in the e2e test | in-process socket shim on the Lua side |
| Backend/gate | real LiveBackend, FaultTolerantEnv, CombatGateEnv, write_readiness | scripted World/AsyncWorld clients in the matrix tests; scripted operator |
| Learner | real CPU RecurrentPPO + VecNormalize via project `train()` and `_train_run` | synthetic game; not Isaac acceptance |

## Results

| Check/requirement | Command/scenario | Exit code | Status | Evidence |
|---|---|---|---|---|
| Stage 1 async real order, one dispatch identity/authority | test_async_real_order_keeps_one_dispatch_identity_and_authority[x2] | 0 | passed | boundary facts after return/exit/start/reconnect |
| Stage 1 diagnostics on/off parity | test_async_order_diagnostics_on_and_off_are_observably_identical[x2] | 0 | passed | portable decoded comparator |
| Stage 2 Lua peer loss at each boundary | test_peer_loss_at_each_boundary[x4] | 0 | passed | after_return: approval_drop; others accepted, attempts=1 |
| Stage 2 delayed/missing confirmation (5 s) | ..._bounded_by_five_seconds[4990,5010,5100,None] | 0 | passed | see table below |
| Stage 2 wall / monotonic lease expiry in transition | 2 tests | 0 | passed | reconnect refused auth=expired / auth=lease; lease not renewed |
| Stage 2 spent attempts, duplicate exit, second start, pending buffer | 4 tests | 0 | passed | counter survives; approval drops; buffered command never applied |
| Stage 2 stale identity after reconnect | 3 params + accepted-hold release test | 0 | passed | old session/replayed sequence close; old epoch rejected; held input None |
| Stage 2 Python gate/backend matrix | 6 tests (AsyncWorld + FakeClock) | 0 | passed | death terminal, stale readiness rejected (replayed, cross_session), faults 0, deadlines restored, queued death terminal |
| Stage 3 loopback e2e through real gate | test_loopback_async_restart_through_the_real_gate_pipeline | 0 | passed | death, reconnect, epoch 2, stale tokens rejected, only releases outside combat, one `restart` command, deadlines unchanged |
| Stage 3 tiny RecurrentPPO across async death | test_tiny_recurrent_ppo_spans_an_async_death_and_resumes_with_lineage | 0 | passed | see learner evidence |
| Stage 3 deadline-interrupted async rollout | test_deadline_interrupted_async_rollout_saves_nothing_and_reports_unsaved | 0 | passed | no latest.txt/manifest; unsaved_steps == combat_decisions == 4 |
| New file repeated runs | `pytest -q tests/test_async_restart_training.py` (x3, random order) | 0 | passed | 31 passed, about 7-9 s |
| Stage 4 mutation discrimination | session-local mutate.py (see below) | 0 | passed | 8/9 caught; 1 equivalent |
| Full macOS gate | `ISAAC_JSON_LUA=~/.cache/isaac-json/json.lua ./scripts/check.sh` | 0 | passed | ruff, format (99 files), mypy (42 files), 1432 passed, 0 skipped, pip check |
| OpenSpec | `openspec validate --all --strict` (pinned local CLI) | 0 | passed | 29 passed, 0 failed |
| Windows Check.ps1 / OpenSpec.ps1 | - | - | not_run | primary reruns on Windows |
| Real game / runtime | - | - | not_run | outside this assignment |

First full-gate run exited 1 on `ruff format --check` for the new file only (one blank
line); fixed with `ruff format`, rerun exit 0. Recorded honestly.

### Delayed confirmation matrix

| Start delay after dispatch | Observed |
|---|---|
| 4990 ms | confirmed restart |
| 5010 ms | unexpected game-start disables restart (no restart_timeout) |
| 5100 ms | render-time restart_timeout |
| none | timeout, reconnect refused auth=inactive |

## RL evaluation / learner evidence (synthetic game, real CPU libraries)

- One 32-step rollout crossed combat, a natural death, the async exit, a reconnect into
  epoch 2 and a fresh handoff: exits 1, connects 1, outcomes include death 1, faults 0.
- Policy decisions = combat_steps = action commands = 32; no command while waiting.
- `VecNormalize.obs_rms.count == 1 + 32` after the first update and `1+32+1+32` after
  resume: wait snapshots (more than handoffs) never reached the normalizer.
- Every observation given to the policy equals `encode(latest.entity_frame).vector`
  (oracle-free encoding).
- Checkpoint t32 reloads (`load_checkpoint`, config hash, seed); resume to t64 produces a
  child with `parent_checkpoint_id` = t32 id.
- Interrupted case: the gate wait cap expires after the async reconnect; no checkpoint,
  `rollout_accounting` reports checkpointed 0 and unsaved 4; input released, client closed.
- This is not a learning-quality result and not Isaac acceptance.

## Mutation discrimination

Baseline SHA-256: main.lua ab68bc29955d89562fe98c1c19fc346c97c4f1df72853a631a365f8a46d794eb;
combat_gate.py ddd750da2377616a03be075ded84757ee049adcd7301dce0be52baca2035c683.
Each mutant was written in place, the new file was run, and the exact original bytes were
restored in `finally`; hashes matched after every mutant and at the end.

| Mutant | Failed tests |
|---|---|
| counter renewed on close (`restart.attempts = 0`) | 11 |
| lease renewed on close (`authority_deadline = nil`) | 3 |
| stale readiness accepted (session check removed) | 2 |
| release removed only from Lua close | 0 (equivalent: unarmed `action_guard` releases) |
| release removed from close and unarmed guard | 1 |
| missing terminal death fact (`player_dead = false`) | 1 |
| changed wire value (`game_epoch` -> `epoch` in ack) | 10 |
| gate `_release` no-op | 1 |
| gate release skipped at terminal/truncation | 1 |

The three release mutants initially survived; that test gap was closed by adding an
accepted-hold peer-loss test and immediate-release assertions (terminal step and a
gate exit in epoch 2).

## Limitations and continuation

- The 2026-10-18 two-start failure is NOT explained or fixed by this work.
- The async order is modelled from one real trace; engine timing variance is unknown.
- macOS results are not Windows proof; no real game ran.
- Harness observation: a scripted World that pauses forever makes a gated step wait out
  the backend timeout in fake ticks while re-reading the request file over SMB (very
  slow, not infinite). Not used in the suite; not judged a production defect.
- Self-review: assertions were not weakened; production bytes unchanged (hashes above);
  only allowed files written.
- Next action: primary review, Windows Check.ps1/OpenSpec.ps1, then decide on the draft
  docs/EXPERIMENT_GATED_TRAINING_RECHECK_V1_DRAFT.md.

## Feedback 1 response (2026-10-19, macOS executor)

Primary review: `reports/2026-10-19-async-restart-training-primary-review.md` (NOT ACCEPTED).

### 1. Windows IPC: BLOCKED (production scope required)

- Cause (from the primary's Windows run): `ScriptedOperator` reads `request.json` while the
  production `combat_gate._write_atomic` (`os.replace`, combat_gate.py:101-104) replaces
  it. On Windows a reader opened without `FILE_SHARE_DELETE` makes the replace fail with
  `PermissionError` (WinError 5); Python's `open` cannot request that share mode.
- The real operator path has the same race: `write_readiness` and the `combat-ready` CLI
  read `request.json` while the gate may rewrite it. The defect is production-relevant, not
  a test artefact.
- Reproducer kept: `test_request_replacement_succeeds_while_the_operator_reads_it` holds an
  open reader and calls the production `_write_atomic`. It is
  `xfail(strict=True, raises=PermissionError)` on win32 only, so a fix turns it into an
  XPASS failure that forces removal of the marker. On macOS it passes (POSIX rename).
- Not done, as instructed: no retries, no removal of the concurrent reader, no longer
  deadlines, no weaker cleanup.
- Dependent acceptance BLOCKED on Windows: the loopback e2e, both production-Lua learner
  tests below, and any live gated run. They are left unmarked so Windows keeps showing the
  real failure.
- Production scope needed (proposal only, not implemented):
  1. `_write_atomic`: bounded retry of `os.replace` on `PermissionError` (winerror 5/32)
     with a short total deadline, then raise the original error.
  2. Readers (`write_readiness`, `combat-ready`, `_wait` reading `ready.json`): treat a
     transient sharing violation as "not yet readable" within their existing poll loop.
  3. Gate `_stop`/cleanup must not mask the first error (chain or re-raise the original).
  4. A Windows test with a concurrent reader/writer loop as acceptance.

### 2. Learner over the real Lua/socket chain

New tests in `tests/test_async_restart_training.py` (the `loop_game` fixture was factored
into a `harness(gate_dir)` context manager; behaviour unchanged):

- `test_tiny_recurrent_ppo_over_production_lua_socket_and_gate`: real CPU `train()` with
  RecurrentPPO + VecNormalize (RAW_CONFIG, seed 7) over production `main.lua` (lupa),
  loopback `LiveClient`, `make_live_env`/`LiveBackend` and `CombatGateEnv`; natural death
  after 10 actions, async exit/start/reconnect, fresh readiness, rollout continues.
  - First run: t32 checkpoint, parent none; 1 death, 0 faults; rejected
    `{replayed: 1, cross_session: 1}`; game_epoch 2; Lua `COMMANDS == ["restart"]`.
  - Instrumentation (`Probe`): wraps `CombatGateEnv._wait`, policy `forward` and
    `predict_values`, `VecNormalize.normalize_obs`, `RecurrentPPO.train`, recording the
    gate state at every call. No learner call happened while waiting; all 32 `forward`
    calls ran in `combat_active`; counts `{forward 32, predict_values 1, train 1,
    normalize_obs 34}` (1 reset + 32 steps + 1 terminal observation, which does not update
    statistics); `obs_rms.count == 33`; recurrent `episode_starts` exactly at [0, 10];
    all 32 actions sent in `combat_active`; encoded observations equal the oracle-free
    encoding.
  - Resume: `LiveBackend.close` closes the listener, so the resume runs in a fresh
    harness (new production Lua, new LiveClient, same gate directory), like a new process.
    `train(resume=True)` to t64; child checkpoint parent == t32 id; counts
    `{forward 32, predict_values 1, train 1, normalize_obs 33}`; `obs_rms.count == 66`;
    0 faults, no death, game_epoch 1 in the new harness.
  - An in-place listener reopen was tried first and abandoned: the reopened listener on a
    new port never received the Lua reconnect within 10 s (Lua logged "Peer disconnected"
    and the game thread stayed alive). Cause not isolated; reopening a closed `LiveClient`
    is not a supported production path, so this is not claimed as a defect.
- `test_interrupted_rollout_over_production_lua_saves_nothing`: `_train_run` with
  `gate_wait_minutes=0.1` over the same chain; the operator answers only epoch 1, death
  after 4 actions. The wait cap expires after the reconnect (last gate `observed` event
  has game_epoch 2): "no new checkpoint", `rollout_accounting` with 0 checkpointed and 4
  unsaved steps, no `latest.txt`/`manifest.json`, one Lua restart, the last command is a
  release.
- Cleanup: the fixture/harness stops both threads in `finally`, joins with 5 s bounds and
  asserts after the `with` block that neither thread is still alive, then that neither
  thread recorded an error.
- The earlier AsyncWorld learner tests are kept as the synthetic-world variant.

### Commands and results (macOS arm64)

| Command | Exit | Result |
| --- | --- | --- |
| `pytest -q tests/test_async_restart_training.py` x3 | 0 | 34 passed each run (21.8-24.2 s) |
| `ruff format` / `ruff check` (test file) | 0 | unchanged / all checks passed |
| `ISAAC_JSON_LUA=... ./scripts/check.sh` | 0 | lint/format/mypy passed; 1435 pytest passed; pip check; OpenSpec 29/29 |
| `openspec validate --all --strict` | 0 | 29 passed, 0 failed |

### Status of checks

- passed (macOS): items in the table above.
- blocked: Windows acceptance of the loopback e2e and both production-Lua learner tests
  (Windows IPC race above); any live gated run.
- not_run: Windows `scripts/Check.ps1` / `scripts/OpenSpec.ps1`; mutation rerun for the
  feedback-1 tests (no production code changed; earlier 8/9 result stands); real game.
