# Evidence: pure self-learning Windows verification

- Date: 2026-10-22, Europe/Amsterdam. Native Windows, Python 3.12.14.
- Scope: `pure-self-learning-v1` tasks 4.2 and 4.3; user-requested history squash
  and push, then a 15-30 minute native acceptance window. Continuous training is
  conditional on all five native checks passing.
- Starting revision: `ace33dd`, dirty refactor tree. Its committed tree equals
  `026eeab` on origin/main. Personal Git identity checked locally.
- History backup: `D:/isaac-history-backup-20261022.bundle`, `git bundle verify`
  passed; SHA256 `704969b7031108c8f8858eccc0e7d899a3ca50b265ea506edd0bd369e9355661`.
- Removed SMB leftovers: the user deleted `src/isaac_threrisaifuture/campaign.py`
  and `.smbdeleteAAA100000000d98c` after automatic tool approval refused deletion.
  The archived campaign copy remains. Both active paths read back absent.

## Windows gate

Raw logs: `reports/local/pure-20261022/` (ignored, not published).

- Initial `Check.ps1`: failed on three mypy errors in the leftover campaign module.
- Next check: lint, format and mypy passed; pytest failed during cleanup of the
  pre-existing `%TEMP%/pytest-of-Elmin/pytest-current` link (WinError 5).
- Lua suites require optional `lupa.lua53` and `ISAAC_JSON_LUA`; the first default
  invocation skipped them. Installed test-only `lupa==2.6` into the ignored
  `reports/local/pure-20261022/lua-runtime`, without changing project dependencies.
- Full Lua-enabled run: 1027 passed, 3 failed. The new fixture upgrader wrote CRLF
  on Windows, which the strict recording reader correctly rejects. Fixed its
  temporary JSONL writer to use explicit LF; no protocol validation was relaxed.
- Final command: `scripts/Check.ps1`, with process-local TEMP/TMP pointing to
  `reports/local/pure-20261022/temp-final`, PYTHONPATH to the isolated Lua runtime,
  and ISAAC_JSON_LUA to the installed game's `resources/scripts/json.lua`.
  Passed, exit 0: lint/format, mypy (29 files), 1030 tests with no skips,
  pip check and strict OpenSpec 11/11. Log: `check-final.log`.
- `scripts/Smoke-RL.ps1`: passed, exit 0, 16 synthetic CPU timesteps, torch
  2.14.1+cpu, observation 1837, action `[5, 5, 4]`. No native-game evidence.

## OpenSpec verification (self-review)

- Completeness: 10/11 tasks complete after the Windows gate. Task 4.3 requires
  native evidence and stays open until every check passes.
- Correctness: observation/action validation and oracle separation map to
  `entities.py`, `encoding.py`, `actions.py`, `live_wire.py` and Lua callbacks;
  reward bounds map to `rewards.py`; restart/watchdog to `live.py`,
  `stall_watchdog.py` and Lua; lineage, retention, metrics and supervision to
  `training.py`, `checkpoints.py`, `episode_metrics.py` and `session_runner.py`.
  Corresponding schema3, reward_v2, Lua actions/restart, watchdog, pure_training,
  and checkpoint suites exercise the declared offline scenarios.
- Removed firing diagnostics were checked against the five baseline requirements
  in `openspec/specs/native-player-actions/spec.md`; their callback trace,
  sparse-diagnostic and stationary-probe implementations are absent from active
  source/mod/scripts. Archived implementations remain historical.
- Coherence: raw-fact encoding, outcome reward, per-run ledgers and a contract-only
  lineage hash follow the design. Runtime effects remain unverified by offline tests.
- Strict validation: 11/11 passed before the final gate. No archive-readiness claim
  while task 4.3 is incomplete. This is primary self-review, not independent review.

## Native acceptance plan

- Deploy only `mod/observer/main.lua` and `metadata.xml` to the existing observer
  directory while Isaac is closed; back up deployed artifacts locally and compare
  SHA256 after copying. No save/Cloud/options or other-mod changes.
- Start through `Start-Pure.cmd` with `--initialize`, intended save file 2,
  lineage `runs/pure-v1`, seed 1. First native window: at most 30 wall minutes;
  request cooperative stop at 15 minutes once evidence is available, otherwise
  continue only within that same 30-minute deadline. The ordinary supervisor
  stop file stops the worker and closes its owned game normally.
- Disk cap: 20,480 MB; five consecutive infrastructure faults stop the supervisor.
  No fresh-model fallback or source/config edits while the session runs.
- Required evidence: plausible schema3 inventory/collectibles/room facts; a use
  press with an actual effect; watchdog restart; death followed by New Run;
  checkpoint load/readback. Missing evidence keeps task 4.3 open and blocks long run.
- After acceptance only: resume with the same Start-Pure command without
  `--initialize`. Daily episode review and frozen random-policy comparison after
  approximately 24 hours remain future work. No agent heartbeat is scheduled.

## Native results

Not run yet. No pure-v1 model, native acceptance or improvement is claimed.
