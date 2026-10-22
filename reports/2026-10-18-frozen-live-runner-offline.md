# Evidence: frozen-live-runner-20261018-01 (OpenSpec `frozen-live-pilot-v1`)

- Date/time and timezone: 2026-10-18, Europe/Moscow working time (macOS external executor).
- Git revision and dirty status: baseline `1788515` (e7d6fbc plus assignment commit). Dirty
  paths after this task: `src/isaac_threrisaifuture/live_evaluation.py` (new),
  `src/isaac_threrisaifuture/cli.py` (new `eval-live` subcommand only),
  `tests/test_live_evaluation.py` (new), `docs/FROZEN_LIVE_PILOT.md` (new),
  `docs/LIVE_EVALUATION_PLAN.md`, `openspec/changes/frozen-live-pilot-v1/**` (new), this report,
  `subagent_report.md`, ignored `agent-status.json`. Pre-existing untracked `errors.txt` preserved.
- Change scope and acceptance criteria: attach-only, inference-only live runner for one frozen
  checkpoint or `RandomPolicy`, reusing `LiveClient`/`make_live_env`. Offline acceptance only;
  the real pilot is pending primary-owned runtime evidence.
- Game/mod/bridge versions: not applicable; no game, mod deployment or real socket to Isaac.
- Python/package versions: macOS venv Python 3.12.13, stable-baselines3 2.9.0, sb3-contrib 2.9.0,
  torch 2.14.1 (CPU), lupa with `ISAAC_JSON_LUA=~/.cache/isaac-json/json.lua`.
- Scenario, seeds, budget: synthetic only. Test checkpoint trained by `training.train` on the
  synthetic room (`RAW_CONFIG` of `tests/test_checkpoint_policy.py`, seed 7, 32 timesteps); no
  private real model was read or copied.

## Implementation summary

- `live_evaluation.py`
  - `FrozenLiveOptions` validates policy kind, checkpoint arguments (path + expected config hash
    required for `checkpoint`, forbidden for `random`), integer seeds, steps 1..100000, finite
    minutes in (0, 480], finite accept timeout in (0, 3600], nonnegative fault budget and the
    assistance label. Defaults: 2000 decisions, 6 minutes, 0 faults, `unknown`.
  - `load_policy` loads `CheckpointPolicy` (or `RandomPolicy`) and calls `verify_unchanged()`
    before any socket or log folder exists.
  - `run_frozen_live` fixes one monotonic deadline, then listens with
    `accept_timeout = min(accept_timeout, remaining)`, connects, builds the env with
    `make_live_env(..., run_deadline=deadline, max_faults=..., action_repeat=3)` and loops.
  - Loop: cap check, deadline check, `policy.act`, deadline check again, then `env.step`.
    `attempted` counts started steps, `completed` counts steps without a fault.
    `policy.reset(policy_seed + segment_index)` after every `env.reset()`; no reset after a
    terminal step that also hit the cap.
  - Stop reasons map to statuses: `step_cap`/`deadline` -> `completed` (0),
    `operator_interrupt` -> `interrupted` (0), any recorded fault or `fault`/`protocol_error`
    (also wrapped as `__cause__`)/`policy_error`/`connection_timeout`/`error` -> `failed` (1),
    artifacts changed (re-hashed in `finally`) -> `invalid` (3). Unexpected exceptions are
    re-raised after the final summary is written.
  - `env.close()` in `finally`; the client is a context manager around env creation and reset.
  - `_RecordingClient(LiveClient)` overrides only `connect`/`take`/`drain` to log every hello
    and the latest session/epoch; no protocol code is copied.
- `cli.py`: `eval-live` subcommand. Exit 2 for option/compatibility errors before listening,
  otherwise the result exit code; `--confirmed-save-slot 2` required; no `--launch`/`--resume`.
- Docs: `docs/FROZEN_LIVE_PILOT.md` (operator guide), `docs/LIVE_EVALUATION_PLAN.md` aligned:
  one policy per invocation, no within-session alternation, whole-session assistance label,
  stop before manual input, only `unassisted` sessions in autonomous attribution. Part B and its
  100-episode / +20 pp / multi-seed / held-out criteria unchanged.

## Results

| Check/requirement | Command/scenario | Exit code | Status | Evidence |
|---|---|---|---|---|
| OpenSpec change strict | `openspec validate frozen-live-pilot-v1 --strict` (pinned CLI, macOS) | 0 | passed | "Change 'frozen-live-pilot-v1' is valid" |
| New tests | `pytest tests/test_live_evaluation.py -q` | 0 | passed | 53 passed |
| Mutation sanity | 7 source mutations, each run against the new tests | n/a | passed | all 7 caught: no policy reset, no post-act deadline, no final verify, faults ignored, no cap check, accept not capped, env not closed |
| Full POSIX pre-check | `ISAAC_JSON_LUA=... ./scripts/check.sh` (ruff, format, mypy win32, pytest, OpenSpec) | 0 | passed | 1329 passed, 0 skipped; mypy 41 files clean; OpenSpec 27/27 |
| Windows gate | `./scripts/Check.ps1` | n/a | not_run | macOS host; primary reruns on Windows |
| Synthetic Lua e2e | `test_synthetic_lua_frozen_checkpoint_run`: production `main.lua` in lupa over loopback, frozen synthetic checkpoint, 30 decisions | 0 | passed | completed/step_cap, 30/30, hello logged, oracle only in `oracle.jsonl`; synthetic, not Isaac |
| Real pilot | `eval-live` against Isaac | n/a | not_run | no runtime authority; approval expired; primary-owned |

### Spec mapping (`specs/frozen-live-pilot/spec.md`)

| Requirement | Tests |
|---|---|
| Attach-only inference runner | `test_frozen_checkpoint_never_learns_saves_or_updates_normalizer`, `test_cli_rejects_before_listening` (`--launch`, `--resume`, missing hash, slot 1) |
| Validation before listening | `test_invalid_options_rejected` (20 cases), `test_incompatible_checkpoint_rejected_before_listening`, `test_cli_wrong_checkpoint_hash_exit_2` |
| One absolute deadline and cap | `test_single_absolute_deadline_reaches_env_and_accept`, `test_deadline_during_act_sends_no_action`, `test_deadline_between_steps`, `test_backend_budget_expiry_is_deadline_not_failure`, `test_step_cap_stops_without_extra_action_and_logs_partial_segment`, `test_defaults_are_the_pilot_caps` |
| Policy reset every segment | `test_policy_reset_at_every_segment_including_death_and_fault`, `test_recurrent_state_cleared_on_new_segment` (real RecurrentPPO `episode_start`), `test_no_reset_after_cap_on_terminal_step` |
| Cleanup and identity | `test_step_failures_close_and_summarize` (fault, protocol, interrupt), `test_bad_model_output_stops_and_closes`, `test_reset_failure_closes_everything`, `test_env_creation_failure_closes_client_and_reraises`, `test_accept_timeout_is_a_failure`, `test_artifact_change_during_run_invalidates_result` |
| Private session logs | partial-segment, summary and configuration assertions above; oracle separation in the synthetic Lua test |
| Honest outcomes | `test_tolerated_fault_is_not_success`, `test_cli_exit_code_follows_result`, `test_wrapped_protocol_error_stops_as_protocol_error` |
| Declared operator assistance | `test_defaults_are_the_pilot_caps`, summary/configuration labels, invalid label rejected |

## Real game

Not run. No game launch, connection to the real port, deployment, approval write or training.

## RL evaluation

Not applicable. No policy-quality, ranking, autonomy or progression claim.

## Limitations and continuation

- Checkpoint manifests do not record the training action repeat; the runner uses 3 (equal to
  `configs/training-live-v1.yaml`) and logs it. A checkpoint trained with a different repeat
  would be run with 3; a manifest field would be a separate change.
- Session/epoch per segment is the latest snapshot seen by the client at segment start (logged
  as such), not read from private backend state.
- A deadline reached during a reconnect wait after death ends as `deadline`/`completed`, possibly
  with an unfinished zero-step segment (logged as `stopped`). An accept timeout before any
  connection is `failed`.
- The synthetic Lua run covers connect, steps, logging and oracle separation; death/reconnect
  boundaries in this runner are covered by fakes, and the shared reconnect path by the existing
  `tests/test_live_e2e.py`.
- No shared API bug found; `live.py`, `checkpoint_policy.py`, `training.py` and existing tests
  are unchanged.
- Self-review (not independent): diff limited to allowed paths; old CLI modes unchanged (full
  suite passes); no approval/launch/learn/save path exists in the new module.
- Next action (primary): rerun `scripts/Check.ps1` on Windows, review, then decide whether to
  authorize a bounded runtime pilot under a fresh approval.
