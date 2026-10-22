# Transactional checkpoint publication: offline evidence

Date: 2026-10-21. Readiness item 3. Change:
`transactional-checkpoint-publication`, 3/4 tasks, unarchived.

## Outcome and scope

The trainer stages and flushes model, normalizer and storage-v2 manifest with
artifact SHA256, renames a complete immutable directory, then atomically replaces
latest. An OS-released nonblocking writer lock serializes parent validation and
publication. Stale parents, non-increasing steps, corrupt state and accidental
fresh initialization around partial artifacts fail explicitly. Version-1
checkpoints remain readable unchanged under their existing compatibility contract,
including legacy directory aliases and initial external-parent serialization.
There is no directory-discovery recovery, replacement policy or New Run fallback.

Final session status independently rereads latest after shutdown; a completed save
whose event was lost is recovered with its manifest timestamp. Corrupt progress
cannot become zero saved steps. Failed heavy restore closes its environment.
Only completed updates are saved; partial rollouts remain unsaved.

## Bounded delegated checks

One fresh `gpt-6-luna` / `high` script worker at a time, no nested delegation,
source/config/test edits, Git writes, game access, approvals, live training or
retries within each assignment. Synthetic training wrote only declared test temp.
Final command: `.venv/Scripts/python.exe reports/local/run_checkpoint_storage_checks_5.py`.
Exact absolute commands, environment, source/config/checkpoint hashes and caps are
in private `reports/local/checkpoint-storage-checks-plan-5.json`.
Expected HEAD: `7c41a6b1ae11e0eefa8ef001ff94e61cc3ecb3a8`.
Final start-before Unix 1792555746.2546144; stop-by 1792556226.2546144;
480-second global execution cap, 512 MiB output/temp cap; zero native steps,
deaths, restarts or permitted infrastructure faults. Only owned offline process
trees could be stopped on cap; no lease renewal or unplanned repetition.

Environment: `PYTHONPATH` points to the existing project Lua test runtime at
`C:/Users/<user>/Documents/Codex/2026-10-17/work-on-isaac-threrisaifuture-in-the/work/lua-test-runtime`;
`ISAAC_JSON_LUA` points to the installed game's `resources/scripts/json.lua`;
TEMP/TMP point to `reports/local/checkpoint-storage-checks-5/temp`.

| Command (sequential) | Exit | Result |
|---|---|---|
| `.venv/Scripts/python.exe -m ruff check src tests scripts/smoke_rl.py` | 0 | Passed |
| `.venv/Scripts/python.exe -m mypy` | 0 | 54 source files, no issues |
| `.venv/Scripts/python.exe -m pytest tests/test_checkpoint_publication.py tests/test_training_manifest.py tests/test_checkpoint_policy.py tests/test_combat_gate.py tests/test_async_restart_training.py tests/test_live_reward_continuity.py tests/test_session_runner.py -q` | 0 | 209 passed, zero failed/skipped |
| `pwsh.exe -NoProfile -File D:/isaac/scripts/Check.ps1` | 0 | 2126 passed, zero failed/skipped; lint/format/types/pip consistency passed; OpenSpec 43/43 |
| `pwsh.exe -NoProfile -File D:/isaac/scripts/Smoke-RL.ps1` | 0 | 16 synthetic timesteps, CPU; Isaac integration false |

Final result/logs: `reports/local/checkpoint-storage-checks-5/` (`result.json`,
`lint.txt`, `types.txt`, `targeted.txt`, `gate.txt`, `smoke.txt`). Runtime 86.49s,
peak output 167835839 bytes. Primary independently rehashed all 388 frozen paths
with zero mismatches, confirmed expected HEAD and read actual logs/exits before
changing final documentation/task checkboxes. Tested production source stayed
unchanged afterward. No worker assertions alone were accepted.

Earlier frozen assignments are retained as evidence, not silently counted as passes:
1. mypy failed on Windows fcntl imports with `os.name`; changed to `sys.platform`
   for platform-aware type checking.
2. 153 targeted passed; full gate 2120 passed / 3 failed exposed existing
   initial external-parent serialization compatibility; preserved that API while
   rejecting missing latest with completed history.
3. 170 targeted passed / 1 failed exposed legacy directory-alias compatibility;
   strict pointer/manifest identity now applies to v2, legacy v1 aliases retained.
4. 172 targeted / 2125 full tests and smoke passed. Primary self-review then added
   final readback for committed publications with lost events; snapshot 5 above
   supersedes snapshot 4. Frozen files were checked after each assignment before edits.

## Behavioral evidence and primary self-review

`tests/test_checkpoint_publication.py` injects failure during model, normalizer,
flush, manifest, directory rename and pointer replacement (before/after commit).
Readers retain complete old/new generations, prior bytes remain immutable,
owned temporary paths are cleaned, and unpublished completed candidates are
neither adopted nor overwritten on retry. A real child process is killed while
writing a staging artifact; the OS releases its writer lock, old latest remains
valid, leftover staging is ignored and a later save succeeds. Concurrent readers,
writer contention, stale lineage, invalid pointers and corrupt hashes are covered.

The actual synthetic RecurrentPPO resume test compares optimizer tensors,
VecNormalize statistics, Python/NumPy and declared Torch RNG at entry to resumed
learning, then checks a new completed update and parent identity. Changed policy
tensors establish another update only, never improved gameplay. Failed-heavy-load
and partial-state tests prove cleanup and no silent fresh initialization.
Existing async restart/unsaved-rollout regressions passed. Session-runner tests
include a complete save without a checkpoint event and final corruption handling.
The semantic-normalizer test helper updates its hash after intentional stats edits;
separate hash-corruption tests still reject unmodified hashes before deserialization.

## OpenSpec verification: transactional-checkpoint-publication

| Dimension | Assessment |
|---|---|
| Completeness | 3/4 tasks; all 3 added requirements mapped offline; task 2.1 not verified (no new native execution request) |
| Correctness | 3/3 requirements and all 6 delta scenarios covered offline; native effects not verified |
| Coherence | Staging/atomic pointer, serialized lineage, fail-closed restore and legacy compatibility follow design and existing module patterns |

Complete atomic publication maps to `checkpoints._publish_checkpoint`,
`latest_checkpoint_dir`, `_replace_pointer` and interruption/concurrent-reader tests.
Immutable versioned integrity maps to `CheckpointManifest`, `read_manifest`,
`save_checkpoint`, `_writer_lock` and hash/stale/writer/orphan/v1 tests.
Strict continuation maps to `training.train` restore/cleanup, live saved-step
accounting, final `session_runner.supervise` readback, actual optimizer/RNG resume,
failed-load and existing rollout tests. Source/diff/spec review was primary
self-review, not independent review. No unresolved offline warning or design
contradiction found. Critical archive blocker: task 2.1 requires separately
requested finite native resume/interruption and owned-cleanup evidence. Do not archive.

## Limits and preserved state

This proves process-interruption consistency, not power-loss durability, external
mutation resistance, native game-state restoration or partial rollout/RNN recovery.
Version 1 has no embedded hashes; it was not rewritten. Hard-killed staging and
unreferenced complete directories remain ignored and consume disk until explicit
recovery/cleanup. No automatic adoption or destructive cleanup was added.

Both t7424 and migrated t6912 model/normalizer/manifest files and latest pointer
were included in the 388 unchanged hashes. Original t6912 was not modified.
Latest remains `7d53f55f-s20-t7424`. No Isaac process or listener 9528 was observed
at the final read-only check; no game, training, deployment, save edit or approval
creation occurred. Native acceptance is **not_run**, not passed. The stopped
overnight experiment remains suspended. Next offline: comparable damage dealt,
damage taken and room clears (item 4). Native qualification remains 5 minutes,
then 15-30 minutes, one hour and only then a newly requested four-hour experiment.
