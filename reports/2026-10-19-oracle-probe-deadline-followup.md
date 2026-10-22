# Evidence: passive oracle probe deadline follow-up, 2026-10-19

- Date/time and timezone: 2026-10-19, Europe/Amsterdam; probe started at approximately 18:44 local and stopped at its configured deadline.
- Git revision and dirty status: `25f9f5e` at probe start. Existing edits to `AGENTS.md`, `docs/AGENT_WORKFLOW.md`, `reports/2026-10-19-oracle-probe-live-runtime.md`, `subagent.md`, `subagent_report.md`, `errors.txt`, and wait scripts were preserved.
- Change scope and acceptance criteria: one bounded, passive diagnostic attach to determine whether this ordinary live session produced additional native callback facts. This is diagnostic evidence only; no Lua/Python behavior, command authority, training, save state, or OpenSpec acceptance changed.
- Game/mod/bridge versions: installed `isaac-ng.exe`, PID 40528, process start 2026-10-19 18:43:21 +02:00; hello acknowledged observer `0.5.0-dev`, Lua 5.3, protocol/schema 1. Game version was unavailable. The operator-selected save/room is not independently attested by this observer.
- Python/package versions and configuration hash: Python 3.12.14; no learner, model, reward, or configuration was used.
- Scenario, split, seeds, budget, and stop conditions: one read-only attach with `--oracle-probe --samples 600 --accept-timeout 60`; no reconnect, action, restart, menu input, forced death, reset, spawn, or damage. Client ended on its deadline.

## Results

| Check/requirement | Command/scenario | Exit code | Status | Evidence |
|---|---|---:|---|---|
| Explicit diagnostic handshake | `.\.venv\Scripts\python.exe -m isaac_threrisaifuture.cli observe --oracle-probe --samples 600 --accept-timeout 60` | 0 | passed | Hello acknowledged `oracle_probe_v1`; session `8df2eb16fecc4a3790bea235caeda814`; snapshots reported game epoch 3. |
| Bounded observation | Same command, one connection | 0 | passed | 599 validated snapshots, sequence 1–599, frames 1423–5020; snapshots remained `active`. Client stopped at its configured deadline. |
| Scene context | Aggregate `post_update` fields from the same private session log | 0 | passed | All 599 reads reported `paused=false`, `clear=true`, and `dead=false`; room visit stayed 1. No room transition was recorded. These are game state flags, not an entity census. |
| Native diagnostic record bounds | Filter exact `[Isaac Future OracleProbe]` prefix and this session ID; ignored local evidence only | 0 | passed | 601 records, contiguous IDs 1–601; `attach` 1, `post_update` 599, `stop` 1 (`reason=deadline`); largest UTF-8 line 232 bytes. No other callback kinds were recorded in this session. |
| Observer and game cleanup | Observer exit and port/process readback | 0 | passed | Python observer exited normally; port 9528 had no listener; Isaac remained running. No game command was sent. |
| Combat/lifecycle callback evidence | Review only this session's filtered native records | N/A | not_run | No damage, entity, room-transition, player death/revival, floor, or terminal callback was observed. The game reported the room clear throughout; this session did not exercise combat callbacks. |
| Windows quality gate | `./scripts/Check.ps1` with `TEMP`, `TMP`, and `TMPDIR` set to ignored `reports/local/check-tmp-oracle-followup-20261019-01` | 0 | passed | 1248 passed, 14 skipped; Ruff, format, mypy, dependency consistency, and OpenSpec passed. The 14 skips require optional isolated Lua 5.3 runtime. |
| Pinned OpenSpec validation | `./scripts/OpenSpec.ps1 validate --all --strict` | 0 | passed | 30 items passed. |
| Diff whitespace check | `git diff --check` and report whitespace scan | 0 | passed | No whitespace errors in the tracked diff or new report. |

The filtered native records are in ignored private storage at `reports/local/oracle-probe-8df2eb16fecc4a3790bea235caeda814.private.log`. The client transcript is also ignored. Neither the full game log, saves, nor private session data was added to Git.

## Real game

The live game process was already running; this probe neither launched nor stopped it. The observer established a new diagnostic session and advancing snapshot frames but did not verify save-slot identity. Its game-state flags reported an unpaused, already-clear room for all 599 snapshots, with no room transition. It supplied no movement or shooting input. No game state was intentionally changed. Isaac remained running and the observer listener was gone after the bounded client exit.

## RL evaluation

Not applicable. No training, policy action, reward, checkpoint, or achievement evaluation occurred.

## Limitations and continuation

Source review explains the result. `probe_update()` emits a regular `post_update` record every 200 ms. Other records are callback-triggered: for example, `damage_attempt` requires `MC_ENTITY_TAKE_DMG`, `npc_init` requires `MC_POST_NPC_INIT`, and `new_room` requires an actual room transition. `npc_update_hp` is not a per-frame entity census; it is emitted only for a target already queued by a damage attempt or NPC initialization. In this session `clear=true` throughout, the room visit stayed constant, and the probe supplied no game input. Thus no combat-triggering callback was evidenced; the output is consistent with the implementation and does not indicate a broken logger.

This session confirms the handshake, regular snapshot path, and bounded cleanup only. It yields no combat or lifecycle coverage and cannot advance event coverage, producer eligibility, delivery, episode completion, or tasks 3.6/3.8. The absence of callbacks is not a negative game event. To collect combat facts, a separately authorized probe must observe an uncleared room while the relevant callbacks occur; reconnecting cannot renew this load's diagnostic window.

Self-review: the report contains only bounded aggregate facts and the session identifier; private logs remain ignored. Existing unrelated worktree changes were not edited or staged.
