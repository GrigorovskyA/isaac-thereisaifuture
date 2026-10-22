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

Deployment passed while Isaac was closed. Old observer files are backed up under
`reports/local/pure-20261022/deploy-backup`; deployed main.lua SHA256 is
`edf4eff22eb785c6b9a24cc511f65b075af23da67c3b5aa7df19d1340ee7c1c8`, metadata
SHA256 `00f46cc452c2a4e7809c14501d94de2db1ac94b1dde12b3c25d163922f34b997`.
Only the existing observer is enabled; all other installed mods retain disable.it.

The first invocation stopped before training on the foreground guard. The forever
supervisor began one retry before the stop file was observed. Both startup workers
needed termination after the 15-second cooperative-stop timeout; this is a cleanup
limitation, not a successful release test. Afterward no game/listener/approval
remained. The user then confirmed readiness to keep the game foreground.

The second invocation (`Start-Pure.cmd ... --initialize`) entered file 2 through
seven guarded menu keys, with fresh `[Continue, 2]` and active character type 0.
Session: `runs/pure-v1/supervisor/session-20261022-160854-0001`, started
16:08:54 CEST. Learner started at 16:09:15. Source revision: `bd44fe6`.
Config contract hash: `c55320966c51d7c51069352659c916111a9c2f55d319d66817789791222c6ada`.

- Death restart passed: session `481d42bca6804392997b6088c8128613`, epoch 1,
  327 steps, natural death; native `source=death`, `[New, 2]`, confirmed epoch 2.
- Watchdog restart passed: the next episode ended `truncated/stall` after 824
  steps; `Command restart accepted` in session `7b5d0d8ba9f5444b9e750a05437dedaf`,
  epoch 2; native `source=command`, confirmed epoch 3.
- Use effect: native accepted use commands and PillCard trigger lines are present;
  the user explicitly confirmed seeing an actual bomb/item/card effect. This
  operator observation supports the required use-effect check, not all three uses.
- Checkpoint readback passed: `CheckpointPolicy` loaded the real model and
  VecNormalize for `c5532096-s1-t1024`, schema3/actions2, pure-v2, seed 1.
  Model SHA256 `5c1613fb984857b359c5e7e9178eab3b85931e679c3a49c14833c94b24c5725b`;
  normalizer SHA256 `3f2964a798203c73f5c7b64a70afa40bb9fe0cb953bd934d27403b2fc6a51ae7`.
  Readback JSON is saved locally. The manifest reward_schema_version field is 1;
  the explicit reward contract is pure-v2 and config contract reward_version is 2.
- The session stopped after 907 seconds. Latest saved checkpoint is
  `c5532096-s1-t7168`, 14 completed rollouts. CSV has 9 completed episodes:
  2 deaths, 7 stalls, no rooms cleared. The unfinished final rollout was not saved.
- Learner exit was 0; owned game closed normally, approval removed, no listening
  port 9528 remained. Final state was nevertheless fault: the user concurrently
  changed `episode_metrics.py` for a dashboard, so frozen-source verification
  detected a mismatch. These edits are preserved; they are outside this commit's
  implementation scope. No clean final-code resume is claimed.
- Read-only follow-up probe passed (exit 0): 40 retained schema3 frames, encoded
  size 1837, session `78ba2d9690fd4532acf0cffd3cc6fe84`, epoch 1, frames
  2590..2737. Coins/bombs/keys 0, no active item or held collectibles, stage 1,
  normal clear room, three open doors, obstacle entities only. Values are plausible
  for the observed empty starting room; nonzero inventory/item diversity remains
  untested. Probe made no gameplay/model/approval writes and closed its owned game.
- The user's new `wall_time` CSV field would reject the old header on resume.
  Performed one additive local data migration with exact-byte backup at
  `runs/pure-v1/metrics/episodes.before-wall-time-20261022.csv`. All 9 original rows
  and cells verified unchanged; added historical timestamps are blank, not invented.
  Original SHA256 `e726b5b13e6b76d0fc842a3994ae7be13d958aa5f7969273293e435b837679d3`;
  migrated SHA256 `0db80cfc53bc43afc50e000c8f6242340b40f97018b9326bafc11b2ad0c4dc91`.
- Re-ran the full Windows gate on the current workspace, including the user's
  dashboard code: exit 0, 1043 tests passed with no skips, mypy 30 files, lint/
  format/pip check and strict OpenSpec 11/11 passed. Log: `check-dashboard.log`.
- All five requested native feature observations have evidence, but task 4.3
  remains open because final frozen-source cleanup failed. Next step is a clean
  bounded resume from latest on stable integrated sources; do not initialize again.
- User requested a logical stopping point while another agent works. Stopped with
  game/learner/listener closed, no approval and stop.forever present. No long run,
  daily automation or 24-hour random-policy comparison was started.

## Publication

The verified refactor was squashed to root `bd44fe6` and force-with-lease pushed
against the known old origin/main hash. Remote main read back at the new hash;
no other remote branches/tags were present. Old local branches and refs/codex were
removed after bundle verification; `git rev-list --all --count` returned 1 then.
Git warned that branch configuration updates could not write `.git/config`, but
readback confirmed local main tracking origin/main. No permission/ACL changes were made.
The final evidence/status handoff is a subsequent documentation commit; concurrent
dashboard source/docs and the pre-existing tools/.bak remain uncommitted.
