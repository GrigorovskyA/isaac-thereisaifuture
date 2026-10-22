# Evidence: passive oracle callback probe, 2026-10-19

- Date/time and timezone: 2026-10-19, Europe/Amsterdam.
- Git revision and dirty status: cf55c2c, main equals origin/main before this report; unrelated pre-existing AGENTS.md, docs/AGENT_WORKFLOW.md, subagent.md and subagent_report.md edits plus errors.txt and wait scripts were preserved.
- Change scope and acceptance criteria: one operator-directed, passive OracleProbe attach to observe real callback facts. No Lua/Python behavior was changed and no OracleEvent export was accepted.
- Game/mod/bridge versions: user-launched isaac-ng.exe PID 39384 with --luadebug; user reported manually choosing file 2 and Continue. Hello reported observer 0.5.0-dev, Lua 5.3, protocol/schema 1, extender absent, game version unavailable. File identity is operator-reported, not independently attested.
- Python/package versions and configuration hash: Python 3.12.14; no learner, model, reward or configuration was used.
- Scenario, split, seeds, budget, and stop conditions: one read-only client, no reconnects, action or restart mode, maximum 600 snapshots/120 seconds. Lua logger shared its per-load 1024-record/400-byte budget. The probe issued no game input and requested no forced death, reset, debug spawn/damage or menu action.

## Results

| Check/requirement | Command/scenario | Exit code | Status | Evidence |
|---|---|---:|---|---|
| Current game instance and Lua access | Read-only process metadata before attach | 0 | passed | Process 39384 was the installed isaac-ng.exe with --luadebug. |
| Explicit probe attach | .\.venv\Scripts\python.exe -m isaac_threrisaifuture.cli observe --oracle-probe --samples 600 --accept-timeout 60 | 0 | passed | Hello acknowledged oracle_probe_v1; session db02b046601a4250899885b62d6429d0, epoch 1. |
| Bounded diagnostic output | PowerShell Get-Content filtered for the exact OracleProbe prefix and session ID; git check-ignore -v -- reports/local/oracle-probe-20261019-db02b046.log | 0 | passed | 1024 records, contiguous IDs 1..1024, maximum 323 UTF-8 bytes; final record stopped with reason=count. Diagnostic span was 109861 ms. Only those session lines were written to the ignored evidence file. |
| Candidate callback coverage | Ordinary manual play across room visits 1..10 | N/A | partial | damage_attempt 72; npc_update_hp 102; post_update_hp 68; post_update_hp_later 132; npc_init 35; entity_kill 19; entity_remove 28; npc_death 16; clean_award 3; new_room 9. |
| Client disconnect and listener cleanup | The observer exited 0; process and port 9528 checks | 0 | passed | No oracle-probe Python process or listener remained. Console output was truncated, so no exact snapshot total is claimed. Isaac stayed open; no game close or restart was issued. |
| Player terminal/floor/exit scenarios | No forced or planned scenario | N/A | not_run | game_end, pre_game_exit, pre_mod_unload and new_level were not observed. Player death/revival semantics remain untested. |
| Export eligibility | Compare observations with episode-lifecycle task 3.6 | N/A | not_run | Raw callback facts do not establish stable spawn identity, universal ordering, clear/reward semantics, delivery, or a completion barrier. No OracleEvent was emitted. |
| Windows quality gate | TEMP/TMP/TMPDIR set to ignored reports/local/check-tmp-oracle-probe-20261019-01; run ./scripts/Check.ps1 | 0 | passed | 1117 passed; 14 optional Lua 5.3 tests skipped because lupa.lua53 is unavailable; formatting, Ruff, mypy, dependency consistency and strict OpenSpec passed. |
| Pinned OpenSpec validation | ./scripts/OpenSpec.ps1 validate --all --strict | 0 | passed | 30 items passed. |
| Diff whitespace check | git diff --check | 0 | passed | No whitespace errors; Git reported only existing CRLF-to-LF normalization warnings. |

The extracted current-session records are preserved only in ignored private evidence at reports/local/oracle-probe-20261019-db02b046.log. The complete game log and save files were not copied or committed.

## Real game

The operator said file 2 was selected and the player was in a room. The first snapshots showed the game paused and the same frame; later snapshots were active, with advancing frames and changing player positions. The capture crossed room visits 1 through 10. The probe sent no gameplay command, and movement source was not independently attributed. The process remained running after the Python client exited. No save, Steam Cloud, mod installation, approval, restart limit, or game setting was changed.

One observed ordering illustrates why the diagnostics remain candidates. At frame 7847, label 1 had entity_type 217 and HP 4.0; damage_attempt recorded requested=3.5. The first post_update_hp sample in that frame still read HP 4.0. The next-frame NPC-update sample still read HP 4.0, while a later-frame sample reported HP 0.5. In a separate sequence, entity_kill was logged at frame 7882 with HP -3.0, followed by entity_remove and npc_death at frame 7883. Three clean_award callbacks and nine new_room callbacks were observed, but those records do not prove that a room was cleared or that a reward was earned. Labels are diagnostic local labels, not verified spawn generations.

## RL evaluation

Not applicable. No training, model, reward, policy action, or achievement evaluation occurred.

## Limitations and continuation

This live run confirms that the installed observer invoked and recorded the listed callback candidates during ordinary play, including a later-frame HP change and an NPC kill/removal/death sequence. A single bounded run cannot establish universal callback ordering, per-hit attribution, stable entity identity, player death/revival, floor changes, terminal-game behavior, event delivery, or a safe transaction barrier. The 1024-record budget stopped diagnostics before the 120-second client cap; the exhausted window cannot be renewed by reconnecting in this mod load.

Episode-lifecycle tasks 3.6 and 3.8 remain open. Keep diagnostic facts separate from OracleEvent policy/reward input. The next safe work is offline: map these measured candidates against the existing OracleEvent contract, identify missing identity/ordering/delivery facts, and decide aggregate versus per-kind capability negotiation. Any additional runtime scenario needs its own explicit finite authorization and current readiness; this probe does not authorize training or further game control. Self-review found no source change and no claim beyond the captured session.
