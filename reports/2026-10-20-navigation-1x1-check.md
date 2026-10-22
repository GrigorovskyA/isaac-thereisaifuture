# Evidence: user-prepared ordinary 1x1 navigation check

User prepared file 2/Continue and an ordinary room for a new finite check. Initial
probe expected pause and raised an assertion: actual state was active, alive and
cleared. Readback confirms supported ordinary shape 1, room index 80, epoch 1/visit
1, player x253.556/y258.933, four red half-hearts; open ordinary exits slots 2
(600,280) and 3 (320,440). No action was sent by the probe. This active clear state
is an eligible navigation starting state, so no menu unpause is required. Initial
capture refused foreground focus without injecting input; no screenshot is used
to choose the route.

One production attach invocation: random combat seed 21, <=512 combat decisions,
three minutes, 90-second handoff waits, zero tolerated infrastructure faults,
one natural-death restart, 512 MiB training tree cap. Navigation limits remain 80
action/release commands, 45 pulse seconds, four transitions, three stationary
pulses. No second invocation, budget renewal, forced reset, policy training or
checkpoint writes. Source/installed observer match and full t5120 reload/identity
passed; exact temporary approval hash recorded after confirming no prior approval.

## Runtime results

Production invocation exited 0 at a handled navigation stop, after 2.500 seconds
of management wait. Session `runs/live/sessions/20261020-075413-18f559/`, connection
`f191c6c4e5a245ea8e1bb0b763bb901f` (recorded hello identity).
The route chose exit slot 2 and issued nine accepted no-shoot movement pulses
(first down four frames to align, then right six frames per pulse). Eight releases
were accepted; ninth was rejected while Python's last snapshot still named visit 1.
Stop reason: `NavigationStopped: Navigation release rejected in the same room`.
No neutral acknowledgment is claimed for the rejected release. Zero combat
readiness acknowledgments/decisions, zero death restarts, no cleanup errors.

A separate post-stop **read-only** probe confirms actual native transition:
epoch 1/visit 2, room index 81, position (80,280), shape 7, same four red half-hearts.
Initial room index was 80. This proves crossing the right door even though the
manager's in-run transition counter remained zero. Reconnecting changes session
identity, so this readback is reported separately and never reused as an action
authorization. It does not establish readiness or combat in the destination.

One final menu pause attempt refused foreground focus without input injection.
The game was then closed normally; process/listener absence, exact approval
removal, full t5120 model/normalizer identity/reload and preflight passed. Disk tree
201,999,617 bytes <512 MiB. Private directory is named by
`reports/local/current-navigation-1x1.txt`; it retains setup, initial/post-stop
probes and cleanup. No second gameplay invocation or renewed budget followed.

## Offline corrective work

The stop exposes a real callback/snapshot race: release can be rejected before the
new-room snapshot arrives. Add a bounded <=0.5-second read-only reconciliation,
under original gate/run and cumulative pulse budgets. Require a fresh later visit
in the same session/epoch with unchanged health. No additional movement, retry or
successful release is inferred. Same-room/unknown/damaged/foreign state still stops.
Design and delta scenario updated. Targeted correction tests passed: 19 tests,
exit 0, 2.72 seconds. An initial version of the correction surfaced an incorrect
timeout label (reconciliation cap treated as operator-wait expiry); targeted and
full suite failed that regression. The correction now preserves the original
deadline's classification and labels an unconfirmed release as the management
stop. Final Check.ps1 passed, exit 0: 1821 tests, zero skips, 47.94 seconds;
Ruff/format/mypy/pip and strict OpenSpec 31/31 passed. No failed invocation counted
as passing. Existing isolated Lua runtime and installed JSON codec were selected
through process-local environment variables; no dependency/settings changes.

Runtime task 2.2 remains open: door crossing is proven, but transition handling
and subsequent fresh combat readiness are not accepted. No training/improvement
claim; no archive. The next room's unsupported shape 7 is also still outside scope.

Human intervention during the test was not independently detected or excluded.
No successful final pause/manual-control recovery is claimed. Final state is game
closed, approval absent and t5120 intact. No post-fix game invocation occurred.

## Separate self-review and OpenSpec verification

Status/apply context and all artifacts reread for bounded-combat-navigation.
Five of six tasks complete; six ADDED/MODIFIED requirements remain mapped to the
implementation and passing behavioral suite. The new race scenario maps to
`_confirm_transition` and the delayed-same-epoch/foreign-epoch regression tests;
the existing same-room-release test verifies failure after the bounded wait.
Reconciliation does not issue commands, renew deadlines, bypass health/session
validation, fabricate neutral acknowledgment or enter learner accounting. Design,
delta scenario and usage agree. Final diff whitespace/strict validation passed.

Critical before archive: task 2.2, post-fix installed-game transition handling and
subsequent fresh combat readiness, remains not verified. Do not archive or claim
an unattended series of fights. No other implementation warning/suggestion found
in this review. Destination shape 7 remains an explicit coverage limitation; narrow
room support requires a separately scoped extension, not removal of the guard.
