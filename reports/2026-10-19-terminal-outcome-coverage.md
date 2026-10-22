# Evidence: terminal-outcome-coverage-20261019-01 (episode-lifecycle, offline coverage-aware outcomes)

**Final Windows disposition: ACCEPTED OFFLINE after the frozen handoff dated
2026-10-19T19:15:53Z.** The final Windows section at the end supersedes the
intermediate pending/rejected wording below. Task 3.15 is complete (20/27);
tasks 3.6/3.8 and the other five runtime/integration tasks remain open.

**Current status: frozen final handoff for Windows primary feedback 2 (2026-10-19, Europe/Amsterdam); NOT accepted.** Read the section "Final frozen handoff (Windows primary feedback 2)" first: it holds the current tree identity (SHA256), the final metrics decision, the initial-terminal regression cases and the final results. Everything between it and the "Primary Windows review" section is the first-pass and continuation history; where it conflicts with the final section (initial-result handling, test counts, check counts, acceptance), the final section wins. Task 3.15 is unchecked pending primary acceptance; tasks 3.6 and 3.8 stay open; the whole episode-lifecycle change remains open.

**Historical status line (continuation after coordinator feedback 1): ready_for_review; the first pass was needs_input.** First-pass text below is preserved as history. The in-scope offline implementation passed its focused checks, but the new contract turned the `LiveBackend` `cleared`/`timeout` outcomes into `unknown`, which turned three existing tests outside the first allowed-write list red (see "Blocker", now **resolved by the continuation**, see "Continuation (coordinator feedback 1)"). Per the task, no out-of-scope file was edited. Task 3.15 stays unchecked; Windows primary review decides acceptance. No runtime, game, deployment, approval, training, save, Steam Cloud, private log or model was touched.

- Date/time and timezone: 2026-10-19, Europe/Amsterdam (macOS worker, shared SMB checkout).
- Git revision and dirty status: baseline b973a2c (Record passive floor-progression oracle probe), as stated by the task. The worktree already held unrelated edits to AGENTS.md, docs/AGENT_WORKFLOW.md, reports/2026-10-19-oracle-probe-live-runtime.md, subagent.md and subagent_report.md plus untracked errors.txt, scripts/Wait-Change.ps1 and scripts/wait-change.sh; all were preserved and none was touched. No commit, push, archive or Git write. Git use was read-only inspection (`git status --short`, `git diff`, `git diff --check`). `subagent.md`, `agent-status.json`, `subagent_report.md`, `docs/STATUS.md` and `ROADMAP.md` were not modified.
- Change scope and acceptance criteria: finding F1 of `reports/2026-10-19-oracle-event-contract-review.md`. A missing `player_died`/`room_cleared` event must stay unknown instead of becoming a `timeout`, a false death or a false clear. Explicit per-result coverage, conservative whole-episode aggregation, tri-state summary facts, explicit `unknown` outcome.
- Game/mod/bridge versions: not applicable.
- Python/package versions and configuration hash: Python 3.12.13 (`~/.venvs/isaac`), repository-pinned ruff, mypy, pytest; OpenSpec CLI from `~/.cache/isaac-openspec` (pinned local install). No model or configuration hash.
- Scenario, split, seeds, budget, and stop conditions: scripted `StepResult` sequences and the synthetic toy backend (seeds 1..100 in the existing 100-episode test); no learner.

## Final frozen handoff (Windows primary feedback 2)

Re-verification by the file-bus worker on 2026-10-19 21:10-21:15 Europe/Amsterdam (macOS, shared SMB checkout), after reading feedback 2 and inspecting the current files. No source or test file was edited in this pass: inspection found no gap in `episodes.py`, `evaluation.py`, `sim.py` or the four test files, so the hashes below describe the tree as the primary left it. This pass edited only `openspec/changes/episode-lifecycle/tasks.md` (task 3.15 back to unchecked, acceptance wording removed) and this report. No Git operation (`git status`, `git diff` and `git diff --check` were deliberately not run), runtime, game, deployment, approval, training, save, Steam setting, private log, dependency change, nested agent or heartbeat was used. `subagent.md`, `agent-status.json`, `subagent_report.md`, `docs/STATUS.md`, `ROADMAP.md`, `curriculum.py`, thresholds, rewards, training and checkpoint code and the native/Lua wire paths were not edited.

### Final metrics decision (REPORT_VERSION 2)

This is the meaning selected by the coordinator/user (`known_only`). It is **not** Windows primary acceptance.

- `REPORT_VERSION` is 2. `Metrics.valid` counts **known outcomes** only: `valid == cleared + deaths + timeouts`.
- `unknown` is a separate count (`Metrics.unknown`), separate from `faults`. `attempted == valid + unknown + faults`.
- `unknown` is excluded from the death/clear/timeout totals and from the clear-rate and Wilson-interval denominator (`valid`).
- The damage and return means still use **all non-fault episodes**, unknown included (the previous population).
- `unknown` cannot satisfy the existing minimum-valid sample gates (`valid >= min_valid_episodes` in `curriculum.should_advance`/`regression_gate`). Incomplete coverage can therefore delay advancement or regression decisions. The threshold constants and `curriculum.py` are unchanged.
- Metrics are identical to the previous behavior whenever no episode is unknown. A report written with `REPORT_VERSION` 1 has no `unknown` field and is not re-interpreted.

### Initial-terminal regression and spec scenario

- Behavior: `EpisodeController.start()` accepts the initial result (identity and coverage), then raises `EpisodeFault("Episode initial result contains a terminal event")` through the existing release/fault path when the initial result carries `player_died` or `room_cleared`. The controller is stopped, the backend is released, a `FaultRecord` is stored, and no playable reset state, outcome or transition is fabricated (Gymnasium reset has no terminal-transition slot).
- Test: `tests/test_episodes.py::test_terminal_initial_result_faults_and_never_allows_an_action`, 6 cases = coverage `FULL`/`NONE` x kinds `(player_died,)`, `(room_cleared,)`, `(player_died, room_cleared)`. Each case asserts: `EpisodeFault` matching `initial.*terminal`; `running` is false; release called exactly once; exactly one fault recorded; the queued next result is never consumed; a following `step()` raises `RuntimeError` ("No running episode") and still consumes nothing.
- Spec: scenario "Terminal initial result cannot start control" under the requirement "Death and clear resolve only on covered evidence" in `openspec/changes/episode-lifecycle/specs/episode-lifecycle/spec.md`; design paragraph in the "Resolution" subsection of `design.md`.
- Pre-guard reproduction (all six cases failed with DID NOT RAISE on the delivered implementation) was recorded by the Windows primary in the section below; it was not re-run here because that would require removing the guard from `episodes.py`.
- Ruff format: the finding from the first Windows `Check.ps1` is fixed in the current content; `ruff format --check` passes (below).

### Frozen tree identity (SHA256, computed 2026-10-19 21:14 Europe/Amsterdam)

| File | SHA256 |
|---|---|
| src/isaac_threrisaifuture/episodes.py | `e97ab2bd27da467d1189dbc3e14d90f1f7fc4ceb8d86fe4b7f702b52e1890d4e` |
| src/isaac_threrisaifuture/evaluation.py | `5c8935ebed46a7d2d840d14847cb245ecc19c90960445e38f0fd279d189e81fb` |
| src/isaac_threrisaifuture/sim.py | `3d26bb51a2b297be45f169cb2d200b98b5189bcd3a44cddd3b6864642eeec624` |
| tests/test_episodes.py | `29b2afbf9a77e2dc4cd9fb35bd8f703d29fa2afb7b2118fd1c69542427b3baa1` |
| tests/test_evaluation.py | `1ef1fda44d147de138fa8e1f6f3264584e012553589e7beec5b7423ba378067e` |
| tests/test_combat_gate.py | `989d1356977db9bc4eb9056add037dfc0d4e4d52e6132326021deb4efd0ac9d3` |
| tests/test_live_e2e.py | `a2df6c12b24264c61198081c3f53fd3054825588f7377fda33c237565f03182d` |

Command: `shasum -a 256 <the seven paths>`. These are the hashes of the working-tree bytes on the shared checkout; the files are LF (`episodes.py`, `tests/test_episodes.py`), and the OpenSpec `design.md`/`spec.md` are CRLF as before. The hashes were recomputed after the last report edit and were unchanged (see the last row of the results table). Any later write to these files invalidates this handoff.

### Final results (macOS worker, Python 3.12.13, ruff 0.17.1)

| Check | Command | Exit | Status | Result |
|---|---|---:|---|---|
| Initial-terminal regressions | `~/.venvs/isaac/bin/python -m pytest -p no:cacheprovider -q tests/test_episodes.py -k terminal_initial` | 0 | passed | 6 passed, 32 deselected |
| Episodes module | `~/.venvs/isaac/bin/python -m pytest -p no:cacheprovider -q tests/test_episodes.py` | 0 | passed | 38 passed |
| Final focused tests | `ISAAC_JSON_LUA=$HOME/.cache/isaac-json/json.lua ~/.venvs/isaac/bin/python -m pytest -p no:cacheprovider -q tests/test_episodes.py tests/test_evaluation.py tests/test_combat_gate.py tests/test_live_e2e.py` | 0 | passed | 83 passed, 0 skipped, 20.95 s (equals the 83 reported by the primary's targeted Windows run) |
| Ruff check | `~/.venvs/isaac/bin/python -m ruff check --no-cache src tests scripts/smoke_rl.py` | 0 | passed | "All checks passed!" |
| Ruff format | `~/.venvs/isaac/bin/python -m ruff format --no-cache --check src tests scripts/smoke_rl.py` | 0 | passed | 106 files already formatted |
| mypy | `~/.venvs/isaac/bin/python -m mypy --platform win32 --cache-dir <session mypy cache>` | 0 | passed | "Success: no issues found in 44 source files" |
| Strict change validation (after the tasks.md edit) | `XDG_CONFIG_HOME="$PWD/.tooling" OPENSPEC_TELEMETRY=0 node "$HOME/.cache/isaac-openspec/node_modules/@fission-ai/openspec/bin/openspec.js" validate episode-lifecycle --strict` | 0 | passed | "Change 'episode-lifecycle' is valid" (macOS has no PowerShell, so the pinned local CLI replaces `scripts/OpenSpec.ps1`) |
| Full offline suite (supplementary, with Lua JSON shim) | `ISAAC_JSON_LUA=$HOME/.cache/isaac-json/json.lua ~/.venvs/isaac/bin/python -m pytest -p no:cacheprovider -q -m "not game"` | 0 | passed | 1802 passed, 0 failed in 56.26 s. A Mac run is not a substitute for the Windows gate |
| Windows full `scripts/Check.ps1` on this frozen tree | not run here | n/a | not_run | pending primary |
| Windows all-items `scripts/OpenSpec.ps1 validate --all --strict` | not run here | n/a | not_run | pending primary |
| Real game / runtime / training | no runtime authority | n/a | not_run | none authorized |
| Git whitespace and status checks | deliberately not run (Git operations prohibited by this task) | n/a | not_run | none |
| Hash re-verification after the last report edit | `shasum -a 256 <the seven paths>` | 0 | passed | identical to the table above |

### Self-review against feedback 2

- Initial-terminal guard, its six regressions, the spec scenario and the design paragraph are present and consistent; the guard sits after `_accept`, so identity and coverage checks of the initial result still apply, and `_raise_fault` releases and records the fault.
- The metrics decision is stated above and matches `evaluation.summarize` (`valid` = known, `unknown` separate, means over non-fault) and the existing gates (`curriculum.py` reads `valid`; not edited).
- Stale first-pass statements about the initial result and the old acceptance wording were marked as superseded; tasks 3.6, 3.8 and 3.15 are unchecked (the checklist has 8 open items: 3.6, 3.8, 3.15, 4.1, 4.2, 4.3, 5.1, 5.2 versus 19 done).
- Not claimed: native producer, Lua export, runtime eligibility, exhaustive live-event delivery, gameplay validity of approximate live clears, Windows acceptance.

### Limitations and coordination notes

- Live runs (`LiveBackend`, no coverage claim) cannot report `cleared` or `timeout`, only `unknown`; the derived clear event is still rewarded and the truncation uses the existing training bootstrap path. No reward or training code was changed.
- Coordinator-owned files still describe task 3.15 as accepted: `docs/STATUS.md` (top and its task summary), `ROADMAP.md` (coverage-aware terminal outcomes paragraph) and `subagent_report.md`. They conflict with feedback 2 and are for the coordinator/primary to reconcile; this worker did not edit them. The `subagent.md` header line "accepted after Windows primary review; executor writes closed" is likewise stale relative to feedback 2.
- The Windows pass counts in the historical primary section (for example "1802 tests, zero skips") belong to an earlier tree state. The primary will repeat `Check.ps1` and strict validation on this handoff.
- Stop condition: no further writes to the seven hashed files, the spec, design, tasks or this report until primary feedback.

## Changes (first pass and continuation; see the final section for the current tree)

| Path | Change |
|---|---|
| src/isaac_threrisaifuture/episodes.py | `Outcome` gains `"unknown"`; new `TerminalKind`, `TERMINAL_KINDS`, `ALL_TERMINAL_KINDS`. `StepResult` gains `terminal_coverage: frozenset[TerminalKind] = frozenset()` (default unknown) with a runtime check (`ValueError` for a non-frozenset or any other kind). `EpisodeSummary.died`/`room_cleared` become `bool \| None`, default `None`. `EpisodeController` keeps per-episode `_complete` (starts with both kinds, intersected with every accepted result including the initial one) and `_observed` (terminal kinds seen in any accepted result), reset in `start()`. `_outcome` and `_transition` use them (see "Contract as implemented"). `truncated` is true for `timeout` and `unknown`. |
| src/isaac_threrisaifuture/sim.py | `SyntheticRoomBackend` explicitly declares `ALL_TERMINAL_KINDS` on its initial and step results; docstring says why (it generates every event itself). |
| tests/test_episodes.py | First pass: 19 new test cases (33 in the module); the tie and 100-episode tests gained fact assertions. Final tree: 38 tests in the module (the first-pass initial-result test was replaced by six initial-terminal regression cases, see the final section). |
| openspec/changes/episode-lifecycle/specs/episode-lifecycle/spec.md | Scenario "Time limit reached" now requires both kinds explicitly covered; four new requirements (explicit claim; conservative aggregation and tri-state facts; death/clear resolve only on covered evidence; time limit and unknown outcomes) with 11 scenarios, each requirement text under the 500-character strict-validation warning limit. CRLF preserved (545 CRLF, 0 lone LF). |
| openspec/changes/episode-lifecycle/design.md | Outcomes and Summary bullets updated; new section "Terminal outcome coverage (offline subtask 3.15, 2026-10-19)" (contract, resolution table, facts, consumer review, non-claims). CRLF preserved (1005 CRLF, 0 lone LF). |
| openspec/changes/episode-lifecycle/tasks.md | New unchecked task 3.15 only; 3.6 and 3.8 untouched. |
| reports/2026-10-19-terminal-outcome-coverage.md | This report. |

## Contract as implemented

- Coverage is an explicit claim on each `StepResult` for its exact interval; it is never derived from requested/recorded kinds, provenance or an empty `events` tuple (the only reads of `terminal_coverage` are the validation and one intersection in `_accept`).
- Aggregation: `_complete &= result.terminal_coverage` for every accepted result from the initial one onward. A kind that lost coverage in any interval stays incomplete; a later complete interval does not repair it.
- Outcome, first matching row: `player_died` event -> `death` (terminated, any coverage); `room_cleared` event with `player_died` in `_complete` -> `cleared` (terminated); `room_cleared` event otherwise -> `unknown` (truncated, released); scenario limit with both kinds complete and no terminal event observed -> `timeout`; scenario limit otherwise -> `unknown`.
- Unresolved clear: a clear with incomplete death coverage is not reported as `cleared`; it maps to the explicit `unknown` outcome, `terminated=False`, `truncated=True`, and `_transition` releases control and stops the episode as for any other outcome.
- Facts: `True` if the kind was observed in any result, `False` if the kind is complete over the whole episode and never observed, else `None`. Death-over-clear precedence applies to the outcome only; facts follow events.
- Initial result (added after primary review): `start()` accepts the initial result for identity and coverage, then faults with `EpisodeFault("Episode initial result contains a terminal event")` through the existing release/fault path if any terminal event was observed, so no action can follow an already observed death or clear.
- Unchanged: session/epoch/room/frame/event-interval checks, release and fault paths, rewards, checkpoints, models and native wire formats (`env.py`, `rewards.py`, native modules, Lua untouched).

## Required test coverage

| Required case | Test(s) in tests/test_episodes.py |
|---|---|
| Default missing coverage | `test_missing_coverage_defaults_to_unknown_and_never_becomes_a_timeout` |
| Complete no-event timeout | `test_complete_coverage_without_events_is_a_timeout`; existing `test_timeout_truncates_without_terminating` and the 100-episode test on the synthetic backend |
| Partial coverage at the limit | `test_partial_coverage_at_the_limit_is_unknown_with_per_kind_facts` (2 cases) |
| Loss of coverage in a later interval | `test_a_coverage_gap_in_any_interval_makes_the_kind_unknown` (4 cases: last-interval loss, later interval does not repair, initial gap persists, one lost kind) |
| Known death | `test_known_death_needs_no_coverage`; tie test (death wins, both facts observed) |
| Known clear | `test_known_clear_with_complete_coverage` |
| Clear with incomplete death coverage | `test_clear_with_incomplete_death_coverage_is_unknown_and_releases` (2 cases: never covered; lost earlier then complete at the clear interval) |
| Per-kind False versus None | the partial/gap cases above, `test_coverage_is_tracked_per_kind_before_the_episode_ends` (running episode), known-death (clear fact `None`), known-clear (death fact `False`) |
| Release on unknown termination | `test_missing_coverage_...` and the clear-unknown test assert release calls, `running` false and a following `step` raising `RuntimeError` |
| Extra | per-episode reset (`test_a_new_episode_does_not_inherit_the_previous_coverage_gap`), invalid coverage claims rejected (3 cases), synthetic backend declares full coverage; the first-pass "initial-result terminal event blocks a timeout claim" test is **superseded**: a terminal initial result now faults in `start()` (six cases in `test_terminal_initial_result_faults_and_never_allows_an_action`) |

## Results (first pass; historical, superseded by the final section)
| Check/requirement | Command/scenario | Exit code | Status | Evidence |
|---|---|---:|---|---|
| Focused tests | `~/.venvs/isaac/bin/python -m pytest -p no:cacheprovider -q tests/test_episodes.py` | 0 | passed | 33 passed (14 before this change) |
| Ruff check | `~/.venvs/isaac/bin/python -m ruff check --no-cache src tests scripts/smoke_rl.py` | 0 | passed | "All checks passed!" |
| Ruff format | `~/.venvs/isaac/bin/python -m ruff format --no-cache --check src tests scripts/smoke_rl.py` | 0 | passed | 106 files already formatted |
| mypy (public types changed) | `~/.venvs/isaac/bin/python -m mypy --platform win32 --cache-dir <session mypy cache>` | 0 | passed | "Success: no issues found in 44 source files" |
| Whitespace check | `git diff --check` | 0 | passed | No whitespace errors; only the pre-existing CRLF/LF normalization warnings |
| Strict change validation | PowerShell is unavailable on this macOS host, so the repository-pinned CLI: `XDG_CONFIG_HOME="$PWD/.tooling" OPENSPEC_TELEMETRY=0 node "$HOME/.cache/isaac-openspec/node_modules/@fission-ai/openspec/bin/openspec.js" validate episode-lifecycle --strict` | 0 | passed | "Change 'episode-lifecycle' is valid". An earlier draft with one single long requirement failed strict mode (>500-character warning, exit 1); the requirement was split. |
| Full offline suite (no Lua JSON shim) | `~/.venvs/isaac/bin/python -m pytest -p no:cacheprovider -q -m "not game"` | 1 | failed | 1333 passed, 2 failed, 13 skipped. Failures: `tests/test_combat_gate.py::test_readiness_resumes_combat_clear_hands_off_and_releases`, `tests/test_combat_gate.py::test_short_fights_over_handoffs_make_a_real_update_and_checkpoint` |
| Full offline suite (with Lua JSON shim) | same with `ISAAC_JSON_LUA=$HOME/.cache/isaac-json/json.lua` | 1 | failed | 1791 passed, 3 failed: the two above plus `tests/test_live_e2e.py::test_live_loop_rewards_death_restart_and_next_episode` |
| Windows `scripts/Check.ps1`, `scripts/OpenSpec.ps1 validate --all --strict` | not run here | n/a | not_run | Windows primary runs both before acceptance |
| Real game | no runtime access | n/a | not_run | none authorized |

## Blocker (first pass; **resolved by the continuation below**)

The three failures above are caused by this change, not by a flaky or pre-existing condition: `LiveBackend` (src/isaac_threrisaifuture/live.py, outside the allowed-write list) builds `StepResult(frame, events)` from `EventDeriver` frame deltas and declares no coverage, so under the required default (missing coverage = unknown) a derived `room_cleared` event now resolves as `unknown` (truncated, released) instead of `cleared`, and a 1800-update live timeout resolves as `unknown`. The failing assertions expect `terminated and info["outcome"] == "cleared"` (test_combat_gate twice, test_live_e2e once; the latter then steps a finished episode and raises `RuntimeError`). A death event still resolves as `death` in the live path.

Not changed, awaiting a coordinator decision (any of these needs paths outside the allowed list):

1. Keep `LiveBackend` without a coverage claim (recommended by the F2 finding that its frame-delta events are approximate and not exhaustive delivery) and update the three tests to expect `unknown`/truncated for derived clears, plus whichever downstream live consumers (reward/summary/log readers) should treat `unknown` explicitly.
2. Have `live.py` declare coverage for the kinds `EventDeriver` genuinely covers. That is a separate evidence-backed decision about approximate events; this subtask makes none and invents no native coverage.

Either option is runtime-ineligible and leaves tasks 3.6 and 3.8 open. Until one is chosen, live training would see `unknown` truncations in place of clears; do not use the live path for training outcome statistics on this tree.

## Limitations and continuation

- `evaluation.summarize` (out of scope) counts only the exact strings `death`, `cleared`, `timeout`, so `unknown` is excluded from those counts but still counts in the `valid` denominator and clear rate; `EpisodeRecord.outcome` documentation does not list it and there is no dedicated unknown counter. The combat gate tallies it under its own `unknown` key. A follow-up should add an explicit unknown count.
- Facts follow events: a same-interval death and clear now reports `died=True` and `room_cleared=True` with `outcome="death"` (previously `room_cleared=False`). This follows the "positive evidence sets True" rule; only the outcome applies precedence.
- **Superseded (first-pass behavior):** a terminal event inside the initial result used to be recorded without ending the episode, so an action could follow an already observed death or clear. `start()` now rejects such an initial result with `EpisodeFault` (release, recorded fault, no playable state); see the final section.
- Running-episode facts report `False` only for kinds covered so far, so a mid-episode `False` is "no event in the covered history", not a final result.
- Coverage is a trusted backend claim; the controller does not cross-check it against delivered events or against the producer. No native producer, Lua export, runtime eligibility or event-delivery guarantee exists or is implied.
- Process note: the first small constant block in `episodes.py` was inserted with a one-off Python string replacement rather than the edit tool; its content is as the edit tool would have written it and every later change used the edit tool.
- Self-review against the task: every required case has a test; coverage is never inferred; aggregation is intersection-only so it cannot be repaired; `False` requires complete coverage over the whole episode and no observation; unknown is truncated, not terminated, released and excluded from death/clear/timeout counts; identity, fault and release paths, rewards, checkpoints and wire formats are untouched; 3.6 and 3.8 and the new 3.15 stay unchecked; edits stay inside the allowed-write list. The one thing I could not do within that list is keep `LiveBackend` outcomes green, hence `needs_input`.
- Next action (first pass, superseded by the continuation below): Windows primary decides the `LiveBackend`/consumer path above, then runs `scripts/Check.ps1` and `scripts/OpenSpec.ps1 validate --all --strict`.

## Continuation (coordinator feedback 1, 2026-10-19)

Direct file-bus executor, no nested workers, no Git writes. `subagent.md`, `agent-status.json`, `subagent_report.md`, `docs/STATUS.md` and `ROADMAP.md` were not touched; `live.py`, `benchmark.py`, `curriculum.py`, `spectator.py`, rewards, training and checkpoint code were reviewed read-only and not edited. The first pass's implementation and coverage tests are kept unchanged; `episodes.py`, `sim.py` and `tests/test_episodes.py` needed no further edit.

### Coordinator decision (applied)

- `LiveBackend` stays without terminal coverage: its `EventDeriver` facts are frame-delta-derived, not exhaustive event delivery. `live.py` was not edited and no coverage is asserted to restore the old `cleared`/`timeout` labels. Option 1 of the first-pass blocker is chosen; option 2 is declined.
- The conservative first-pass rules are unchanged. Positive `player_died` stays `death`; an unresolved clear/death precedence is `unknown`, truncated (not terminated), control released.
- `unknown` is explicit in `EpisodeRecord` and evaluation metrics; faults stay distinct. Threshold constants, reward implementation, training code and checkpoint/model data are unchanged. By the coordinator's explicit `known_only` choice (2026-10-19), existing minimum-valid sample gates count only known outcomes; unknown episodes therefore do not satisfy those gates and can delay advancement or regression decisions when coverage is incomplete.

### Changes in the continuation

| Path | Change |
|---|---|
| src/isaac_threrisaifuture/evaluation.py | `EpisodeRecord.outcome` documents `death \| cleared \| timeout \| unknown \| fault`. `Metrics` gains `unknown` (between `timeouts` and `faults`) and a docstring with the invariants `attempted == valid + unknown + faults` and `valid == cleared + deaths + timeouts`. `summarize`: `valid` is now the known-outcome count and the only denominator of `clear_rate` and `wilson_interval`; `unknown` is counted separately from `faults`; the damage/return means still divide by the whole non-fault population (unknown included), exactly the previous population. `REPORT_VERSION` 1 -> 2. Module docstring updated. `_run_episode` needed no change (`unknown` flows from `info["episode"]["outcome"]`; the episode is truncated so the loop ends without stepping again). |
| tests/test_evaluation.py | New: `test_summarize_keeps_unknown_out_of_categories_rates_and_faults` (mixed cleared/death/unknown/fault: separate counts, invariants, rate and Wilson over known only, means over non-fault), `test_only_unknown_episodes_give_no_rate_evidence` (valid 0, rate 0.0, CI (0.0, 1.0), means over non-fault), `test_uncovered_backend_reports_unknown_not_clears_and_json_round_trips` (end-to-end `evaluate` over a no-coverage subclass of the toy room: no cleared/timeout, no faults, report version 2, JSON round trip, per-scenario `unknown`). The existing summarize test now also asserts `unknown == 0`. |
| tests/test_combat_gate.py | `test_readiness_resumes_combat_clear_hands_off_and_releases`: the derived clear now expects `truncated`, not `terminated`, `outcome == "unknown"`, `episode.room_cleared is True`, `episode.died is None`, a `RuntimeError` for a step after the end (no step of an ended episode), and `stats.outcomes == {"unknown": 1}`; reward and release assertions unchanged. `test_short_fights_over_handoffs_make_a_real_update_and_checkpoint`: the episode count equals `outcomes["unknown"]` (and `outcomes["cleared"]` is 0); all other assertions (normalizer, rollout starts, reward signs, resume lineage) unchanged and still pass. |
| tests/test_live_e2e.py | `test_live_loop_rewards_death_restart_and_next_episode`: the derived clear loop stops on `terminated or truncated` and asserts truncated, not terminated, `outcome == "unknown"`, `room_cleared is True`, `died is None` (so the ended episode is not stepped again); the death half (positive `player_died`) still expects `death`, and the death loop also stops on `truncated`. |
| openspec/changes/episode-lifecycle/specs/episode-lifecycle/spec.md | New requirement "Evaluation metrics keep unknown outcomes separate" (under 500 characters) with three scenarios: unknown and fault in one evaluation, only unknown episodes, uncovered backend through the evaluation loop. CRLF preserved (all 560 lines). |
| openspec/changes/episode-lifecycle/design.md | "Consumers" section rewritten for the decision: `LiveBackend` intentionally uncovered, `unknown` metric shape, `valid` semantics, report version, benchmark limitation. CRLF preserved (all 1016 lines). |
| openspec/changes/episode-lifecycle/tasks.md | Task 3.15 description extended; it stays unchecked (3.6 and 3.8 untouched). |
| reports/2026-10-19-terminal-outcome-coverage.md | Status, blocker marker, this section. |

### Design choice resolved: `valid` means known outcomes (2026-10-19)

The coordinator selected `known_only`. `valid` is the known-outcome count because the unchanged consumers read it as the sample size behind `clear_rate` and its interval: `curriculum.should_advance` (`valid >= min_valid_episodes` with the Wilson lower bound), `curriculum.regression_gate` (`too few valid episodes`) and `spectator._read_eval` (`eval_episodes`). Unknown episodes do not satisfy the existing minimum-valid sample gates, so incomplete coverage can delay advancement or regression decisions; threshold constants and gate implementations are unchanged. Damage and return means still cover the entire non-fault population, including unknown episodes. Metrics are identical to the previous behavior whenever no episode is unknown.

### Consumer review (read-only for out-of-scope modules)

| Consumer | Behavior with `unknown` | Action |
|---|---|---|
| `env.py` | forwards `outcome`, `terminated`, `truncated`; emits `info["episode"]` for any non-null outcome | none |
| `combat_gate.py` | `outcomes` tally uses `info["outcome"]` as a key, so `unknown` is its own key; no cleared/timeout assumption | none; tests updated |
| `curriculum.py` | reads `valid`, `clear_rate`, `clear_rate_ci95`, damage mean; consistent under the `valid` choice above | none |
| `spectator.py` | reads `overall.clear_rate` and `overall.valid` from a report; older v1 reports without `unknown` still parse | none |
| `benchmark.py` | counts `outcomes[str(info["outcome"])]`; `clear_rate = cleared / episodes` with `episodes = sum(outcomes)`, so an `unknown` episode would be in its denominator. Its backend is `SyntheticRoomBackend` (complete coverage), so `unknown` cannot occur today | not edited; needs a separate path if an uncovered backend is ever benchmarked |
| rewards / `env.py` accountant | rewards come from delivered events regardless of the label, so a derived live clear event is still rewarded although the episode is `unknown` | not changed (out of scope); disclosed |
| training (SB3 via `FaultTolerantEnv`) | an `unknown` end is a truncation, so live-style training would bootstrap the final value instead of treating the clear as terminal; the updated training test still passes with the same reward-sign assertions | not changed; disclosed |
| live evaluation (`live_evaluation.py`) | `segment.end = str(info.get("outcome") or "truncated")`, so a live segment label becomes `unknown` | not edited; disclosed |
| `fullrun.py` / `floors.py` | own outcome enums, not fed by `EpisodeController.outcome`; unaffected | none |

No consumer other than `benchmark.py` needs a new path to stay correct; none was edited.

### Continuation results (historical, superseded by the final section)
| Check/requirement | Command/scenario | Exit code | Status | Evidence |
|---|---|---:|---|---|
| Focused tests | `ISAAC_JSON_LUA=$HOME/.cache/isaac-json/json.lua ~/.venvs/isaac/bin/python -m pytest -p no:cacheprovider -q tests/test_episodes.py tests/test_evaluation.py tests/test_combat_gate.py tests/test_live_e2e.py` | 0 | passed | 78 passed |
| Related consumers | same runner on `tests/test_evaluation.py tests/test_episodes.py tests/test_curriculum.py tests/test_spectator.py tests/test_checkpoint_policy.py` | 0 | passed | 107 passed |
| Full offline suite, no Lua JSON shim | `~/.venvs/isaac/bin/python -m pytest -p no:cacheprovider -q -m "not game"` | 0 | passed | 1338 passed, 13 skipped (`tests/test_lua_observer.py`; `tests/test_live_e2e.py` is also skipped without the shim) |
| Full offline suite, with Lua JSON shim | same with `ISAAC_JSON_LUA=$HOME/.cache/isaac-json/json.lua` | 0 | passed | 1797 passed, 0 failed (previously 1791 + 3 failed) |
| Ruff check | `~/.venvs/isaac/bin/python -m ruff check --no-cache src tests scripts/smoke_rl.py` | 0 | passed | "All checks passed!" |
| Ruff format | `~/.venvs/isaac/bin/python -m ruff format --no-cache --check src tests scripts/smoke_rl.py` | 0 | passed | 106 files already formatted |
| mypy (public types changed) | `~/.venvs/isaac/bin/python -m mypy --platform win32 --cache-dir <session mypy cache>` | 0 | passed | "Success: no issues found in 44 source files" |
| Whitespace check | `git diff --check` | 0 | passed | no whitespace errors; only the pre-existing CRLF/LF normalization warnings |
| Strict change validation | `XDG_CONFIG_HOME="$PWD/.tooling" OPENSPEC_TELEMETRY=0 node "$HOME/.cache/isaac-openspec/node_modules/@fission-ai/openspec/bin/openspec.js" validate episode-lifecycle --strict` | 0 | passed | "Change 'episode-lifecycle' is valid" |
| Windows `scripts/Check.ps1`, `scripts/OpenSpec.ps1 validate --all --strict` | not run here | n/a | not_run | Windows primary runs both before acceptance |
| Real game | no runtime access | n/a | not_run | none authorized |

### Limitations after the continuation

- The original blocker is resolved: all three previously red tests pass with `LiveBackend` unmodified; `live.py` carries no coverage claim and no `cleared`/`timeout` label is recovered for live runs.
- Live runs therefore cannot report `cleared` or `timeout` at all until a separately reviewed, evidence-backed coverage decision exists; live outcome statistics must treat `unknown` as "derived clear or limit, not confirmed". Tasks 3.6 and 3.8 stay open and 3.15 stays unchecked.
- A derived live clear is still rewarded (reward follows events) while the episode label is `unknown`; the value bootstrap on that truncation is a behavior difference of the unchanged training path. Neither was changed.
- `benchmark.py` would put an `unknown` episode in its `episodes` denominator; unreachable with its complete-coverage synthetic backend.
- `valid` changed meaning only when `unknown` episodes exist (see the design-choice section); a report written with `REPORT_VERSION` 1 has no `unknown` field and is not re-interpreted.
- Process: every edit in this continuation used the edit tool; no Python or shell file writes. The `.tooling/openspec/config.json` read by the OpenSpec CLI is the tracked, pre-existing file, unchanged.

## Primary Windows review and correction (2026-10-19; historical, superseded by Windows primary feedback 2)

> Recorded by the Windows primary before feedback 2. Feedback 2 states that the review is
> **not accepted**: its first `Check.ps1` invocation passed Ruff check but failed Ruff format
> on the then-unformatted initial-terminal tests (exit 1, later gates did not run); a separate
> targeted Windows run passed 83 tests and pinned all-items strict OpenSpec passed 30/30, which
> are partial checks. The guard and the formatted tests were changed during that review while
> the task still advertised `ready_for_review`. Treat the acceptance wording and the check
> results below as history of an earlier tree state, not as evidence for the frozen handoff;
> the primary repeats `Check.ps1` and strict validation on that handoff. The Ruff format
> finding is fixed in the final content (see the final section).

Reviewed the actual diff and the task-specific detailed report. `subagent_report.md`
still began with the older native-oracle-recording-provenance task; it did not
contain the current terminal-outcome summary. The matching ignored status file
was `ready_for_review` for terminal-outcome-coverage-20261019-01. This discrepancy
was recorded instead of treating the old summary as fresh acceptance evidence.

### Finding and correction

The initial result accumulated terminal events but `start()` always returned an
ongoing episode. A backend returning `player_died` or `room_cleared` at startup
could therefore allow an action after a terminal event. The worker test asserted
only a later unknown outcome at the limit and did not check this unsafe interval.

Replaced that test with six cases (death, clear and both, with complete or missing
coverage). All six failed on the delivered implementation (DID NOT RAISE). The
controller now rejects a terminal initial result through `EpisodeFault`, invoking
the existing release/fault path before returning a playable reset state. Each
case checks release, stopped state, a recorded fault and that the queued step is
never consumed, including after a rejected follow-up action. Gymnasium reset has
no terminal-transition return slot; invalid initialization must fail explicitly.
The delta scenario and design now document this. No valid step outcome or
coverage claim is fabricated. This supersedes the earlier initial-event handling
and its obsolete unknown-at-limit scenario above.

### Windows verification

Used existing CPython 3.12.14 in `.venv`; no dependency change. For the full gate:

```powershell
$env:PYTHONPATH = 'C:\Users\<user>\Documents\Codex\2026-10-17\work-on-isaac-threrisaifuture-in-the\work\lua-test-runtime'
$env:ISAAC_JSON_LUA = 'C:\Program Files (x86)\Steam\steamapps\common\The Binding of Isaac Rebirth\resources\scripts\json.lua'
$env:TEMP = 'D:\isaac\.tooling\tmp-primary-coverage-review'
$env:TMP = $env:TEMP
./scripts/Check.ps1
```

The JSON file is read by the isolated Lua harness; Isaac was not launched or
connected. TEMP/TMP are process-local and use an ignored workspace directory.

| Check | Command | Exit | Result |
| --- | --- | ---: | --- |
| Reproduction before correction | `.venv/Scripts/python.exe -m pytest -q tests/test_episodes.py -k terminal_initial` | 1 | failed as expected: all six new regressions detected ignored terminal initial events |
| Focused final behavior | `.venv/Scripts/python.exe -m pytest -q tests/test_episodes.py tests/test_evaluation.py` | 0 | passed: 47 tests |
| Initial Windows gate, before correction, without optional Lua runtime | `./scripts/Check.ps1` with isolated TEMP/TMP only | 0 | passed: 1270 tests, 14 optional Lua modules skipped; skips are not acceptance evidence |
| Full Windows gate, after correction | `./scripts/Check.ps1` with the environment above | 0 | passed: 1802 tests, zero skips, 44.25 seconds; Ruff, 106 files formatted, mypy 44 source files, pip consistency, embedded strict OpenSpec 30/30 |
| Strict change validation after scenario edit | `./scripts/OpenSpec.ps1 validate episode-lifecycle --strict` | 0 | passed |
| Final all-items validation after acceptance documentation | `./scripts/OpenSpec.ps1 validate --all --strict` | 0 | passed: 30/30 |
| Final whitespace check | `git diff --check` | 0 | passed; only existing line-ending normalization warnings |
| Checklist readback | `./scripts/OpenSpec.ps1 instructions apply --change episode-lifecycle --json` | 0 | passed: task 3.15 done, 20/27 complete, seven remaining |

### OpenSpec verification and self-review

Using openspec-verify-change; this is a separate self-review by the primary agent,
not an independent review. Verification scope is the delivered task 3.15 and its
five new terminal-coverage/evaluation requirements; existing native obligations
remain open and must not be inferred complete from the offline gate.

| Dimension | Result |
| --- | --- |
| Completeness | Task 3.15 accepted; episode-lifecycle 20/27 tasks complete. Seven remaining tasks: 3.6, 3.8, 4.1, 4.2, 4.3, 5.1, 5.2; all remain required before whole-change acceptance/archive. |
| Correctness | 5/5 added requirements mapped to code and behavioral tests; the existing timeout scenario now explicitly requires complete coverage. No removed/renamed requirements in this task. |
| Coherence | Per-result explicit claims, intersection across all intervals, tri-state facts and known-outcome metrics follow the design. Initial terminal safety is now specified and tested. |

Requirement/scenario mapping:

- Explicit claim/default unknown: `StepResult.__post_init__`, default-missing and
  invalid-coverage tests, synthetic coverage test. No requested-kind/provenance
  inference or Lua/native change appears in the diff.
- Conservative aggregation/tri-state facts: `_accept` and `_fact`, partial-kind,
  all gap positions, episode reset, death/clear tie and ongoing-summary tests.
- Covered terminal resolution: `_outcome`, known death, known clear and
  unresolved-clear release tests; `start` plus six initial-terminal fault tests.
- Timeout/unknown separation: `_outcome` and `_transition`, complete timeout,
  partial/missing coverage, control release, stopped-state and 100-episode tests.
- Evaluation separation/version: `summarize`, `REPORT_VERSION=2`, mixed
  unknown/fault, all-unknown and end-to-end uncovered backend serialization tests.
  Combat gate and real loopback Lua tests exercise propagation of unknown labels.

No unresolved finding remains in task 3.15. Whole-change native producer semantics,
event delivery, consumed updates, endpoint sealing, lifecycle scenarios and 100
real episodes remain not verified; these correspond to the seven open tasks.
Do not archive. No game, real training, approval, deployment, save, checkpoint or
reward implementation changed. Unknown truncation still uses the existing learner
bootstrap path, and positive approximate clear events still receive existing
rewards; this review does not establish their gameplay validity.

Primary also updated STATUS, ROADMAP, task acceptance and the coordinator summary.
Unrelated pre-existing dirty files and the Mac-owned agent-status.json were left
unchanged. No successor worker or monitor was started, and no commit/push occurred.
Next concrete work is evidence for the native producer/transaction gate, not
declaring approximate live events exhaustive to recover old outcome labels.

## Final Windows acceptance after frozen handoff

The intermediate rejection documented a real concurrent-review problem: another
Windows review overlapped this primary's initial-terminal correction. The primary
stopped implementation edits and waited for the existing worker's frozen handoff,
published as ready_for_review at **2026-10-19T19:15:53Z**. That worker made no source
or test changes, only report/task updates. Its seven code/test SHA256 values match
the reviewed implementation exactly. No successor worker or monitoring was started.

After that handoff, `./scripts/Check.ps1` was run again on Windows with the existing
isolated Lua runtime and installed game JSON file (same environment shown above,
but TEMP/TMP relocated to `D:\isaac\reports\local\tmp-primary-coverage-review`).
Exit **0**: **1802 passed, zero skips, 44.22 seconds**; Ruff, format (106 files),
mypy (44 source files), pip consistency and embedded all-items strict OpenSpec
**30/30** passed. The seven code/test files plus delta spec and design were SHA256
checked against the earlier passing snapshot before and after this final gate;
all **nine files stayed identical**. Private hash readback is retained in
`reports/local/coverage-stable-gate-hashes.json`. No runtime was exercised.

The separate self-review and five-requirement mapping above apply unchanged to
this exact content. The concurrency blocker is resolved for this snapshot. Task
3.15 is accepted; episode-lifecycle stays open at 20/27 tasks and is not archived.
The earlier failed formatter invocation and provisional acceptance/rejection
notes are history, not failures of this final frozen snapshot. Mac-owned
agent-status.json is retained as a handoff record rather than rewritten by Windows.
