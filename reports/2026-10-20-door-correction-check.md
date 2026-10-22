# Evidence: minimum-lease and doorway correction check

User requested another real check. One attach-only production random-policy
seed-21 invocation, at most 512 combat decisions, three minutes, 90-second gate
wait, zero tolerated infrastructure faults, one natural death restart, 512 MiB
training-tree cap. Navigation: 256 commands, 90 pulse seconds, four transitions,
three stationary pulses. No PPO update, second invocation or automatic renewal.

Preflight: existing PID 45728, Repentance+ v1.9.7.17, paused ordinary room 81,
shape 7, position (1089.7366943359, 288.58288574219), four red half-hearts.
Installed Lua/metadata match source; no deployment. Full t5120 identity/model/
normalizer reload and latest pointer verified unchanged. Temporary approval hash
and initial read-only probe retained in reports/local/door-correction-20261020-083850/.
Fresh route memory uses the production exit selector; no forced route selection.

## Runtime result: failed before gameplay

Production CLI returned exit 2 during handshake: `Peer closed before a complete
record`. Session log: runs/live/sessions/20261020-084027-0cc7d6/; console:
reports/local/door-correction-console.txt. Game log explicitly reports
`Observer capability/protocol fault: ... main.lua:814: Too many capabilities`.
Zero gameplay commands, navigation transitions, combat decisions or PPO updates.
The minimum-lease/crossing fix remains not run in this attempt.

Source inspection: hello loads local authorization only while approval_loaded is
false; load_action_authorization returns immediately when Config already holds
an authorization. Expiry suppresses safe_actions/live_loop/navigation capabilities.
The process survived the previous finite run, so replacing the authorization file
did not replace its cached lease. An expired prior lease is the supported causal
inference; the exact cached expiry was not exported. The successful initial probe
does not establish that a new on-disk lease was loaded or will cover the run.
Do not weaken expiry/capability checks or hot-reload authority to avoid this error.

Recovery: capture confirms visible pause menu, two full hearts, same doorway.
No menu/gameplay input or second invocation. Exact temporary approval removed;
full t5120 model/normalizer reload, identity and latest unchanged. No port-9528
listener; PID45728 left open paused. Disk 202,020,838 bytes <512 MiB. Cleanup saved
to the private artifact directory. Human intervention/recovery was not measured.

## Verification and next action

Documentation-only follow-up; production source unchanged, no deployment.
Previous full offline gate remains 1893 passed, zero skips; it was not rerun for
this report. Separate self-review confirms failure is not counted as traversal
or acceptance. OpenSpec task2.2 and all-shape native coverage remain unfinished.
Next finite check must normally close/relaunch Isaac with the new approval already
present, select file2/Continue, then attach and test crossing plus fresh combat.
Never infer a fresh cached authority solely from the replacement file or an old
process's successful probe. No second run or budget renewal in this attempt.
