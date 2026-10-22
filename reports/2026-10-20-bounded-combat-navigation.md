# Evidence: bounded combat navigation

1x1 follow-up: nine accepted movement pulses reached room 81 from room 80, confirmed
by a separate read-only post-stop probe (visit 1 -> 2, unchanged health). Runtime
stopped early on a release/callback snapshot race; no combat readiness followed.
A bounded no-action reconciliation correction and regression tests were added
offline. Full runtime acceptance remains pending, including the destination's
unsupported shape 7. See [1x1 evidence](2026-10-20-navigation-1x1-check.md).

Follow-up manual attach: installed-game navigation telemetry and automatic fresh
combat readiness passed. Random controller executed 483 combat decisions, then
the gate stopped on unsupported shape 7 with zero navigation commands/transitions.
Task 2.2 remains pending: no door transition was observed. Exact cleanup and full
t5120 preservation passed; game closed normally after focus guards refused final
pause. See [manual attach evidence](2026-10-20-manual-navigation-check.md). The
startup failure below is the earlier attempt, not the follow-up result.

## Scope and recorded runtime budget

OpenSpec `bounded-combat-navigation`; primary Windows implementation, no delegation.
New opt-in management telemetry and same-client routing, preserving policy/reward/
checkpoint schemas and default operator gate. See proposal/design/delta specs.

One installed-game check after the final offline gate: existing file 2/Continue,
random combat policy (management/integration evidence only), seed 21, 512 decisions,
three minutes, 90 seconds per handoff, zero tolerated infrastructure faults, one
natural-death restart, 512 MiB training tree cap. At most 80 management action/release
commands, 45 pulse seconds, four transitions; three stationary pulses stop. No
forced death/reset, second invocation, budget renewal or checkpoint training.
Latest must remain t5120, with full parent identity/reload checked after cleanup.
Close Isaac before deployment; retain the previous observer main.lua backup/hash.
Launch through Steam, select file 2 and Continue using menus only. Gameplay stays
on the bridge. On completion stop input, pause/close normally, remove only the exact
matching temporary approval and verify process/listener absence.

## Offline checks

- Targeted Python plus production Lua 5.3 tests: 17 passed, exit 0, 1.97 seconds.
  Two earlier test assertions were corrected to use required LiveRunOptions
  constructor arguments and the actual fixture coordinate; no production behavior
  was weakened to pass them.
- First Check.ps1 invocation failed lint B009; corrected optional controller lookup.
- Full Check.ps1 then passed 1819 tests, zero skips, 44.92 seconds; Ruff/format/mypy,
  pip consistency and strict OpenSpec 31/31 passed. Existing isolated Lua test runtime
  on process-local PYTHONPATH and installed json.lua were used; no dependencies or
  persistent environment settings changed.
- Separate self-review found delayed transition counting could miss a room change.
  Count now follows every fresh management poll, including changes arriving after
  the pulse. Added an integration assertion; the next full gate passed in 43.74s.
- A boundary probe then found that Python Literal[1] also admitted boolean true.
  Added an explicit integer-only version validator and two malformed-version cases.
  Final full Check.ps1 passed, exit 0: 1819 tests, zero skips, 43.59 seconds,
  lint/format/mypy/pip and strict OpenSpec 31/31. Final whitespace check passed.

## Runtime and verification

| Check | Exit/status | Evidence |
| --- | --- | --- |
| Closed-game deployment | passed | PID 36960 closed normally; previous observer main.lua copied to ignored `reports/local/combat-navigation-main-before.lua`, previous/new hashes recorded in runtime setup JSON. Source-matching deployment/preflight completed before the one Steam launch |
| One runtime invocation | 2 / failed connection | `live --mode random --seed 21 --steps 512 --minutes 3 --max-faults 0 --combat-gate --auto-navigate --gate-wait-minutes 1.5 --confirmed-save-slot 2 --connection-timeout 60`. Listener session `runs/live/sessions/20261020-063440-dd3687`; `No Lua peer connected before accept deadline` |
| Startup delay | observed | Steam window showed Launching; Steam cloud log recorded upload timeouts and a launch sync. Two early game-window captures refused because no Isaac window existed; no input was injected. Isaac PID 12488 appeared after the connection wait had failed; intro image retained. Cloud/startup delay is an observed association, not proof of a specific Steam failure mechanism |
| File 2 / gameplay | not_run | Late launch never reached save selection/Continue in this attempt. No handshake, navigation telemetry, action, combat step, restart or training update; no save-profile/progression claim |
| Cleanup | passed | Late-starting Isaac closed normally without menu/gameplay input. Exact SHA256-matching temporary approval removed; process/listener absent. Full t5120 model/normalizer identity/reload and latest pointer unchanged; source/installed preflight passed. No second invocation or renewed budget |

Runtime telemetry, an actual transition and subsequent combat readiness remain
**not verified**. Task 2.2 stays unchecked; the change is not archived. The updated
observer is deployed but navigation remains opt-in. The next concrete action is a
new bounded attach test once Steam startup/Cloud sync is complete, using the same
unchanged t5120 lineage; this completed attempt grants no automatic retry.

Private setup/cleanup records: `reports/local/combat-navigation-runtime-setup.json`
and `reports/local/combat-navigation-cleanup.json`; console
`reports/local/combat-navigation-runtime.txt`. Large raw artifacts remain ignored.

## OpenSpec verification and separate self-review

Using openspec-verify-change for bounded-combat-navigation, schema spec-driven;
status/apply context and all five artifact files reread from disk after the delta
addition. Five of six tasks complete; runtime task 2.2 is deliberately pending.

| Dimension | Result |
| --- | --- |
| Completeness | 5/6 tasks; six ADDED/MODIFIED requirements implemented offline. Installed-game acceptance not verified: connection expired during startup |
| Correctness | Telemetry/filtering/default negotiation: navigation_wire.py, observer_client.py, live.py and production Lua tests. Bounds, fresh same-client handoff and learning separation: combat_navigation.py plus real-wrapper VecNormalize tests; existing stale/resume-race/readiness scenarios also pass in the full suite |
| Coherence | Opt-in CLI/wire mode, separate oracle metadata, unchanged encoder/config/checkpoint schemas, existing gate token validation, preserved original deadlines, unsupported geometry refusal. No screenshot planner in production |

CRITICAL before archive: incomplete runtime acceptance (task 2.2). Run a fresh
bounded installed-game check after normal startup and record actual transition
and fresh combat handoff; never substitute the Lua harness or process existence.
No other critical implementation issue found in checks that ran; zero outstanding
warnings/suggestions. Runtime behavior is not verified, so archive readiness is
not claimed. All unrelated dirty changes were preserved; no commit/push/delegation.
