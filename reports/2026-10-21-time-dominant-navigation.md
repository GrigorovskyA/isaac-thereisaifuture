# Evidence: time-dominant-combat-navigation

- Date: 2026-10-21, Europe/Amsterdam.
- Tested base: f9d327d0cf22b69b246be37d343f0db863cd78cf plus this change's frozen diff.
- Scope: readiness item 2, explicit finite-window navigation and observed no-progress stops.
- Native game/training/deployment/approval activity: not_run; suspended experiment stays closed.
- Learning algorithm, observation, reward, configuration hashes and saved lineage unchanged.

## Verification

| Check | Command/evidence | Exit | Result |
|---|---|---:|---|
| Final delegated assignment | `.venv/Scripts/python.exe reports/local/run_navigation_window_checks_5.py` | 0 | One gpt-6-luna/high worker, exact prepared commands/environment, no retries |
| Lint | `python -m ruff check src tests scripts/smoke_rl.py` | 0 | Passed |
| Targeted | `python -m pytest tests/test_observed_routes.py tests/test_combat_navigation.py tests/test_session_runner.py tests/test_combat_gate.py -q` | 0 | 130 passed, zero failed/skipped, 8.57s |
| Full Windows gate | `pwsh.exe -NoProfile -File scripts/Check.ps1` | 0 | 2101 passed, zero skipped, 45.68s; lint, 128 formatted files, mypy 54 files, pip consistency clean |
| OpenSpec | Full gate strict validation | 0 | 42 passed, zero failed |
| Primary acceptance readback | Rehashed all 381 frozen entries, checked Git HEAD, command exits and actual logs | 0 | Zero mismatches; worker assertions independently confirmed |
| Native qualification | Separately declared finite Continue2 pilot | — | not_run; remains an archive blocker |

Final private artifacts: `reports/local/navigation-window-checks-5/{result.json,lint.txt,targeted.txt,gate.txt}`;
exact commands, hashes, limits and environment in `navigation-window-checks-plan-5.json`.
Each assignment had one global 480-second/512-MiB cap and absolute start/stop bounds,
zero runtime decisions/deaths/restarts, zero retries, no Git/source/game authority.
Final actual execution: 59.03 seconds, sampled peak 91,014,576 bytes.
Primary did not edit tested files during worker execution.

Failed preparation evidence is retained: assignment 1 stopped at lint because two
test fixtures referenced a class declared later; assignment 2 passed 126 targeted
tests, then stopped at mypy over a reused optional/nonoptional door variable.
The primary fixed both; no checks were weakened. Intermediate snapshots 3 and 4
passed their full gates but were superseded by self-review regressions. Only final
snapshot 5 is acceptance evidence for the delivered source. Planning task checkboxes
and final documentation were updated after primary frozen-file verification;
strict validation and diff review were repeated for those documentation edits.

## Behavioral results and self-review

- Explicit time mode bypasses cumulative command/transition/pulse-second stops,
  keeps their telemetry, and gives handoffs the declared finite window narrowed
  by the fixed run deadline. Default diagnostics retain their existing limits.
- A simulated 25-transition route reaches combat even with cumulative counters
  already above the old scale-5 limits. VecNormalize receives one combat reset
  observation and then one sample per actual combat decision, never travel frames.
- Only selected doors with accepted action acknowledgments followed by fresh
  same-floor transitions create directed connections. No inferred reverse edge,
  hidden map or target-index arithmetic. Session/epoch/floor changes clear memory.
- Confirmed routes return through cleared rooms to observed unexplored exits.
  Closed observed cycles stop after their connections are known. Unreachable exits
  produce a different reason. These are partial observed ordinary-room results,
  never a full-floor or gameplay-success claim.
- Self-review added lost-action-ack/rejected-release provenance coverage, cached
  unreachable-frontier coverage and a known-blocked-intermediate-route cycle case.
  Fresh visits remeasure paths; changed observed door sets invalidate cached paths.
- Existing path, freshness, release, health, stationary and global-deadline guards
  remain. Safety/transport faults are not converted into successful exploration.
  No New Run fallback, model initialization or save replacement was added.

## OpenSpec verification: time-dominant-combat-navigation

| Dimension | Assessment |
|---|---|
| Completeness | 3/4 tasks complete; native task 2.1 not verified, no new native plan requested |
| Correctness | All 3 added requirements mapped to source and offline scenarios; native effects not verified |
| Coherence | Design followed; existing gate/bridge/default diagnostic behavior retained |

Requirement mapping: finite navigation modes are implemented in
`CombatNavigationGate`, `LiveRunOptions/_gated`, CLI and `SessionPlan/worker`;
observed route memory in `ObservedRoutes` and `_remember`; no-progress classification
in `ObservedRoutes.choose`, propagated as `NavigationStopped` and exact runner
early-stop reason. Offline scenarios are in test_observed_routes.py and
test_combat_navigation.py, with full existing gate/runner/transport regressions.
This is primary self-review, not independent review. One critical archive blocker
remains: native repeated-room travel, further combat and owned cleanup acceptance.
No archive or learned-play improvement claim.

## Preserved state and next action

All three checkpoint files for both `7d53f55f-s20-t7424` and migrated t6912 were
frozen and independently rehashed unchanged. Latest pointer still names t7424.
Read-only end check found no Isaac process/listener 9528 or action approval.
No training or game reset occurred. The one-off previous New Run permission was
not reused. Next offline task: transactional checkpoint publication and strict
interrupted-save/resume tests (readiness item 3). Native qualification still starts
with a separately declared five-minute pilot, then 15–30 minutes, one hour, and
only after acceptance a newly requested four-hour experiment.
