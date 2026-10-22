# Evidence: frozen-policy-evaluation-20261018-01 (OpenSpec frozen-policy-evaluation-v1)

- Date/time and timezone: 2026-10-18, 16:37-17:10 +02:00.
- Git revision and dirty status: HEAD `4e11d78` (assignment commit on top of `8473302`); tree was
  clean except the unrelated untracked `errors.txt` (preserved, untouched). Nothing committed or pushed.
- Executor: macOS 26.7.1 Copilot CLI agent on the shared SMB checkout `/Volumes/isaac` (= `D:/isaac`).
- Change scope and acceptance criteria: offline frozen RecurrentPPO policy adapter, its tests and the
  predeclared live evaluation plan. Real performance evaluation is not part of acceptance.
- Game/mod/bridge versions: not applicable. No game launch, connection, deployment, training on the
  real game, approval writing, reset or save access occurred. **No real-game inference, control or
  evaluation occurred.**
- Python/package versions: Python 3.12.13, stable-baselines3 2.9.0, sb3-contrib 2.9.0, torch 2.14.1
  (CPU), existing Mac venv; nothing installed.
- Scenario/seeds/budget: synthetic room only (`sim.SyntheticRoomBackend`), test fixture seed 7,
  32 timesteps RecurrentPPO, LSTM 16; regression test seed 1, 64 timesteps.

## Changed files

Allowed by the assignment:

- `src/isaac_threrisaifuture/checkpoint_policy.py` (new): `CheckpointPolicy`, `PolicyIdentity`,
  `InvalidPolicyOutput`.
- `tests/test_checkpoint_policy.py` (new, 29 cases).
- `docs/LIVE_EVALUATION_PLAN.md` (new).
- `openspec/changes/frozen-policy-evaluation-v1/**` (new: proposal, design, tasks, delta spec
  `frozen-policy-evaluation`).
- `reports/2026-10-18-frozen-policy-evaluation-offline.md` (this file), `subagent_report.md`
  (summary prepended), `agent-status.json` (ignored; atomic replace via `agent-status-tmp.json`).

Outside the assignment's list, authorized by the user in chat ("I allow fixing bugs") after the bug
below was found:

- `src/isaac_threrisaifuture/training.py`: `train` wraps each environment in SB3 `Monitor`.
- `tests/test_training_manifest.py`: regression test
  `test_training_survives_episodes_that_finish_inside_a_rollout`.
- `openspec/changes/combat-ppo-training/tasks.md`: task 1.4 records the fix.

## Bug found and fixed: training crashed after the first finished episode

`IsaacCombatEnv` puts its episode summary under `info["episode"]`, the key SB3 reserves for Monitor
statistics. RecurrentPPO calls `_dump_logs` every iteration (`log_interval=1`), which reads
`ep_info["r"]` and raised `KeyError: 'r'` whenever a rollout contained a finished episode. The live
256-step smoke likely passed only because no episode ended inside that rollout; any longer live
training would have crashed after the first death or room clear.

Minimal reproduction on HEAD (before the fix): `train()` with an `IsaacCombatEnv` over
`SyntheticRoomBackend`, `Scenario("toy", "train", 1, 30, enemy_count=1, enemy_hp=7.0)`,
`n_steps=64` -> `KeyError: 'r'` in `stable_baselines3/common/on_policy_algorithm.py:291`.
Fix: `DummyVecEnv([lambda: Monitor(env_factory(seed))])`. Monitor overwrites the key only above the
environment, so `FaultTolerantEnv` episode records and `evaluation.evaluate` (no Monitor) still see
the inner summary. The regression test fails without the fix (1 failed) and passes with it, and it
asserts the inner summary (`outcome`) is still visible below Monitor.

## Results

| Check/requirement | Command/scenario | Exit code | Status | Evidence |
|---|---|---|---|---|
| Targeted tests | `~/.venvs/isaac/bin/python -m pytest tests/test_checkpoint_policy.py -q` | 0 | passed | 29 passed |
| Regression without fix | same regression test with `training.py` stashed | 1 | passed (expected failure) | 1 failed `KeyError: 'r'` |
| Related suites | `pytest tests/test_training_manifest.py tests/test_checkpoint_policy.py tests/test_live_e2e.py tests/test_live.py` | 0 | passed | 65 passed, 1 skipped (no ISAAC_JSON_LUA in that run) |
| Mutation sanity | double normalization; no state clear on reset; `deterministic=False`; no upper action bound | n/a | passed | each mutation caught (1, 1, 3, 1 failures); file restored byte-identical |
| macOS gate | `ISAAC_JSON_LUA=~/.cache/isaac-json/json.lua ./scripts/check.sh` | 0 | passed | ruff clean, 93 files formatted, mypy 40 files clean, 1254 passed, OpenSpec 26/26 |
| OpenSpec change | pinned CLI `validate frozen-policy-evaluation-v1 --strict` | 0 | passed | "Change 'frozen-policy-evaluation-v1' is valid" |
| Windows gate | `./scripts/Check.ps1` | - | not_run | macOS executor; primary must rerun |
| Windows OpenSpec | `./scripts/OpenSpec.ps1 validate --all --strict` | - | not_run | macOS substitute above is not Windows evidence |
| Real-game pilot/comparison | `docs/LIVE_EVALUATION_PLAN.md` parts A/B | - | blocked | no runtime authority; no frozen live runner; no seeded live scenarios |

The macOS gate runs mypy with `--platform win32`; it is a substitute for, not a claim of, Windows success.

## Coverage of required behaviours

- Frozen statistics and single normalization: mean/var/count unchanged after 40 decisions; every
  model input equals one clipped `(obs - mean) / sqrt(var + eps)`; `training` and `norm_reward` false.
- Recurrent carry/reset: first decision after reset gets `state=None` and `episode_start=True`; later
  decisions carry nonzero state; carried state differs from fresh state; reset with a different seed
  reproduces the same action sequence.
- Deterministic mode: every `predict` call has `deterministic=True`; identical evaluator reports twice.
- Unchanged artifacts: hashes of every checkpoint file equal before/after load + 30 decisions + reset;
  `verify_unchanged()` detects an appended byte.
- Compatibility: wrong config hash, wrong seed, observation/action schema mismatch, algorithm `PPO`,
  manifest id != directory, latest-pointer root and pointer file.
- Missing/corrupt: missing manifest/model/normalizer, truncated model zip, garbage pickle/manifest.
- Malformed observations: wrong length, 2-D, NaN, infinity, non-numeric; state not advanced.
- Invalid model outputs (fake model): component 5, -1, three components, float, too short.
- Real round trip: RecurrentPPO + VecNormalize trained and saved by the project `train()` on the
  synthetic room, loaded by the adapter, run through `evaluation.evaluate`.

## RL evaluation

Not applicable: no real evaluation. The synthetic checkpoint is a test fixture only. The private
smoke checkpoint `1f4a187e-s20-t256` was not read, loaded, copied or uploaded.

## Self-review (not independent)

- Spec vs diff: every requirement scenario in the delta spec maps to a test above; the plan section
  maps to `docs/LIVE_EVALUATION_PLAN.md` (no document-existence test, by instruction).
- Heavy imports are inside `_load`/`_spaces_only_env`; module import needs only numpy/pydantic.
- Observations are not range-clipped by the adapter (the env emits [-1, 1]; hp fraction could exceed
  it); only shape and finiteness are enforced. Recorded in design.
- Hashing and loading are not atomic; `verify_unchanged()` after evaluation closes that window.
- Pickle artifacts are trusted-input only; documented in the module docstring and proposal.
- Existing `baselines.py`/`evaluation.py` were not modified.

## Limitations and continuation

- Windows `Check.ps1` and OpenSpec wrapper: not_run here; the primary reruns before acceptance.
- Requests for additional allowed writes: none beyond the user-authorized bug fix listed above.
- Suggested follow-ups for the primary (not done): note the training fix in STATUS; consider
  renaming the env's summary key to avoid the SB3 reserved name in future; a frozen-policy live
  runner needs its own change and runtime approval before Part A of the plan.
- State: superseded by the feedback 1 response below.


## Feedback 1 response (2026-10-18, 17:02-17:20 +02:00)

Primary review (`reports/2026-10-18-frozen-policy-primary-review.md`) found that construction accepted
a saved normalizer with `obs_rms.mean[0] = NaN`. Baseline for this round: HEAD `4e11d78` plus the
uncommitted round-1 diff; the primary's `docs/STATUS.md`, `subagent.md` and review report edits were
left untouched. The training Monitor fix was not reapplied or expanded. No real checkpoint under
`runs/` was read or modified; all corruption used private pytest copies of the synthetic fixture.

Changes (allowed files only):

- `checkpoint_policy.py`: `_validate_normalizer` runs at construction before any inference. It
  requires `norm_obs` and `obs_rms`; mean and variance numeric, shape `(OBSERVATION_SIZE,)`,
  finite; variance >= 0 (zero allowed); statistics count a finite positive number (not bool/str);
  `epsilon` and `clip_obs` finite and positive. Failures are `CheckpointError`; nothing is repaired
  or clamped. `act` now raises `CheckpointError` if the normalized vector is non-finite, before
  `predict`, without advancing recurrent state.
- `tests/test_checkpoint_policy.py`: +22 cases. Corrupt states are written through SB3's own
  `VecNormalize.save` into a private copy (the primary's reproduction path), then construction
  must fail while `RecurrentPPO.predict` is patched to fail if called: mean NaN/inf/shape, variance
  NaN/-inf/negative/shape, count NaN/inf/0/negative/string, epsilon 0/negative/NaN, clip 0/inf/NaN,
  `norm_obs` off. Zero variance loads and yields finite input equal to `(obs - mean) / sqrt(eps)`
  clipped. Non-finite normalized output (NaN, inf) never reaches `predict` and keeps state.
- OpenSpec `frozen-policy-evaluation-v1`: three new scenarios in the delta spec, design decision,
  task 2.4.

| Check | Command | Exit | Status | Evidence |
|---|---|---|---|---|
| Targeted tests | `~/.venvs/isaac/bin/python -m pytest tests/test_checkpoint_policy.py -q -p no:cacheprovider` | 0 | passed | 51 passed |
| Regressions vs pre-feedback code | same, with `_validate_normalizer` replaced by the old shape-only check and the finite guard disabled | 1 | passed (expected failure) | 19 failed, 32 passed; mean-shape and norm-obs-off were already caught; file restored byte-identical (`cmp`) |
| OpenSpec change | pinned CLI `validate frozen-policy-evaluation-v1 --strict` | 0 | passed | valid |
| macOS gate | `ISAAC_JSON_LUA=~/.cache/isaac-json/json.lua ./scripts/check.sh` | 0 | passed | ruff clean, format clean, mypy 40 files, 1276 passed, OpenSpec 26/26 |
| Windows gate | `./scripts/Check.ps1`, `./scripts/OpenSpec.ps1 validate --all --strict` | - | not_run | macOS executor; primary reruns |
| Real-game activity | - | - | not_run | no game, inference on real data, training or approval write |

Self-review: count accepts numpy numeric scalars and Python int/float; RunningMeanStd's default
count (1e-4) is valid. A float64 mean near the representable limit can still overflow during
normalization; that is caught by the finite guard rather than at construction. No real-game
inference, control or evaluation occurred. State: ready_for_review.
