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

Code committed and pushed over a8bf858 as `e7a0663`:
`pure-v3: observation v4, slower control, reward v4`. Only unrelated tools/ remains
untracked. No runs, models, approvals or raw logs were included.

Deployment passed with Isaac closed: both old files backed up locally, both new
files copied and SHA256 matched source. main.lua:
`6aec119be5354ff6281731ca3cdbb8b49b4e9c47d78a887c0f760a9680848d46`;
metadata.xml: `00f46cc452c2a4e7809c14501d94de2db1ac94b1dde12b3c25d163922f34b997`.
Native launcher preflight passed. Task 2.2 is complete.

Native qualification ran from 19:30:12 to 19:45:13 CEST, session
`runs/pure-v3/supervisor/session-20261022-193012-0001`. The runner recorded fresh
file2 Continue and active Isaac after seven guarded menu keys. Reward pure-v4,
seed 1 and the expected contract hash were confirmed. No working-copy file was
edited during the session. The monitor and final readback verified 791 frozen
tracked/helper files unchanged.

| Native criterion | Status | Evidence |
| --- | --- | --- |
| Stats / flags / weapons | passed, baseline scope | damage 3.5, tears/sec 2.727, range 260, shot/move speed 1, luck 0; 16 false tear bits, only tears weapon true |
| Schema4 encoding | passed | 1100 retained game_api frames revalidated and encoded to 2038 values |
| Own tears | passed | 863 sampled frames contained own_attack during policy shooting |
| Placed bomb age | passed | Six bomb identities retained; example session 350b2dcfc6154039b451ab2caee8a6b5, epoch 2, room 0, entity 50: age 0..44 in 29 samples |
| Accepted use | passed | 559 accepted use acknowledgements; bomb ack sequence 13 at frame 90, entity age 0 appeared at frame 91 next to the player, inventory bombs 0 |
| Action hold | passed | Captured accepted action commands all requested frames=6; first native update use_none share 0.8359375 |
| Watchdog | passed | Five stall episodes; native source=command dispatch and increasing epochs |
| Natural death / New Run | passed | Episode 5, epoch 5, source=death, [New, 2], confirmed epoch 6 |
| Checkpoint load | passed | Real model + VecNormalize loaded from 03b9c5e3-s1-t3584, schema4, pure-v4, expected hash/seed |
| Stop / frozen inputs | passed | 900 s stop request; terminal elapsed 901.782 s, learner exit 0, user_cancelled, no faults or cleanup errors, all frozen hashes unchanged |
| Native ownership cleanup | passed | No game, training Python, listener 9528 or approval remained; stop.forever present |

Seven optimizer updates / 3584 steps were saved; six completed episodes comprise
one death and five stalls. The last partial rollout was not saved. Source status
remained training through checkpoint completion, consistent with the new idle
threshold. Old pure-v2 remains stopped at d9b93984-s1-t58880.

Checkpoint model SHA256:
`47f5bfcd772f3830f488657f9ed1ff3664fc412edb9217da4d56f14536d473a8`;
normalizer SHA256:
`91c5d5ebf64596bd6789560829a061e493e1a37547d719ae6b372edee60a9d10`.
Readbacks: audit-summary.json, checkpoint-cleanup-readback.json and monitor-result.json
in the ignored local evidence folder; original bounded records in
`runs/pure-v3/acceptance-audit`.

Sampled native messages peaked at 5301 bytes, below 32768; this is not worst-case
load evidence. Native positive tear flags, non-tear weapons, lasers/knives and
heavy-attack capture remain outside this baseline check. Episode use_* CSV counts
remain requested uses; accepted presses above come from actual acknowledgements.
These 15 minutes do not establish improved play or the hours comparison milestone.

Task 2.3 is complete at the declared short-check scope. No change was archived.
All report/status/task edits were made after full shutdown, before continuation.

## Two-hour continuation handoff

The prepared `reports/local/pure-v3-schema4-20261022/Run-TwoHour.ps1` removes only
the pure-v3 stop file, starts a 7200-second Start-Job timer, and calls Start-Pure.cmd
without --initialize. Its PowerShell parent stays alive while training runs; the
timer creates stop.forever. Runtime launch/deadline receipts are
`runs/pure-v3/supervisor/two-hour-timer.json` and, when it fires,
`two-hour-timer-fired.json`. The next supervisor plan records the actual resumed
parent and status. Qualification audit instrumentation is not enabled for this run.
No working-copy edits will be made while the two-hour session is active.
