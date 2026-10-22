# Evidence: paused navigation-to-training handoff

- New user-requested finite attempt following the observed game-over handoff gap.
- One Steam launch, file 2 selected visually. Because the previous run ended naturally, a normal New Run menu selection is permitted; no live run is forcibly reset.
- Navigation: one connection, 30 seconds, at most 14 down/no-shoot commands plus final release. Stop on first room transition and wait at most three seconds for an active destination. If the destination is combat, immediately send one menu Escape, verify bridge paused and player alive, then disconnect. No further navigation budget.
- Learner: one seed-20 t4864 resume invocation, target t5120 (256 new steps), five minutes, one-minute gate waits, zero tolerated infrastructure faults, one natural-death restart, 512 MiB disk cap. No renewed invocation.
- Handoff: learner must first observe the verified paused room. A private local manager unpauses once, waits for the same request/session/epoch/room to report combat, then writes the existing readiness acknowledgment. At most three acknowledgments, each fresh request and verified combat. No acknowledgment in empty/dead/paused/foreign state.
- No reward/config/model format or production implementation edits. Private helpers are experimental management assistance, not learned navigation or evaluation.
- Parent t4864/config hash/seed 20 reload and identity checks passed before launch and after cleanup. Temporary approval was 15 minutes, max_restarts=1, with no pre-existing approval overwritten.

## Results

| Check | Status | Evidence |
| --- | --- | --- |
| Menu/new run | passed | Steam PID 43292; file 2 visibly selected. Continue was disabled after the prior natural death. Agent selected New Run, Isaac, Normal, without seed/config edits |
| Navigation | passed | Session `735e2a9fc6994111a2564d4e0bb2a3a7`, epoch 1; two accepted down/no-shoot commands from room 0; y380 -> y427.51 -> room visit 1; no gameplay keyboard input |
| Fresh combat before pause | passed | Private navigation trace records classification combat at destination epoch 1/room 1/frame 393 |
| Automatic pause | failed | Nested process mistakenly invoked Windows PowerShell 5 (`powershell.exe`), whose ExecutionPolicy refused the helper script: "running scripts is disabled on this system". It exited 1 before sending the pause key; navigation helper exited 1 |
| Release | passed | Final structured release returned accepted; no additional movement commands or navigation retry |
| Recovery observation | observed | Subsequent window capture showed the character alive with three hearts in the enemy room. This was not a verified paused handoff |
| Learner / readiness / PPO | not_run | No paused-destination artifact was produced, so the learner manager was not started; no readiness acknowledgment or training invocation |
| Cleanup | passed | Normal CloseMainWindow request, successful game shutdown/unload log, process absent after two seconds; exact temporary approval hash verified before removal; no settings changed |
| Parent preservation | passed | Latest remains t4864; model/normalizer/manifest identity matches initial snapshot and reload succeeds |

The infrastructure failure ends this declared attempt; it is not counted as a
successful pause or training run. No execution-policy setting was changed, no
ExecutionPolicy bypass flag was added, and the rejected pause operation was not
rerun through a different host during this attempt.

## Offline correction prepared after cleanup

The enclosing Codex terminal already uses pinned PowerShell 7.6.5 with effective
RemoteSigned policy. Its executable path and current policy were recorded without
changing either in `reports/local/menu-runtime.json`. Both private helpers now
require that explicit configured runtime instead of guessing `powershell.exe`.
They also require a fresh `ISAAC_HANDOFF_DIR` for per-attempt traces so old evidence
cannot be overwritten or mistaken for a new handoff. The corrected helpers pass
`python -m py_compile`; their corrected pause/resume path remains **not_run**.

Private evidence: `reports/local/nav-pause-events.jsonl`,
`nav-pause-output.txt`, `pause-menu-*.png`, `pause-recovery-state.png`, parent and
approval identities. No production source, dependency, save/Cloud/Steam option
or third-party mod changed. Navigation and menu management are not learned play.

Self-review: two actions and one accepted release stay inside the 16-command
limit. Error output is retained; successful movement does not hide the failed
pause. No new run, approval renewal or training invocation followed the fault.
Next concrete check: use the recorded runtime with a fresh artifact directory,
verify paused/alive same-room bridge data, then test coordinated resume/readiness
under a new finite experiment budget. Full offline gate not rerun for private
helper/report changes; parent readback, preflight and syntax checks passed.
