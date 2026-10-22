# Evidence: firing-cadence-diagnostics

- Date: 2026-10-19, Europe/Amsterdam.
- Baseline: 18f3e91, unrelated errors.txt preserved/excluded.
- Scope: extend existing default-off private callback trace with weapon cooldown
  and native tear correlation; no stat/input/reward/protocol/authority change.
- Game/mod: production observer source, offline simulated Lua 5.3 runtime for
  implementation; one separately authorized real-game comparison is recorded in
  `reports/2026-10-19-firing-cadence-runtime.md`.
- Python: existing Windows CPython 3.12.14 environment and isolated Lua 5.3/lupa
  harness; installed game resources/scripts/json.lua decoder.

## Results

| Requirement | Command/scenario | Exit code | Status | Evidence |
|---|---|---|---|---|
| Cooldown diagnostic contract | Focused production-Lua tests plus existing trace tests | 0 | passed | 36 passed, 0.34 s; 19 new cases |
| Private trace parser | Windows project Python 3.12: `python -m pytest tests/test_firing_trace.py -q -p no:cacheprovider` | 0 | passed | 150 passed, 0.17 s; includes trailing-whitespace and embedded-line-ending rejection |
| Full Windows quality gate | `scripts/Check.ps1` | 0 | passed | 1644 passed, 42.90 s; no skips/xfails |
| Lint/format/types/dependencies | Included in Check.ps1 | 0 | passed | Ruff; 105 formatted files; mypy 44 sources; pip consistent |
| Pinned strict OpenSpec | `scripts/OpenSpec.ps1 validate --all --strict` | 0 | passed | 31/31 |
| Real cadence comparison | One approved bounded empty-room test | 0 | passed | Task 4 result and limits: `reports/2026-10-19-firing-cadence-runtime.md` |
| Real input/tear/cooldown correlation and operator cleanup | Filtered current-session game trace; user-confirmed control and normal exit | 0 | passed | 114 valid records, 9 native tear callbacks, explicit release, approval removed, default-off source restored |

Full gate used the existing isolated Lua test runtime on PYTHONPATH,
ISAAC_JSON_LUA set to the installed decoder, and a private ignored
reports/local directory for TMP/TEMP. No environment/dependency changes or skips
were used to pass. The parser summary and source-level review are recorded in
reports/2026-10-19-firing-trace-parser.md. The separately authorized runtime
result is documented at `reports/2026-10-19-firing-cadence-runtime.md`; the
single test does not authorize a repeat or a gameplay-stat change.

## Design and behavior

Existing callback_trace remains false. When explicitly enabled, input records for
shooting buttons append fire_delay/max_fire_delay; matching controlled-player
native tear callbacks may emit fire_tear with the same fields and correlation.
Only finite numeric values within +/-1000000 are formatted (six significant
digits); missing/invalid values are na. No property writes, spawning or input
forcing beyond the unchanged approved command path. No new policy/wire field.

One nonrenewable ten-second/512-attempt/300-byte trace budget remains unchanged.
Count/line stops can occur earlier. Diagnostic property/sink/recursive failures
stop diagnostics, not input or cleanup. Existing held/frame/wall expiry and
heartbeat/disconnect/death/transition semantics remain intact. The existing
first-four-tears-per-hold logging guard also bounds fire_tear records; trace
absence is not physical shot absence. See docs/FIRING_CADENCE_DIAGNOSTICS.md.

## Self-review

Reviewed actual Lua and test diff against both new requirements. Production
changes only read cooldown properties inside existing protected diagnostic work;
trace off avoids reads entirely. Fault tests preserve input and expiry/disconnect
cleanup; recursive getter disables trace. Existing trace suite verifies deadline,
reconnect nonrenewal and sink behavior. Tests use real production Lua with stubbed
engine callbacks; they do not establish the installed engine's callback order,
actual weapon firing rate or physical neutrality. No dependency/architecture,
reward, schema, model, save, launch or restart-limit change.

## Limitations and continuation

Task 4 was completed in one separately authorized <=30-second/16-command
stationary comparison (3 vs 6 held game frames), with zero restarts/training,
manual launch/file-2 selection/exit, a finite action approval and unconditional
release. Results and limits are in `reports/2026-10-19-firing-cadence-runtime.md`.
The default-off source was restored after the game closed, and the OpenSpec change
was archived at `openspec/changes/archive/2026-10-19-firing-cadence-diagnostics`.
The observations do not establish maximum-rate loss. A repeat, stat adjustment,
or frozen-policy comparison is a separate experiment requiring its own finite
authorization.
