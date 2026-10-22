# Evidence: live-training-loop (offline, macOS)

- Date/time and timezone: 2026-10-18, Europe/Berlin (+02:00)
- Git revision and dirty status: HEAD 9a92e54; all changes uncommitted (commits are made remotely)
- Change scope and acceptance criteria: `openspec/changes/live-training-loop` (proposal, design, spec)
- Game/mod/bridge versions: source observer 0.5.0-dev (not installed); no game run
- Python/package versions and configuration hash: macOS venv Python 3.12; `configs/training-live-v1.yaml`
- Scenario, split, seeds, budget, and stop conditions: simulated game only (lupa stubs); tiny test configs

## Results

| Check/requirement | Command/scenario | Exit code | Status | Evidence |
|---|---|---|---|---|
| Lint, format, mypy (win32), pytest, OpenSpec strict | `ISAAC_JSON_LUA=... ./scripts/check.sh` | 0 | passed | 1219 tests passed; OpenSpec 25/25 |
| Training approval, `live_loop_v1` negotiation, oracle block, rejected acks, heartbeat release, restart budget/interval, approval across restart | `pytest tests/test_lua_live_loop.py` | 0 | passed | 31 cases; legacy Lua suites unchanged (371 Lua tests total) |
| EventDeriver, FaultTolerantEnv, approval writer, config exclusivity | `pytest tests/test_live.py` | 0 | passed | 18 cases |
| Real `main.lua` + `LiveClient` over loopback: actions, rewards, clear, death, autonomous restart, reconnect; `run_live` random and train (RecurrentPPO checkpoint) | `pytest tests/test_live_e2e.py` (repeated 3-6 times) | 0 | passed | 3 cases, stable |
| Windows gate | `./scripts/Check.ps1` | - | not_run | macOS has no PowerShell/Windows runtime |
| Deployment and real-game tasks 5.2-5.5 | see docs/LIVE_LOOP.md | - | not_run | requires Windows and Isaac |

## Real game

No real-game run took place. The simulated game is not Isaac evidence: stubs model
`HitPoints`, `IsClear`, `IsDead` and an engine restart that fires PRE_GAME_EXIT.

## RL evaluation

Not applicable; only a pipeline smoke (16 timesteps) ran on the simulated game.

## Limitations and continuation

- Real-game unknowns: HP semantics, IsDead/IsClear timing, consecutive restart stability.
- No game pause during PPO updates; approximate events (vanished enemy = kill).
- Self-review (not independent): diff checked against the delta spec; refusals keep
  sequence monotonic; replay still closes; legacy modes keep epoch binding.
- Next: Windows tasks 5.1-5.5 in `openspec/changes/live-training-loop/tasks.md`.
