# Evidence: combat-experience-gate-20261018-01 (OpenSpec combat-experience-gate-v1)

Executor: macOS external executor (one bounded offline task). Baseline HEAD `548efbc`.
Nothing committed, pushed or archived. **No real-game activity occurred.** No game launch or
connection, approval, save/Cloud/options change, `runs/` model access, or installs.

## Changed paths

| path | change |
|---|---|
| `src/isaac_threrisaifuture/combat_gate.py` | new: `classify`, request/ack models, `CombatGateEnv`, `write_readiness`, stats |
| `src/isaac_threrisaifuture/live.py` | `LiveBackend.latest`/`poll` (read-only, command-free); opt-in `LiveRunOptions.combat_gate`/`gate_wait_minutes`; gate wiring in `_random_run`/`_train_run`; `rollout_accounting` |
| `src/isaac_threrisaifuture/cli.py` | `live --combat-gate --gate-wait-minutes`; new `combat-ready --session-dir [--request]` |
| `tests/test_combat_gate.py` | new: 15 behavioral tests |
| `docs/COMBAT_EXPERIENCE_GATE.md` | new operator guide |
| `docs/LIVE_LOOP.md` | new optional section only |
| `openspec/changes/combat-experience-gate-v1/**` | proposal, design, delta spec, tasks |

Not changed: `training.py` (not needed), existing tests, Lua/mod, rewards, encoding,
checkpoint format, STATUS/ROADMAP/README, dependencies.

## Design summary

- The gate wraps `FaultTolerantEnv`. Its `reset()` is the operator handoff: it releases
  input, issues a nonce request, polls only the latest transport state, and waits for a fresh
  ack plus same-room `combat`. Then it calls the inner reset, which re-baselines the deriver
  and ledger.
- SB3 receives the terminal step normally. `DummyVecEnv` auto-reset blocks inside the wait,
  so a rollout spans several encounters and wait frames are never samples, decisions or
  normalizer updates. `Monitor` sees ordinary episodes.
- One run deadline plus a per-handoff cap (`CombatGateExpired`, a `LiveBudgetExpired`
  subclass: stop, not a fault retry). On stop: release, request `stopped`, summary row,
  client closed via env close.
- Eligibility comes from the oracle and is used for management only. It is never in obs/info,
  the reward or the normalizer.

## Results

| check | command | exit | result |
|---|---|---|---|
| OpenSpec strict, before implementation | `openspec validate combat-experience-gate-v1 --strict` (pinned, `XDG_CONFIG_HOME=.tooling`) | 0 | passed |
| targeted tests | `pytest tests/test_combat_gate.py -q` | 0 | passed, 15/15 |
| mutation check | 9 hand mutations of `combat_gate.py`: ack bypass, cross-room, replay, overflow, room exit, wait cap, not-eligible, predating, release on end | n/a | 9/9 caught (wait-cap mutation by hang/timeout); file restored |
| ruff, format, mypy (win32) | inside `scripts/check.sh` | 0 | passed |
| full macOS precheck | `ISAAC_JSON_LUA=~/.cache/isaac-json/json.lua ./scripts/check.sh` | 0 | passed: 1344 passed, 0 skipped; OpenSpec 28/28 |
| Windows gate | `./scripts/Check.ps1` | n/a | not_run (no Windows; primary-owned) |
| real-game gated run | n/a | n/a | not_run (no runtime authority; primary-owned) |

The first full precheck failed (1 failed): the new wait-cap validation rejected the default
`minutes=0.01` in an existing test. Fixed by validating the cap only when `combat_gate` is set;
default behavior is preserved and a regression assertion was added. Rerun: exit 0.

### Requirement to test mapping (`tests/test_combat_gate.py`)

| scenario | test |
|---|---|
| eligibility incl. overflow, transition, paused, dead, hp 0 | `test_classify_is_conservative` |
| empty start: zero actions/samples; no response, cap, cleanup, no fault retry, stopped request refused | `test_empty_start_without_operator_acts_never_and_stops_at_cap` |
| enemy spawn without ack does not resume | `test_enemy_spawn_does_not_steal_control_without_readiness` |
| valid readiness resumes; unchanged observation; clear terminal reward, release, second handoff with no actions | `test_readiness_resumes_combat_clear_hands_off_and_releases` |
| natural death/restart: terminal death reward, wait, prior-restart ack rejected, new-epoch resume | `test_natural_restart_waits_and_rejects_prior_epoch_readiness` |
| invalid, oversize, stale, predating, future, cross-session/epoch/room, replayed | `test_invalid_stale_replayed_and_mismatched_readiness_is_rejected` |
| ack outside combat rejected | `test_readiness_outside_combat_is_rejected` |
| global deadline during wait: stop, no renewal, no fault | `test_global_deadline_stops_wait_without_renewal` |
| manual damage during the wait not credited | `test_manual_wait_damage_is_not_credited` |
| disconnect reconnects; protocol error stops | `test_disconnect_during_wait_reconnects_and_protocol_error_stops` |
| room change and fault in combat: truncation, release, logged outcome | `test_room_change_and_fault_in_combat_end_segment_and_release` |
| short fights over several handoffs: real RecurrentPPO update and checkpoint; boundaries, terminal rewards, `obs_rms.count`, resume lineage | `test_short_fights_over_handoffs_make_a_real_update_and_checkpoint` |
| interrupted gated rollout: honest `unsaved_steps`, no checkpoint, release and close | `test_interrupted_gated_rollout_reports_unsaved_steps` |
| opt-in default, cap bounds, non-live env refused | `test_gate_is_opt_in_and_wait_cap_is_bounded` |
| CLI `combat-ready` writes only the fixed ack; refusals | `test_combat_ready_command_writes_only_the_fixed_ack` |

The training test checks the following:

- **Checkpoint:** a manifest exists at t32 with parent None.
- **Wait isolation:** the gate saw 32 decisions and at least 5 handoffs, and wait snapshots
  outnumber handoffs. The normalizer count is 1 + 32, so no wait frames reached it.
- **Episode boundaries:** rollout `episode_starts` sit at 0 and at each Monitor episode
  boundary.
- **Rewards:** normalized rewards are positive exactly at terminal clears and negative
  elsewhere.
- **Lineage:** a resumed run to t64 records the t32 parent.

The test harness is a scripted fake client under the real
`LiveBackend`/`IsaacCombatEnv`/`FaultTolerantEnv`/`RewardLedger` stack. The Lua+socket
harness was not reused for the gate: `poll` is covered with the fake client only.

## Real game

not_run. Pending primary-owned checks, run with `--combat-gate` on file 2 after the normal
preflight:

- handoffs and accepted/rejected acks with their reasons;
- wait exposure;
- no action commands while waiting;
- release on clear, death and timeout;
- new-epoch provenance after a natural restart;
- reconnect during a wait;
- operator-wait cap stop.

## RL evaluation (if applicable)

Not applicable. The synthetic RecurrentPPO run proves mechanics only, not play quality.
Seeds do not create matched real scenarios.

## Self-review (not independent)

- **Spec and diff:** every delta requirement maps to code and tests. Defaults are unchanged:
  the gate is built only when `combat_gate=True`, and the existing `budget` records keep
  their text.
- **Oracle separation:** classification reads `snap.oracle` only inside the gate. Obs and
  info are untouched, which the observation-equality test checks.
- **Known limits:**
  - A resume race counts as an extra handoff.
  - `request.json` is rewritten whenever the provenance/eligibility key changes, which can
    flap in combat. Writes stay bounded by those changes.
  - Rooms whose enemies never clear end by timeout.
  - A fight still running after a timeout needs a fresh ack, by design.
  - `rollout_accounting` assumes one environment (`num_envs: 1`), as in the training config.
- **Shared APIs:** `LiveBackend` gained read-only `latest`/`poll`; `start_episode`/`step`
  are unchanged.

## Limitations and continuation

- The primary should rerun Windows `Check.ps1`, review the diff, and decide on a bounded
  real gated run (operator present).
- Not done: eval-live gating, curriculum, reward changes, automatic navigation.


## Feedback 1 response (2026-10-18)

Both blocking findings were fixed. Same task id; nothing committed, pushed or archived; no
real-game activity. Changed paths stay within the allowed list:
`combat_gate.py`, `live.py`, `tests/test_combat_gate.py`, `docs/COMBAT_EXPERIENCE_GATE.md`,
`openspec/changes/combat-experience-gate-v1/**`, this report and `subagent_report.md`.
`training.py` and `cli.py` are unchanged in this round.

### Finding 1: eligibility maintained during combat

- `LiveBackend` gained an opt-in veto hook (`action_gate`, default `None`, so non-gated
  behavior is unchanged) and a `blocked` reason. `step()` evaluates the hook on the current
  state and on every drained queued snapshot after absorbing it, before sending the action:
  - absorbing first keeps the queued damage and kill events;
  - a queued death still returns a terminal death first;
  - a veto withholds the action, sends `release` and waits only for one frame newer than
    the step start.
- After every step the gate also classifies the final state. Any non-combat result
  truncates the segment with `info["gate_exit"]`, releases input and hands off:
  - `empty` (also when the clear flag is still false), `cleared` without the clear event;
  - `ambiguous`, `paused`, `unavailable`;
  - `room_changed`.
  If the action was vetoed, the segment also carries `info["action_withheld"]`.
- No clear or death is fabricated. Kill and damage rewards already observed are kept.
- **Trade-off:** if the clear flag lags enemy deaths past a step boundary, the segment ends
  as `empty` and the clear bonus is not credited.
- **Sample accounting:** a vetoed step remains one SB3 sample (a real observed transition)
  whose action was not executed. It is counted in `withheld_actions`.

### Finding 2: the handoff deadline bounds resume and reconnect

- **Narrowing:** for the whole handoff, the gate sets `run_deadline` on the backend and on
  every wrapper that holds one (`FaultTolerantEnv`) to `min(original, handoff cap)`. Each
  original value is restored on exit, so neither deadline is renewed or widened.
- **What it bounds:** the wait polls, the `poll` reconnect accept timeout, the resume
  `env.reset()` and its `start_episode` reconnect loop all stop at the smaller deadline.
- **Recheck:** both deadlines are rechecked after the inner reset returns, so combat never
  activates after expiry.
- **Error reporting:** a narrowed expiry surfaces as `CombatGateExpired` (cap) or
  `LiveBudgetExpired` (run deadline). Protocol errors are passed through unchanged.
- **Simplification:** the earlier clamp of the cap to the global deadline was redundant
  under `min` (a mutation proved it untested) and was removed.

### Readiness freshness

- The retained latest state is cleared after a disconnect, or after `stale_seconds` with no
  snapshot (default 1 s; the observer samples every 50 ms). The clear is logged as an
  `observed` row with eligibility `unavailable` and counted in `observation_gaps`.
- An ack judged without fresh state is rejected as `no_observation`. A resume race also
  clears the retained state.
- `GateConfig.stale_seconds` must lie in `[poll_seconds, 30]`.

### Commands and results

| check | command | exit | result |
|---|---|---|---|
| OpenSpec strict | `openspec validate combat-experience-gate-v1 --strict` (pinned) | 0 | passed. The first run warned about two long requirements; they were split into separate requirements. |
| targeted tests | `pytest tests/test_combat_gate.py -q` | 0 | passed, 32 (15 existing + 17 new) |
| mutation check | 8 reverts of the fixes (no veto, no post-step check, no narrowing, no post-resume recheck, no gap clearing, no expiry conversion, backend sends anyway, plus the redundant clamp) | n/a | 7/7 applicable caught; the clamp was removed as dead logic |
| full macOS precheck | `ISAAC_JSON_LUA=~/.cache/isaac-json/json.lua ./scripts/check.sh` | 0 | passed: 1362 passed, 0 skipped; ruff, format, mypy (42 files) clean; OpenSpec 28/28 |
| Windows gate | `./scripts/Check.ps1` | n/a | not_run (primary-owned) |
| real gated run | n/a | n/a | not_run (primary-owned) |

### New tests (fake clock and no sleeps where timing matters)

| scenario | test |
|---|---|
| reviewer reproduction 1: eligibility lost inside a step (empty with clear false, overflow). The segment truncates; no clear reward; `step` refused; no next action. | `test_eligibility_lost_within_a_step_ends_segment_before_any_next_action[empty, ambiguous]` |
| ineligible queued snapshot before the next action (empty, overflow, paused, unavailable, room change). No action is sent; queued damage is credited; release; truncation. | `test_ineligible_queued_snapshot_withholds_the_next_action_and_keeps_events[5]` |
| queued death stays a terminal death with no action | `test_queued_death_before_the_next_action_stays_a_terminal_death` |
| honest boundaries and counting through the real `Monitor`/`DummyVecEnv`/`VecNormalize` stack. Two eligibility losses and three handoffs: `obs_rms.count` = 1+8, done flags only at the losses, 7 actions for 8 samples, `withheld_actions` = 1. | `test_eligibility_losses_keep_honest_boundaries_and_normalizer_counts` |
| expiry inside readiness on the fake clock. Both deadlines are restored, not renewed; the request is stopped. | `test_readiness_wait_expires_on_the_fake_clock` |
| reviewer reproduction 2: expiry inside resume. Covers a blocking reconnect loop (bounded to cap + 2 ticks; every accept timeout within the cap), a slow reset and a slow successful return. Both deadlines are narrowed during the reset; combat never activates; state is stopped; no action. | `test_cap_expiry_inside_resume_never_activates_combat[3]` |
| reconnect during the wait. The accept timeout is bounded by the cap; expiry stops the run. | `test_reconnect_during_the_wait_is_bounded_by_the_cap` |
| run deadline expiring inside resume is reported as the run budget, not the cap | `test_global_deadline_inside_resume_is_reported_as_the_run_budget` |
| a retained observation cannot authorize a resume after a silent gap or a disconnect (`no_observation`); a fresh ack then resumes | `test_retained_observation_cannot_authorize_resume_after_a_gap[silence, disconnect]` |
| staleness bounds | `test_gate_config_rejects_staleness_outside_bounds` |

The real synthetic short-fight RecurrentPPO rollout and checkpoint regression is unchanged
and passes.

### Remaining limits

- The tests use only the scripted fake client; the Lua+socket harness is not exercised.
- A pause or unavailable snapshot queued before an action still makes the vetoed step wait
  for one newer playable frame. That wait is bounded by the existing step and pause
  timeouts and the run deadline.
- `stale_seconds` assumes the 50 ms observer sampling. A slower stream would cause more
  `no_observation` rejections, never a stale accept.
- The primary should rerun Windows `Check.ps1` and review the diff before any real gated run.
