# Evidence: combat-progress-diagnostics and checkpoint pointer read repair

- Date/time: 2026-10-21, Europe/Amsterdam; successful checks completed 10:05:33 UTC.
- Base revision: f024d4cba94d0a14d2a56da618f138885b757a4d plus this reviewed diff.
- Scope: opt-in gated endpoint evidence and persistent conservative progress stop;
  repair the concurrently exposed Windows checkpoint pointer-open sharing race.
- Python 3.12.14, pytest 9.1.1; no dependency installation or changes.
- Game/mod/bridge: not run, not deployed, no schema/reward/config/model migration.
- Preserved learning identity: 7d53f55f-s20-t21760, seed20, config hash
  7d53f55f92aae137da716f2916e4cc18db2c2594ef76bb58d2104bdb1e7ce4ee,
  reward live-conservative-v2. Strict checkpoint load/hash validation succeeded.

## Implemented behavior

Live and finite session entry points expose `--combat-trace-bytes` (0 disables,
maximum 256MiB combined streams) and `--combat-progress-updates` (omitted disables,
integer 1..108000). Invalid ungated requests fail before game actions. The session
plan retains limits; no default learning behavior or weights changed.

Policy JSONL pairs the selected action with before/after encoder vectors and
identities, clipping/overflow and transition/fault labels. Raw snapshots are in a
separate oracle JSONL. Encoded vectors are checked against their raw frame and
labeled pre-VecNormalize; network normalized inputs/RNN states and command
acknowledgements are not captured. Weapon range is explicitly not exported.
Exclusive file creation and combined pair-byte checks prevent overwrite/overflow.
Capacity exhaustion declares incomplete capture and stops before another action.

The endpoint monitor reuses conservative EventDeriver floors. Software reset
rebaselines membership without renewing accumulated combat updates or HP credit.
Management/reset gaps do not count. New native visits start new windows. Healing,
missing enemies, overflow and max-HP phase changes cannot fabricate progress.
Registered conservative damage or a clear resets the window. This is partial
endpoint coverage, not proof that actual damage was zero. An explicit diagnostic
stop releases input before the next action/reset, invents no outcome and permits
no automatic new run. Last counted decisions remain in checkpoint/unsaved accounting,
including a sample SB3 auto-reset can interrupt before rollout storage.

Full-gate concurrency exposed `latest.txt` open failing with Windows access denial
during atomic publication. Checkpoint reads now retry only WinError5/32/33 for at
most one second. Persistent/unclassified errors still fail explicitly; corruption,
strict hash/lineage validation and no-initialization-fallback remain enforced.

## Execution and results

The primary prepared exact scripts; fresh gpt-6-luna/high workers executed one
bounded assignment each, sequentially, fork_turns=none. Final assignment had a
12-minute wall cap, 2GiB artifact cap and zero native actions/deaths/restarts or
runtime authority. Only report/test artifacts and normal caches were writable.
No tested source/config was edited during a worker run. The last worker's final
message hit its account usage limit after the script completed; acceptance below
comes from primary inspection of actual files, not a worker assertion.

| Attempt/check | Exit | Status | Evidence |
| --- | --- | --- | --- |
| Attempt01 targeted | 1 | failed infrastructure | Shared TEMP pytest-current access denial during session cleanup; no usable pass summary |
| Attempt02 targeted | 1 | failed setup | 24 passed,105 errors,0 skips; backslash path consumed by PYTEST_ADDOPTS parsing |
| Attempt03 targeted | 0 | passed | 129 passed,0 skips |
| Attempt03 full gate | 1 | failed | 1641 passed,1 concurrent pointer-read failure,17 optional Lua skips; no acceptance |
| Attempt04 targeted | 0 | passed | 160 passed,0 failed/errors/skipped in10.34s |
| Attempt04 full Check.ps1 | 0 | passed | 2229 passed,0 failed/skipped in50.67s; ruff/format/mypy56 sources/pip consistency passed; OpenSpec48/48 |
| Primary frozen readback | 0 | passed | All380 recorded input hashes matched; helper/manifest hashes matched |
| Primary `./scripts/Smoke-RL.ps1` | 0 | passed | Synthetic CPU RecurrentPPO16 steps/save/reload,torch2.14.1+cpu; no Isaac integration |
| Native diagnostic/training/comparison | N/A | not_run | No new game launch,approval,New Run or learning |

Exact successful commands, from D:/isaac:

```powershell
$env:PYTEST_ADDOPTS = '--basetemp=D:/isaac/reports/local/combat-diagnostics-check-04/pytest-targeted'
.venv/Scripts/python.exe -m pytest tests/test_combat_progress.py tests/test_combat_diagnostics.py tests/test_combat_gate.py tests/test_session_runner.py tests/test_checkpoint_publication.py -q
$env:PYTEST_ADDOPTS = '--basetemp=D:/isaac/reports/local/combat-diagnostics-check-04/pytest-full'
./scripts/Check.ps1
```

The helper also supplied the existing isolated Lua5.3 runtime on PYTHONPATH and
the installed game resources/scripts/json.lua on ISAAC_JSON_LUA. Those process
environment values were restored after execution. No test was weakened/skipped
to obtain acceptance. The isolated forward-slash basetemp fixes harness setup,
while source regressions and pointer repair fix the actual concurrency defect.
Full tests include synthetic learning/continuation; these do not verify Isaac.
After Luna's final-report usage-limit failure, the primary ran the required RL
smoke directly with isolated process TEMP/TMP under
reports/local/combat-diagnostics-smoke/temp, restoring both afterward. Output:
reports/local/combat-diagnostics-smoke/smoke.log and result.json. No runtime or
checkpoint lineage in the real training root was touched by this synthetic test.

Local evidence: reports/local/combat-diagnostics-check-01..04 (ignored), with
run.ps1, inputs.json, targeted.log, full.log, result.json and primary-verification.json.
Final helper SHA256: AB0E0D2021BE08150AAAC140B6E0C07944C9271E6A4CD29C0CC195DEDD7A655E.
Final input manifest SHA256: 855652DA45124A1DD28B32EF64B8709AB35DF17740AB8A6859D19E609D71DDE9.
No active Isaac process/listener9528 or training approval was observed on readback.
The strict current checkpoint read returned t21760/21760 steps. Prior states and
unrelated errors.txt were not edited. Raw native logs, saves and models are excluded
from publication.

## Self-review and OpenSpec verification

Used openspec-apply-change and openspec-verify-change; this is primary self-review,
not independent review. Historical context in OpenSpec config is superseded by
current AGENTS.md authorizing one bounded Luna runner and primary Git publication.

| Dimension | Assessment |
| --- | --- |
| Completeness | combat-progress-diagnostics3/4; checkpoint-storage follow-up4/5. Native tasks remain incomplete; neither change is archive-ready |
| Spec coverage | All3 new combat requirements and the added pointer-sharing scenario mapped to implementation; no removed/renamed requirements |
| Correctness | Same-frame separation/cap/mismatch tests; persistent reset/HP floor/unknown-outcome/stop/unsaved tests; live and worker option propagation; classified/persistent/unclassified pointer reads; existing concurrent reader/corruption/restore tests passed |
| Coherence | Defaults off, version1 diagnostic format, unchanged policy/reward/checkpoints, explicit partial coverage and pre-normalization boundary match design |
| Native qualification | not verified: no new bounded runtime experiment executed |

Critical before archive: complete native task2.1 in each relevant change under a
new finite experiment. No unresolved source-level issue was found in the offline
checks reviewed. Publication does not supply native acceptance or authorize resume.

## Continuation

See [usage and next learning steps](../docs/COMBAT_PROGRESS_DIAGNOSTICS.md).
First qualify five-minute native capture and owned cleanup under a new experiment.
Then add verified weapon-range/type observation with explicit compatibility and
lineage planning, bounded reachable-firing-position shaping and verified kill
evidence. Keep the injury penalty but do not equate it with learned dodging.
Compare actual HP loss, damage taken and clears, with unknowns and failed attempts.
Advance duration5min ->15-30min ->1h ->new4h request. No better-play claim or new
learning run is made by this offline milestone.
