# Evidence: exposed-start-curriculum offline implementation and Windows handoff

- Date/time and timezone: 2026-10-22, local.
- Git revision and dirty status: base `64399c0`; implementation committed locally on
  top (not pushed). Unrelated untracked `errors.txt` and `tools/` were not touched.
- Change scope: OpenSpec `exposed-start-curriculum` tasks 1.1-3.2 (offline code and
  tests). Tasks 4.1-4.3 (Windows gate, native pilot, child reload) remain open.
- Implementation host: macOS over the SMB mount of `D:\isaac`; no game, no
  `Check.ps1`, no native bridge. Python 3.12 venv, `mypy --platform win32`.
- Configuration: `configs/training-live-boundary-v5-pilot.yaml`, hash
  `a0a93c29b588fb2ee4b23e3c19f16c5e4124b97fb312503978a6ada405f13f15`, seed 20,
  schema 2/723, reward `live-firing-v5`.

## Changed files (sha256 at hand-off)

| File | sha256 |
|---|---|
| `src/isaac_threrisaifuture/exposed_start.py` (new) | recompute; see Windows step 1 |
| `src/isaac_threrisaifuture/live.py` | recompute; see Windows step 1 |
| `tests/test_exposed_start.py` (new) | recompute; see Windows step 1 |

Hashes are taken on Windows from the committed revision (line endings may differ
across the SMB mount); the Windows agent records them before freezing the assignment.

## What was implemented

- `exposed_start.PilotCaps`: hashed cap manifest, unchanged design values (300 s
  lease; 45 s startup; 30 s/240-command setup; <=180 s/2048-step learning to the
  absolute target 28416; two frozen phases of <=20 s/64 decisions each; 3000 action
  commands; 9000 progress / 1800 segment updates; 2 GiB output; 128 MiB trace;
  zero faults/retries/death restarts/New Run; training stop at observed health <=1
  half-heart or 4 cumulative half-hearts lost). Construction refuses inconsistent caps.
- `SetupSpec`/`route_step`/`run_setup`: room-83 scripted setup ported from the
  qualified mixed-control branch (`743a655`): one-frame movement, neutral braking until
  speed <=0.1, axis-major route door(560,280) -> (560,200) -> (320,200), never shoots.
  `precheck` refuses without commands on non-Isaac, wrong room/door, non-combat,
  unsupported weapon, blocked measured grid or missing target at (80,200)+-2.
  During setup any session/epoch/room, grid, weapon, target, health loss, terminal
  boundary, missing velocity, rejected command, command cap or deadline refuses,
  releases input and grants no reset/budget. Handoff requires release plus a fresh
  newer snapshot with a clear aligned in-range line to the same target.
- `ExposedStartEnv` (learner boundary, outermost wrapper via `_train_run(wrap=...)`):
  first reset refuses a stale handoff (context, frame not newer, target moved, no clear
  line); observations/rewards/info pass through unchanged; samples are report-only.
  Setup never enters the collector, so it has no rollout entries, reward credit,
  normalizer updates or recurrent carryover; `EventDeriver.begin` sets a fresh HP
  baseline so a wounded target earns no credit. Health stops release and raise
  `CurriculumStop` before the next action; healed damage still counts as loss.
- `branch_checkpoint`: named parent only; verifies v2 manifest hashes; refuses an
  existing child run; stages copy, verifies hashes, moves, publishes `latest.txt`
  last, reloads, re-verifies parent artifacts and pointer, writes
  `seed-20/branch-receipt.json` exclusively. Interrupted copy publishes no pointer.
- `run_pilot` (dispatched from `run_live` when `exposed_start=True`): validates that
  options equal the cap manifest and that the child run starts at the branched parent;
  setup -> learning (`min(lease, +180 s)`) -> frozen parent -> frozen learned child,
  all inside one never-renewed lease. A refused setup reports `learning: not_run`.
  A frozen child without a newly learned checkpoint is `not_run`; the copied initial
  child is never substituted. Writes `logs/exposed-start-phases.json`.
- `run_frozen_phase`: deterministic `CheckpointPolicy`, fresh recurrent start,
  `verify_unchanged()` in `finally`, reconnect if the learner closed the transport,
  optional setup only if `precheck(at_door=False)` passes, else any eligible combat,
  else `not_run`.
- `phase_metrics`/`write_report`: enemy-HP-loss lower bound, half-hearts lost,
  clears, deaths, context changes, old-corner occupancy, 10 s stagnation windows
  (bbox <20 units, no damage/clear/context change), clear-line exposure with its
  denominator, start/end fingerprints; report labelled `observational`.
- `LiveRunOptions.exposed_start`/`exposed_start_parent`: opt-in requires train,
  resume, combat gate, auto/time-dominant navigation, geometry, boundary reward,
  `max_deaths==1`, `max_faults==0`, a session deadline, a parent and
  `0 < combat_trace_bytes <= 128 MiB`. Defaults unchanged.

## Results (macOS pre-gate, not authoritative)

| Check/requirement | Command/scenario | Exit code | Status | Evidence |
|---|---|---|---|---|
| Focused tests | `pytest tests/test_exposed_start.py` (48 tests) | 0 | passed | closed loop 16 seeds; 3-frame non-convergence; refusals; boundary; branch; pilot |
| Lint/format | `ruff check`/`ruff format --check` | 0 | passed | |
| Types | `mypy --platform win32` (66 files) | 0 | passed | |
| Offline suite | `pytest -m "not game"` | 1 | passed except 2 | 1853 passed, 20 skipped; 2 Windows-only failures (`ctypes` `_Input` size, `subprocess.CREATE_NO_WINDOW`) are host-specific, pre-existing |
| Dependencies | `uv pip check` | 0 | passed | |
| OpenSpec | `openspec validate --all --strict` | 0 | passed | 56/56 |
| `scripts/Check.ps1` | Windows | - | not_run | task 4.1 |
| Native pilot | Windows | - | not_run | task 4.2 |

Synthetic closed-loop physics (`v' = 0.8 v + 0.6 u`) is a regression model, not
native physics. Native route evidence remains the mixed-control result (512/512
empirical cases, max 215 commands; old three-frame baseline 0/5).

## Windows handoff (tasks 4.1-4.3)

Read `docs/RUNTIME_AUTHORITY.md` and this section before any game action.

1. **4.1 gate** (from `D:\isaac`, final committed revision):
   `.\scripts\Check.ps1` and `.\scripts\OpenSpec.ps1 validate exposed-start-curriculum --strict`.
   Save complete logs under `reports/local/exposed-start-pilot-20261022/`; record
   `git rev-parse HEAD` and sha256 of the three changed files plus the config. Any
   failure stops; fix offline first.
2. **Branch** (once, offline, before the game starts):
   ```python
   from pathlib import Path
   from isaac_threrisaifuture.exposed_start import branch_checkpoint
   parent = Path("runs/live-boundary-v5-pilot-20261021/seed-20/checkpoints/a0a93c29-s20-t26368")
   branch_checkpoint(parent, Path("runs/live-exposed-start-pilot-20261022"), seed=20,
       cfg_hash="a0a93c29b588fb2ee4b23e3c19f16c5e4124b97fb312503978a6ada405f13f15",
       reward_contract="live-firing-v5", observation_schema=2)
   ```
   Keep the receipt. An existing child root refuses; do not delete or reuse it.
3. **4.2 pilot** (one shot, Continue on file 2, no retry/New Run): a local helper
   under `reports/local/exposed-start-pilot-20261022/` calls `run_live` (the
   `session_runner.worker` does not pass reward/geometry flags) with:
   ```python
   LiveRunOptions(mode="train", out_dir=Path("runs/live-exposed-start-pilot-20261022"),
       config_path=Path("configs/training-live-boundary-v5-pilot.yaml"), seed=20,
       resume=True, steps=28416, minutes=5.0, max_faults=0, max_deaths=1,
       combat_gate=True, auto_navigate=True, navigation_time_dominant=True,
       firing_position_reward=True, boundary_progress_reward=True, combat_geometry=True,
       combat_trace_bytes=128 * 1024**2, combat_progress_updates=9000,
       session_deadline=time.monotonic() + 300, stop_file=<owned stop file>,
       require_initial_isaac=True, exposed_start=True, exposed_start_parent=<parent above>)
   ```
   Match flags to the qualified v5 pilot helper where they differ (launch/port/
   approval), but do not change caps. Preconditions: the Continue state must be the
   measured room-83 door start; otherwise setup refuses and that is the recorded
   outcome. Cleanup per RUNTIME_AUTHORITY (release, observer close, owned game close,
   listener/process check, exact owned approval removal).
4. **4.3 acceptance**: independently reload the newest child checkpoint with
   `CheckpointPolicy`; verify parent `a0a93c29-s20-t26368` artifacts/pointer unchanged
   against the branch receipt; at least one real optimizer update (timesteps > 26368
   in the child manifest); learner-attributed native damage in the learning phase
   (`enemy_hp_loss_lower_bound > 0` after handoff). Publish
   `exposed-start-phases.json` metrics with the observational label. If any required
   evidence is absent, keep 4.3 unchecked and record the blocker.

## Assumptions to verify natively

- Frame ids advance at 60/s (from the 15-frame = 250 ms hold expiry); stagnation and
  `active_seconds` depend on it.
- A frozen-phase reconnect is not checked to return the same game session; the
  report records each phase's start fingerprint instead.
- The combat gate hands off without movement in the settled exposed position; the
  learner's stale-handoff check refuses if it does not.

## Limitations and continuation

Self-review only; no independent review. No native evidence: tasks 4.1-4.3 open.
Comparisons are observational, single-seed and unpaired. Next action: Windows agent
executes the handoff above under its authorization.
