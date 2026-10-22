# Evidence: negotiated diagnostics without patched builds

- Date/time and timezone: 2026-10-18, Europe/Amsterdam.
- Git revision: based on aba77f4; code/spec/tests/docs reviewed before commit.
- Scope: activate the existing passive probe through explicit oracle_probe_v1 negotiation, preserving default observation and all per-mod-load budgets.
- Game/mod: observer 0.4.3-dev source installed while closed; no game session started.
- Python/packages: existing CPython 3.12.14, pytest 9.1.1; dependencies/locks unchanged.
- Scenario/budget: simulated peers, production Lua harness and fake CLI clock; Lua 120 s / 1024 attempts / 128 labels / 400 bytes. CLI <=600 samples / 120 s from attach, one in-progress receive <=3 s, zero reconnects.

## Results

| Check/requirement | Command/scenario | Exit code | Status | Evidence |
|---|---|---|---|---|
| Lua and Python negotiation | .venv/Scripts/python.exe -m pytest tests/test_lua_oracle_probe.py tests/test_oracle_negotiation.py -q | 0 | passed | 41 cases; later invalid-hello coverage also included in full gate |
| CLI bounds and closure | .venv/Scripts/python.exe -m pytest tests/test_oracle_cli.py -q | 0 | passed | 10 cases |
| Full Windows gate | ./scripts/Check.ps1 with environment below | 0 | passed | 918 tests, zero skips; Ruff, 83 formatted files, strict mypy on 37 sources, pip consistency, OpenSpec 24/24 |
| Closed-game deployment | Check process/approval absence and old hashes; back up; copy two reviewed source files; compare SHA256 | 0 | passed | New source/installed hashes below |
| Stable launcher verification | ./Start-Isaac.cmd --preflight-only | 0 | passed | No process launched; no diagnostic hash exception needed |
| Live negotiated activation | Manual game launch and explicit diagnostic hello | N/A | not_run | The new activation path is offline-verified only; earlier combat evidence used 0.4.2-dev |

Full-gate environment:

```powershell
$env:PYTHONPATH='C:\Users\<user>\Documents\Codex\2026-10-17\work-on-isaac-threrisaifuture-in-the\work\lua-test-runtime'
$env:ISAAC_JSON_LUA='C:\Program Files (x86)\Steam\steamapps\common\The Binding of Isaac Rebirth\resources\scripts\json.lua'
$env:TMP=Join-Path (Get-Location) 'reports\local\check-native-protocol'
$env:TEMP=$env:TMP
.\scripts\Check.ps1
```

An initial Ruff check found one long Lua harness string in Python; it was split
before the full gate. No failing check was removed or weakened.

## Design and self-review

The base hello shape/protocol version is unchanged. Python appends the capability
only for strict boolean ObserverConfig.oracle_probe=True. CLI observe --oracle-probe
uses the same path. Lua advertises it only when the callback identifiers exist
and the mod-load window has not started/ended. An unsupported/exhausted request
faults without fallback; ordinary observation stays available. Diagnostic facts
remain in separate logs, never policy snapshots or wire outcome events.

The source flag/private patched-build flow was removed. Diagnostic callbacks are
registered when available but perform no diagnostic reads/logging on default
attach. Damage/award callbacks still return nil. Action/restart/native-step
combinations are rejected; entity observation may combine through the API.
Diagnostic start/failure/stop never renews action or restart authority.

Tests cover default inactivity even with failing read APIs, default disconnect
followed by first explicit attach, invalid hello without consuming the window,
unsupported peers, strict opt-in, mixed-mode rejection, explicit exhausted
reconnect rejection followed by successful ordinary observation, and existing
count/time/label/logger/read/cleanup behavior. CLI tests cover actual 600-record
capping, absolute loop deadline, timeout/reconnect rejection before opening a
socket, protocol fault and Ctrl+C closure, and unchanged ordinary sample counts.

Specification mapping: the seven passive-probe scenarios map to these behavioral
tests plus existing partial-step fault tests. The component is coherent with
the updated design. Completeness stays 12/19 whole tasks; runtime outcome/export,
terminal-step acceptance, attach barrier, real backend and 100 real episodes are
unfinished. No archive readiness is claimed.

## Installation and real game

No Isaac process or private action approval existed. Previous source-matching
0.4.2-dev hashes were checked before copying; private backup:
reports/local/oracle-negotiation-deployment-b3d88b50d90f4191bb029f1d8274d001/.

Source/installed SHA256:

- main.lua: 2b7c1ec56e1b42d7150fe7583596df605cf4af19f210a0e1fdd4ebea66a21752.
- metadata.xml: b50d5666d874596a2960364e1288e16e2845c96a12eacd3345884577dd35542f.

Mode switching no longer changes these files. Normal preflight passed without
starting the game. No save, Cloud, other mod, options, approval or executable was
changed. Startup, slot selection and normal exit stay manual. No input or reset
was supplied. Existing action/restart limits and training-isolation gates remain.

## RL evaluation

Not applicable; no training, outcomes, reward attribution or achievement claims.

## Limitations and continuation

Actual 0.4.3-dev negotiation/diagnostic start still needs a manual runtime check.
This does not validate HP realization: the measured NPC-update counterexample
remains valid. Next implementation work is a bounded end-of-update HP sampling
experiment, with cancellation, concurrent effects, negative death HP and source
attribution kept unknown. Death/revival/floor coverage and exact native input
completion remain unverified. Future code upgrades still require closed-game
installation; only diagnostic mode switching is now free of file replacement.
