# Evidence: passive oracle probe during reported floor progression, 2026-10-19

- Date/time and timezone: 2026-10-19, Europe/Amsterdam. The game process started at 18:57:07 +02:00; the Repentance+ log containing this session was last written at 19:03:17 local.
- Git revision and dirty status: `16c00bd98698afbd0336f015271678577db9655d` at review. Pre-existing edits in `AGENTS.md`, `docs/AGENT_WORKFLOW.md`, `reports/2026-10-19-oracle-probe-live-runtime.md`, `subagent.md`, `subagent_report.md`, `errors.txt`, `scripts/Wait-Change.ps1`, and `scripts/wait-change.sh` were preserved.
- Change scope and acceptance criteria: one bounded, read-only `oracle_probe_v1` attach during operator-directed play. It records raw observer/callback diagnostics only; it changes no game, mod, save, input, training, approval, or runtime authority.
- Game/mod/bridge versions: `isaac-ng.exe` with `--luadebug`; handshake acknowledged observer `0.5.0-dev`, protocol/schema 1, epoch 1. Game version and save-slot identity were not attested by the observer.
- Python/package versions and configuration hash: no learner, model, reward, or policy was used. The CLI transcript is private and ignored at `reports/local/oracle-probe-20261019-185806-pid11844.private.log`.
- Scenario, split, seeds, budget, and stop conditions: one CLI attach requesting `oracle_probe_v1`, `--samples 600 --accept-timeout 60`; no reconnect, gameplay command, action, restart, menu input, forced death, reset, spawn, or damage. The client exited successfully after 585 snapshots. Lua diagnostics stopped at their existing 1,024-record cap (`reason=count`) after 99.511 seconds of diagnostic time.

## Results

| Check/requirement | Command/scenario | Exit code | Status | Evidence |
|---|---|---:|---|---|
| Explicit read-only diagnostic handshake | `python -m isaac_threrisaifuture.cli observe --oracle-probe --samples 600 --accept-timeout 60` | 0 | passed | Hello acknowledged `oracle_probe_v1`; one session, epoch 1. |
| Advancing observation and room traversal | Same one-connection attach | 0 | passed | 585 snapshots, sequences 1–585, frames 16049–19315; 10 distinct room visit IDs. Status was active for 544 snapshots and paused for 41. Position values changed across the recording. |
| Bounded native diagnostic records | Exact `[Isaac Future OracleProbe]` prefix and current session ID in the Repentance+ log | N/A | passed | 1,024 records, IDs 1–1,024 without gaps, maximum UTF-8 line length 323 bytes, stop reason `count`. Event counts: attach 1; post_update 618; damage_attempt 66; npc_init 20; npc_update_hp 83; npc_death 7; entity_kill 8; entity_remove 20; clean_award 3; new_room 5; post_update_hp 64; post_update_hp_later 128; stop 1. Of 618 periodic state records, 321 were `paused=false, clear=false, dead=false` and 297 were `paused=false, clear=true, dead=false`. |
| Diagnostic cap timing | Same session records | N/A | passed | Diagnostic time range 100296147–100395658 ms (99.511 seconds). The 1,024-record cap stopped callback logging; it did not cover all subsequent play. |
| Observer/game cleanup | Process readback after recording | 0 | passed | CLI exited with code 0; no `isaac-ng` process was present when reviewed. No game command was sent. |
| Operator-reported combat/floor scenario | User report in this conversation | N/A | reported | The operator said they traversed several enemy rooms, defeated a boss, and reached the next floor. Snapshot schema exposes visit IDs but not floor, boss, enemy identity, or save slot; that scenario is not independently attested at that level. |
| Episode lifecycle / event acceptance | Review of this probe only | N/A | not_run | These are raw callback observations, not negotiated `OracleEvent` delivery, verified entity identity/order, a completion receipt, or an outcome barrier. No player death/revival or terminal-run event was observed; `new_room` does not identify a floor transition. Tasks 3.6 and 3.8 remain open. |
| OpenSpec strict validation | `./scripts/OpenSpec.ps1 validate --all --strict` | 0 | passed | 30 items passed. |
| Windows quality gate | `./scripts/Check.ps1` with `TEMP`, `TMP`, and `TMPDIR` set to ignored `reports/local/check-tmp-oracle-floor-20261019-01` | 0 | passed | 1,248 passed, 14 skipped (optional isolated Lua 5.3 runtime unavailable); Ruff/formatting, mypy, dependency consistency, and strict OpenSpec passed. The first run used shared system temp and failed at pytest cleanup with WinError 5 after all tests passed; isolated rerun passed. |
| Diff whitespace check | `git diff --check` | 0 | passed | No whitespace errors in the evidence/doc diff. |

The raw game log and observer transcript remain outside Git. The log was filtered by exact current-session ID; only aggregate counts above are retained in this report.

## Real game

The game was already running under manual operator control. The client only observed state and requested the bounded diagnostic capability; it issued no gameplay commands. At extraction the game process was absent. The operator reported combat-room and boss progression plus a floor transition. The observer independently recorded advancing frames, changing positions, and 10 room visit IDs, but its schema cannot identify the active save slot, boss, floor, or room-clear outcome. The callback record limit ended diagnostics after 99.511 seconds, so the remainder of play is outside diagnostic callback coverage.

## RL evaluation

Not applicable. No training, policy action, reward, checkpoint, or achievement evaluation occurred.

## Limitations and continuation

`damage_attempt` is an attempted callback, not proof of applied damage. NPC HP samples are raw callback reads, not a causal damage result. Death, kill, removal, clean-award, and room callbacks are candidates and do not prove stable identity or event ordering. The operator's floor/boss report is kept distinct from observer-attested facts. This probe does not satisfy episode-lifecycle acceptance or tasks 3.6/3.8. No further probe or game launch is started by this report; any new runtime session needs a separate bounded decision and manual launch/save selection.

Self-review: this report contains only aggregate evidence and preserves the listed unrelated worktree changes. Private logs, saves, backups, and model data are not included.
