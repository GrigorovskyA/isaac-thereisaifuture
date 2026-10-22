# Evidence: manually prepared navigation attach check

User confirmed manual Steam/file-2/Continue/pause preparation. One attach-only
runtime test: random combat policy seed 21, at most 512 decisions, three minutes,
90 seconds per gate wait, zero tolerated infrastructure faults, one natural-death
restart, 512 MiB training tree cap. Production auto-navigation limits remain 80
action/release commands, 45 pulse seconds, four transitions, three stationary
pulses; no budget renewal, second invocation or PPO/checkpoint writes.

Initial read-only negotiated probe: session `0988d300010e472393186fd86da6182e`,
epoch 1/room visit 0, paused/alive. Navigation API telemetry exists: room index 82,
stage 1/type 0, ordinary room type 1, shape 7, zero currently open ordinary doors.
Screenshot shows paused combat with three hearts. Shape 7 is outside navigation's
1x1 scope: combat is allowed, but any clear-room navigation there must stop. A
natural restart, if it occurs, may supply a supported starting room; do not force
death/reset to arrange the test. File-2 identity relies on the user's preparation,
not independent slot attestation.

Source/installed main.lua and metadata match. Full t5120 model/normalizer reload
and identity match passed; fresh approval created only after confirming absence,
with exact hash retained for removal. Initial game capture refused foreground
focus once without injecting input; second capture passed after the bridge probe.
Private artifacts are in the directory named by
`reports/local/current-navigation-manual.txt`.

## Results

| Check | Status | Evidence |
| --- | --- | --- |
| Negotiated installed-game telemetry | passed | Actual Lua 5.3 observer 0.5.0-dev/game v1.9.7.17 accepted combat_navigation_v1; initial paused navigation object validated with shape 7/current index 82. No deployment during the running game |
| Fresh automatic combat readiness | passed | Runtime session `f97eac11475d4da5928eada7001f36b7`, epoch 1/visit 0. External menu Escape after setup, then fresh combat -> navigation_ready -> ready_accepted -> combat_resumed, existing request/context checks. Initial wait 17.859 seconds |
| Random combat | passed, integration only | 483 decisions, approximate return -11.500666666666564. Segment ended as empty with no fault. No terminal death/room-clear outcome was recorded; later room-clear or progression is not inferred |
| Geometry refusal | passed | Second reset observed empty and stopped as `NavigationStopped: Navigation supports ordinary 1x1 rooms only`; zero navigation actions and zero room transitions. Exit 0 indicates a handled stop, not target completion |
| Limits | passed | One invocation, 483/512 decisions, < three minutes, zero/one restarts, zero navigation commands/transitions. Training tree 201,993,739 bytes < 512 MiB. No second invocation or budget renewal |
| Gate cleanup | passed | Two handoffs, one accepted readiness; zero readiness rejections, resume races, observation gaps, withheld actions or cleanup errors |
| Input recovery | pause not verified | Two final menu attempts refused foreground focus before sending input. No successful pause or human-control recovery claimed. Switched to normal window closure, which requires no input injection |
| Final cleanup/lineage | passed | Normal window close, observer unload/successful shutdown log, game process/listener absent, exact SHA256-matching temporary approval removed. Full t5120 model/normalizer identity and latest pointer unchanged; post-close source/installed preflight passed |

Command: `live --mode random --seed 21 --steps 512 --minutes 3 --max-faults 0
--combat-gate --auto-navigate --gate-wait-minutes 1.5 --confirmed-save-slot 2
--connection-timeout 15`, project Python CLI; exit 0. Session logs:
`runs/live/sessions/20261020-074917-f00836/`. Console:
`reports/local/navigation-manual-console.txt`. Exact private directory:
`reports/local/navigation-manual-20261020-074844/` with setup, paused probe and cleanup.
Final game is closed, not left paused. No persistent UI/security/Steam setting changed.

## Interpretation and next action

Installed-game telemetry and automatic fresh combat readiness are now verified.
The requested door transition and subsequent combat are **not verified** because
the prepared run uses unsupported shape 7. OpenSpec task 2.2 remains unchecked;
no archive or training update. This is a scenario/geometry limitation, not a
transport connection failure. Next implementation must explicitly scope and test
support for narrow rectangular geometry (or a later bounded check must use a
supported 1x1 clear room). Do not pretend the shape guard proved navigation.

No production code changed in this attempt, so the full offline suite was not
rerun; the previously recorded 1819-test gate is historical offline evidence.
Runtime checks, parent reload, preflight and diff whitespace passed in this attempt.
Self-review retains the distinction between an observed empty segment, a native
clear event, a management stop and a completed target. Human intervention during
the test was not independently detected or ruled out.
