# Bounded offline task: make episode outcomes coverage-aware
Task ID: terminal-outcome-coverage-20261019-01
Status: accepted after Windows primary review; executor writes closed
Owner: one existing file-bus executor; no nested workers
Baseline: b973a2c (Record passive floor-progression oracle probe)
Workspace: D:\isaac shared checkout; all project artifacts must remain in English
Continuation: episode-lifecycle tasks 3.6 and 3.8 remain open and runtime-ineligible. Preserve all unrelated dirty files; do not reset, clean, checkout, or overwrite them.
Runtime authority: none. Do not launch/connect/control Isaac, deploy a mod, create or change approvals, train, edit saves/Steam Cloud/settings, or access private logs/models.
Result: reports/2026-10-19-terminal-outcome-coverage.md

## Primary acceptance (2026-10-19)

Accepted with a primary correction for terminal initial results: they now fault
and release before allowing an action. Windows Check.ps1 passed 1802 tests with
zero skips, plus lint/format/mypy/pip and strict OpenSpec 30/30. Offline task
3.15 is complete; native tasks 3.6/3.8 and runtime acceptance remain open.
The matching detailed report was delivered, but subagent_report.md still headed
an older task at review time. The Windows summary records this discrepancy.
No successor assignment, worker invocation, monitoring or runtime action is
requested. The task and feedback below are historical instructions, not renewed
write authority.
Final confirmation after feedback 2: the frozen handoff at
2026-10-19T19:15:53Z was rechecked on Windows: 1802 passed, zero skips, strict
30/30, with all nine implementation/test/spec/design hashes unchanged. The
intermediate NOT ACCEPTED feedback below is superseded. No more executor edits
or fresh handoff are requested for this accepted task.

## Goal
Address finding F1 in reports/2026-10-19-oracle-event-contract-review.md: EpisodeController currently treats missing terminal events as evidence for timeout, and EpisodeSummary defaults death/clear facts to False. Missing coverage must remain unknown rather than becoming a negative game outcome.

## Required contract
- Review EpisodeController, StepResult, SyntheticRoomBackend, Gymnasium/info consumers, current episode-lifecycle spec/design/tasks, and relevant tests before editing.
- Add explicit per-result coverage for the terminal OracleEvent kinds `player_died` and `room_cleared`. Coverage describes exhaustive delivery for that StepResult's exact frame interval; it is not inferred from a requested/recorded kind list, provenance, or absence of event records. Missing coverage defaults to unknown/incomplete. The synthetic backend may explicitly declare complete coverage for tests.
- Aggregate coverage conservatively across the whole episode: a kind is complete only if every interval from the initial result onward explicitly covers it. A later complete interval must not repair an earlier gap.
- Positive event evidence may set its corresponding summary fact True without complete coverage. Set a summary fact False only when that kind is complete over the whole episode and no event of that kind was observed; otherwise use None. Keep death-over-clear precedence. A clear event cannot be reported as the resolved `cleared` outcome if death coverage is incomplete for the relevant episode history; represent the unresolved result explicitly and stop safely.
- At the scenario update limit, report `timeout` only if both terminal kinds are complete across the episode and neither terminal event occurred. Otherwise report an explicit `unknown` outcome, with a truncated transition (not terminated), and release control. Do not count unknown as death, clear, or timeout in summaries/metrics. Document how the unresolved-clear case above maps to the explicit unknown outcome and release.
- Preserve known behavior for fully covered backends, all session/epoch/frame checks, existing release/fault guarantees, rewards, checkpoint/model formats, and native wire formats. Do not invent runtime coverage: no native producer exists, and this change grants no runtime eligibility or Lua export.
- Add an OpenSpec requirement with scenarios and an unchecked offline task 3.15 in the existing episode-lifecycle change; update design. Keep tasks 3.6 and 3.8 unchecked.
- Add focused tests for: default missing coverage; complete no-event timeout; partial coverage at the limit; coverage loss in a later interval; known death; known clear; clear with incomplete death coverage; per-kind False versus None summary values; and control release on unknown termination. Keep the existing 100-episode synthetic test passing under explicit simulator coverage.
- Write the result report with changed paths, commands/exit codes, limitations, and a self-review. Do not mark task 3.15 complete; Windows primary review decides acceptance.

## Allowed writes
- src/isaac_threrisaifuture/episodes.py
- src/isaac_threrisaifuture/sim.py
- tests/test_episodes.py
- openspec/changes/episode-lifecycle/design.md
- openspec/changes/episode-lifecycle/specs/episode-lifecycle/spec.md
- openspec/changes/episode-lifecycle/tasks.md (add unchecked task 3.15 only)
- reports/2026-10-19-terminal-outcome-coverage.md

No other paths, STATUS/ROADMAP, coordination files, user recordings/private data, dependencies, Git operations, runtime access, Lua/native wire changes, rewards/training changes, commits/pushes or archives. If the consumer review shows an out-of-scope integration change is required, report the exact blocker and stop rather than expanding the allowed-write list.

## Validation
Run focused `tests/test_episodes.py`, Ruff check/format, mypy if public types changed, `git diff --check`, and pinned `scripts/OpenSpec.ps1 validate episode-lifecycle --strict`. Report exact commands and results. The Windows coordinator will run `scripts/Check.ps1` and `scripts/OpenSpec.ps1 validate --all --strict` before acceptance.

## Coordinator feedback 1 — decision and bounded scope extension (2026-10-19)

Decision: choose Blocker option 1. Keep `LiveBackend` without terminal coverage: its `EventDeriver` facts are frame-delta-derived and are not an exhaustive event-delivery guarantee. Do not edit `live.py` or assert coverage to recover the previous labels. Update the existing tests to expect `unknown`/truncated where the derived clear or timeout cannot be resolved under the new contract; ensure the ended episode is not stepped again.

The Windows coordinator explicitly extends the allowed-write list for this continuation to:
- `src/isaac_threrisaifuture/evaluation.py`
- `tests/test_evaluation.py`
- `tests/test_combat_gate.py`
- `tests/test_live_e2e.py`

Required continuation:
- Represent `unknown` explicitly in `EpisodeRecord` and evaluation metrics. Keep `faults` distinct. Add an `unknown` metric count; exclude unknown outcomes from death/clear/timeout category totals and from the clear-rate/Wilson denominator. Preserve the existing non-fault population for damage/return means unless a test or contract shows that data is unavailable. Bump the serialized evaluation report version for the metrics-shape change and add/update an OpenSpec scenario in the already-authorized episode-lifecycle delta. Do not change curriculum thresholds, rewards, training behavior, or checkpoint/model data.
- Keep the conservative coverage rule from the initial task. Do not make `LiveBackend` coverage complete merely to preserve `cleared`/`timeout` outcomes. Keep `player_died` positive evidence as death; unresolved clear/death precedence remains unknown.
- Update and rerun all affected tests. Amend the evidence report with this coordinator decision, full-suite results and the added files. Leave task 3.15 unchecked for Windows review; keep 3.6 and 3.8 unchecked.
- Do not edit `docs/STATUS.md`, `ROADMAP.md`, `agent-status.json`, or `subagent_report.md`; do not perform Git operations. No runtime authority is added.

After the feedback is read, the file-bus coordinator must publish a matching `working` state before continuing edits, then a matching `ready_for_review` or `blocked` state when done.

## Windows primary feedback 2 — freeze and resubmit final revision (2026-10-19)

Task ID remains terminal-outcome-coverage-20261019-01. No successor assignment or expanded write/runtime authority.

Review is NOT accepted. The first Windows Check.ps1 invocation passed Ruff check but failed Ruff format on the new initial-terminal tests in tests/test_episodes.py (exit 1); subsequent gates did not run. Separate targeted Windows execution passed 83 tests in 13.93 seconds; pinned all-items strict OpenSpec passed 30/30. These are partial checks, not full acceptance.

Files changed while the task still advertised ready_for_review at 19:06:04Z: the initial-terminal start guard appeared in episodes.py during review, and the unformatted initial-terminal tests were subsequently formatted during review. The final formatted content has been observed; do not report the formatting finding as still unfixed. The required remaining action is a coherent frozen handoff and full Windows rerun against that exact content.

- Publish matching working before any additional edits. Finish all edits under the existing allowed-write list, including the initial-terminal guard/tests/spec scenario and an accurate final report.
- State the final metrics decision explicitly in the report: report-version-2 valid counts known outcomes; unknown stays separate, means cover non-fault episodes, and unknown cannot satisfy minimum-valid gates. Do not change thresholds or curriculum.py under this feedback. This records the reviewed implementation choice, not final acceptance.
- Record the initial-terminal regression cases and final focused/lint/format results accurately. Keep tasks 3.6, 3.8 and 3.15 unchecked pending primary acceptance.
- Publish a fresh matching ready_for_review timestamp only after all worker/coordinator writes to implementation/tests/spec/report are finished. Include SHA256 identities of episodes.py, evaluation.py, sim.py and the four affected test files in the named report. Stop writing those files until primary feedback.

Monitor is PAUSED. No code acceptance, commit/push, archive, runtime or new approval occurred. Primary will repeat Check.ps1 and strict validation on a fresh stable handoff; do not claim the earlier Mac suite or the partial Windows run establishes acceptance.
