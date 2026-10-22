# Evidence: pure-v3 observation v4 and control acceptance

- Date: 2026-10-22, Europe/Amsterdam. Native Windows; user-requested continuation
  from `a8bf858` with the prepared `pure-v3-observation-and-control` change.
- New lineage only: `pure-v3`, seed 1, schema 4 / 2038 floats, action v2, repeat 6,
  reward v4 (`pure-v4` contract), initial use-none probability 0.85. Model contract
  hash `03b9c5e3c782d6b3d59c0e6b30cc4aa7ea8818f3d68e7180f4a32c269fdc8429`.
- `pure-v2` remains stopped by its existing stop file and preserved at
  `d9b93984-s1-t58880`. Its analysis is `2026-10-22-pure-v2-analysis.md`.
- No save/Cloud/options, unrelated tools, model migration or dependency changes.
  Personal Git name/email checked locally before publication.

## Offline checks and review

| Check | Status | Evidence |
| --- | --- | --- |
| Unused tests/test_stall_watchdog.py.bak | removed | Untracked legacy backup; not imported or needed |
| First Windows gate with Lua | failed | 1118 passed; oversized parametrized test name exceeded Windows environment-variable limit during pytest setup/teardown |
| Windows fixture/test repair | passed | Gave the malformed-input cases short IDs; oversized payload and strict protocol assertions unchanged |
| Final scripts/Check.ps1 | passed, exit 0 | 1119 tests, no skips; ruff/format, mypy 31 files, pip check, strict OpenSpec 13/13 |
| scripts/Smoke-RL.ps1 | passed, exit 0 | 16 synthetic CPU steps, 2038 observations, actions [5,5,4] |
| Git diff check | passed | No whitespace errors |

Logs: `reports/local/pure-v3-schema4-20261022/` (ignored).
Primary self-review maps player/weapon/attack/bomb facts to Lua, `entities.py`
and `encoding.py`, control/prior to `training.py` and `live.py`, reward v4 to
`rewards.py` and the config. Schema4, Lua entity, pure-training, reward-v4 and
session-runner tests cover the declared offline scenarios. This is not independent
review. Native API correctness and learning improvement remain unproved by tests.

## Frozen native plan (prepare before starting)

1. Commit verified source/config/tests/docs, excluding runs, models, approvals, raw
   logs and unrelated tools. Deploy only main.lua and metadata.xml while Isaac is
   closed, with local backups and SHA256 readback.
2. Start `Start-Pure.cmd <game> <log> --initialize`, run root `runs/pure-v3`.
   Exactly one supervised qualification window: 900 seconds from the runner clock;
   stop on source/config/mod/audit-input changes or early fault. Disk cap 20,480 MB,
   fault cap 5, unlimited death/stall New Run subject to native pacing and lease.
3. The primary makes no working-copy edits during the session. Existing runtime
   artifacts, checkpoints and bounded audit logs are the only writes.
4. Passive acceptance instrumentation is loaded only for this session through a
   process-local PYTHONPATH / ISAAC_ACCEPTANCE_AUDIT_DIR. It delegates the original
   LiveClient read/command methods unchanged and captures sampled policy frames
   (oracle excluded), wire sizes and selected command acknowledgements. Limit:
   5000 records / 32 MiB per worker. No scripted gameplay, masks or rewards.
   Audit input: `reports/local/pure-v3-schema4-20261022/audit-runtime/sitecustomize.py`,
   SHA256 `5bf2e688106d56037ae3f969f7ea406edf612f1563d186727fb01fa78bcef51d`.
5. Verify plausible stats/16 flags/15 weapon bits, own_attack while shooting,
   a bomb with increasing age for one identity, accepted use acknowledgement,
   watchdog and death restarts, actual checkpoint/model/normalizer load, frozen
   hashes and normal cleanup. Missing evidence keeps task 2.3 open.
6. Only after acceptance, resume without --initialize for at most 7200 seconds.
   The prepared PowerShell parent holds a Start-Job stop timer and calls the same
   Start-Pure.cmd; timer creates runs/pure-v3/supervisor/stop.forever. The parent
   stays alive with the command, so the job is not abandoned when a launcher exits.
   No agent heartbeat or scheduled supervision. Dashboard defaults to pure-v3.

## Native results

Not run yet. Deployment, acceptance and two-hour continuation are pending.
