# Comparable gameplay evaluation: offline evidence

Date: 2026-10-21 (Europe/Amsterdam). Readiness item 4.
Change: `comparable-gameplay-evaluation`, 3/4 tasks, unarchived.
Base HEAD: `3499db8f57394ec03ee914a63cfa226fbf1f0c75`, new source uncommitted
in the frozen test snapshot. No native policy-quality result was collected.

## Outcome

Added `python -m isaac_threrisaifuture.gameplay_comparison manifest.json report.json`.
The analyzer validates a bounded predeclared matrix and trace hashes, preserves all
attempts/missing cells/faults, independently derives sampled raw HP-loss and
clear/death metrics, and blocks pairing on mismatched start, budgets, policy,
control attribution, coverage or native provenance. Actual initial health and
player/enemy positions, types, HP and phases must match across policies even when
case metadata agrees. Paired deltas are descriptive; learning_claim is always false.
No reward or tensor changes enter the comparison. There is no automated winner.

The guide `docs/GAMEPLAY_COMPARISON.md` declares original t6912/current t7424/future
completed checkpoint and random/scripted controls, frozen normalization/recurrent
rules, validation cases/batches, seeds, limits, denominators and native blockers.
The old live evaluation plan links the new contract without upgrading old logs.

## Frozen delegated checks

One fresh gpt-6-luna/high worker per bounded snapshot; one active worker at a time.
Only prepared offline scripts and own log/test-temp writes were allowed. No source,
test or config edits, installs, Git writes, nested agents, native game/bridge,
approvals, live training, retries within assignment or scheduled supervision.
Primary retained implementation and acceptance.

Final sole command:
`.venv/Scripts/python.exe reports/local/run_gameplay_comparison_checks_3.py`.
Private exact commands/env/hash plan:
`reports/local/gameplay-comparison-checks-plan-3.json`.
Start-before Unix1792568177.6454995; absolute stop-by1792568657.6454995;
480-second global wall cap, 512MiB disk cap; zero native decisions/deaths/restarts
or permitted infrastructure faults/retries. Helper could terminate only its owned
offline child tree on caps. Expected HEAD was the base revision above.

Environment: PYTHONPATH used existing Lua test runtime
`C:/Users/<user>/Documents/Codex/2026-10-17/work-on-isaac-threrisaifuture-in-the/work/lua-test-runtime`;
ISAAC_JSON_LUA used installed game `resources/scripts/json.lua`; TEMP/TMP were
`D:/isaac/reports/local/gameplay-comparison-checks-3/temp`.

| Sequential command | Exit | Result |
|---|---|---|
| `.venv/Scripts/python.exe -m ruff check src tests scripts/smoke_rl.py` | 0 | Passed |
| `.venv/Scripts/python.exe -m mypy` | 0 | 55 source files, no issues |
| `.venv/Scripts/python.exe -m pytest tests/test_gameplay_comparison.py tests/test_evaluation.py tests/test_live_evaluation.py -q` | 0 | 105 passed, zero failed/skipped |
| `pwsh.exe -NoProfile -File D:/isaac/scripts/Check.ps1` | 0 | 2169 passed, zero failed/skipped; 131 files formatted; pip consistency passed; OpenSpec44/44 |

Final logs/result: `reports/local/gameplay-comparison-checks-3/` (`lint.txt`,
`types.txt`, `targeted.txt`, `gate.txt`, `result.json`). Runtime63.94s,
peak output103105289 bytes, under both caps. Primary independently rehashed all396
frozen paths with zero mismatches, confirmed HEAD, actual logs and exit codes.
Final documentation/task updates happened afterward; tested source/tests stayed
unchanged. No worker assertions alone were accepted.
Synthetic RL smoke was not repeated: no training/dependency code changed. Native
testing is not_run; offline synthetic contract fixtures are not gameplay evidence.

Earlier assignments retained, not hidden or counted as passes:
- Snapshot1: lint failed B905 (zip missing explicit strict=False), later checks
  not_run. Primary rehashed396 files unchanged and fixed it.
- Snapshot2: lint/mypy passed; targeted104 passed/1 failed, full gate not_run.
  An adversarial fixture mutated a shared policy dictionary and invalidated the
  later CLI fixture. Deep-copying test inputs fixed isolation; production policy
  identity validation remained strict. Primary rehashed396 files before edits.
- Primary self-review also strengthened actual observed-start matching and final
  terminal-flag agreement before the final passing snapshot.

## Behavior and self-review

The43 new tests cover full submitted-native contract pairing (simulated metadata,
not a native run), unchanged learning_claim=false, synthetic/assisted/mixed/shadow
exclusion, observed initial-health/position/HP differences, missing and duplicate
cells, config/build/runtime/seed identity, corruption/path/size limits, invalid raw
ordering/numbers/extra reward fields, and an actual offline CLI subprocess that
preserves existing output. Existing evaluator/live-runner regressions also passed.

Raw accounting tests cover disappearance, healing, changed spawn generation,
inactive/unknown phase, identity/frame gaps, empty starts, overflow, transient
clear flags, software censoring and faults. Player loss uses observed decreases,
not net health; enemy loss never invents the unseen killing hit. Exposure stops at
the last sample, and near-wall stationary remains explicitly unavailable.

## OpenSpec verification: comparable-gameplay-evaluation

Using openspec-verify-change, spec-driven context: proposal/design/delta/tasks
read and mapped to actual source/tests. This is primary self-review, not independent
review. All three requirements are ADDED; no removals/renames apply.

| Dimension | Assessment |
|---|---|
| Completeness | 3/4 tasks; 3 requirements implemented offline; native task2.1 not verified |
| Correctness | 3/3 requirements and all6 scenarios covered offline; native acquisition/attribution not verified |
| Coherence | Strict WireModel boundaries, lazy offline CLI, existing Wilson helper and oracle separation follow design; existing runtime untouched |

Frozen matrix maps to PolicySpec/Case/Manifest/Trace and compare bounded/hash checks;
tests cover malformed/changed/duplicate/missing cells and observed start mismatches.
Raw gameplay metrics map to raw_metrics and its independent HP/phase/clear/death
tests. Descriptive pairing maps to compare issue gating/aggregates/paired_deltas;
synthetic, intervention, fault and full-contract tests exercise all scenarios.

One critical archive blocker remains: task2.1 requires actual native raw-log
normalization, same-start verification, frozen inference, raw damage/clear and
owned-cleanup acceptance. No offline warning/design contradiction found; zero
optional suggestions. Native acquisition/attribution checks were skipped because
there is no accepted normalized exporter/matched-start controller or newly declared
finite native experiment. Keep task2.1 unchecked and do not archive.

## Material limits and next action

The report validates submitted evidence, not the truth of metadata. Raw-log hash
is a reference; only normalized trace bytes are independently hash-checked by this
analyzer. Native acceptance must inspect original bytes and transformation.
Sampled damage is a lower bound, not projectile attribution; unseen damage and
health/phase mechanics remain unknown. All-observed aggregates include partial
fault/assisted data explicitly without causal policy attribution. Censored episodes
are not known failures; both all-attempt clear fraction and known-outcome rate/CI
must be read beside counts/exposure. No statistical winner or model selection.

No matched original/current/control gameplay suite exists yet. Different game
seeds do not replace independent training seeds; t6912/t7424 both use training
seed20. Train/validation/test separation and multi-seed confirmatory acceptance
remain pending. No existing mixed-control trajectory was relabelled as matched.

No native launch/training/deployment/save/reset/approval writes occurred. The six
migrated-t6912/t7424 artifact hashes and latest pointer were frozen and unchanged;
latest still names7d53f55f-s20-t7424. Original t6912 was not modified. Final
read-only check found no Isaac process or listener9528. errors.txt was left alone.
Next: prepare/review normalized raw capture and the finite five-minute native
qualification, then15-30minutes and one hour before any new four-hour request.
The stopped overnight experiment remains suspended.
