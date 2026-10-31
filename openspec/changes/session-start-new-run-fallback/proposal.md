## Why

The reward v11 / schema 9 run stopped at t253952 on an automatic lease rollover. Session 2 ended
3 s after a death (episode 595), before the death restart had started a new run, so file2 had
no saved game. Session 3 then refused to start: `MenuEntryError: Existing file2 game state not
confirmed; no New Run fallback`. The user authorized (2026-10-31) that a pure-profile session may
start a New Run on file2 when file2 has no game to continue.

## What Changes

- `menu_entry.enter_file2` gains mode `continue-or-new`: after the file2 selection is confirmed,
  it continues when the fresh log shows a loaded file2 game state, starts a New Run when the log
  verifies `No Game State detected` for file2, and stops with no input otherwise (no evidence or
  contradictory evidence). It records `menu_entry_resolved`. New function
  `continue_or_new_run_file2`.
- The pure supervisor session (`session_runner`) uses `continue_or_new_run_file2`.
- Docs: `docs/RUNTIME_AUTHORITY.md` (standing authority), `docs/TRAINING_SESSION.md`.

## Non-goals

- No change to the contract (hash `7c016069...` stays), observation, reward, actions or Lua.
- An existing Continue is never replaced: the explicit replacement path stays separate.
- The launcher modes `continue` and `new-run` are unchanged.
- No retry after a menu fault and no change to the fault cap.

## Acceptance

- Offline gate and strict OpenSpec validation pass; tests cover Continue when a game exists, New
  Run on verified absence from each start slot, and a stop without game-state evidence.
- Native: the next lease rollover after a death at the lease end starts a New Run and training
  resumes from `latest`.
