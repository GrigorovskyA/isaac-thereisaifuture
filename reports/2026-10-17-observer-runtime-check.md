# Evidence: observer runtime check

- Date/time/timezone: 2026-10-17, Europe/Amsterdam (CEST).
- Starting revision: 6df189c3412f3c5ab33f8d7c81cd142a13051267.
- Scope: continue item 02 with actual read-only observation; no control/reset/RL.
- Authorization: user requested launch/check and then explicitly approved the
  current ordinary profile for observation after local backup, accepting that
  game startup may update saves. This is a **specific user-authorized exception**
  to the isolation prerequisite for this bounded read-only check, not proof of
  isolation or permission for future training, actions, resets or Cloud changes.
- Backup: 120 files across both Documents edition roots and the Steam app
  userdata root, verified copy hashes, stored under Git-ignored reports/local.
  Backup completeness for unknown external writes/restoration is not claimed.
- Target: installed Repentance+ v1.9.7.17; Steam build 22878971.

## Results

| Check | Command/scenario | Exit/status | Evidence |
|---|---|---|---|
| Deployment | Copy exact two approved observer files into mods/isaac_threrisaifuture_observer and compare SHA-256 | passed | Initial installed hashes match committed artifact plan; no existing directory overwritten |
| Launch | Steam Play UI | passed | Actual game process and fresh mod-script-load log |
| Manual gameplay | User reported ready; fresh log recorded current room transition | observed | No agent movement/shooting, reset or new-run command |
| First connection | Loopback Python observer, game without --luadebug | not established | Listener active, zero handshake/snapshots; cause not yet established |
| Diagnostics improvement | Bound errors to 300 characters, log through Isaac.DebugString when available, registration marker | offline passed | 16 Lua stub tests; running game not hot-patched |
| Repeat module probe | Relaunch with temporary --luadebug after user normal exit | passed for partial probe | Actual handshake and 300 snapshots; no persistent Steam/Cloud setting changed |
| State correlation / ten-minute soak | User-manual state and resource/response observation | incomplete | Initial 60.141-second capture does not complete acceptance |

## Real game and boundaries

Computer Use was stopped by the user's physical Escape key during manual
handoff. No further UI input was issued afterwards. User subsequently reported
ready; inspection continued through the existing Python listener and fresh logs.
The current run was not closed by the agent; user normal exit was requested
before a possible diagnostic relaunch. A missing --luadebug flag is a hypothesis,
not proof of the connection failure.

## Partial real result after relaunch

The user normally exited/saved and authorized relaunch. Diagnostic artifact
SHA-256 6C9D6D82AD81D7786CE96AE85D117228C39DC9CE762B8EC167F889EF8EA19577
was deployed while the game was closed. Actual process command line and fresh
log confirmed temporary --luadebug. No permanent Steam/Cloud option changed.
After user continuation, one real handshake and 300 snapshots were captured over
60.141 seconds: frame 2551 to 4138, 72 distinct positions, 2 room visits, 0 protocol
faults. Initial raw health was 6 red half-hearts, capacity 6, soul 0, bone 0.
Game metadata remained explicitly unavailable in the wire handshake; local
process/log identified the installed version separately.

Physical Escape stopped Computer Use again during manual gameplay. No further
Computer Use calls followed. The Python observer and memory sampler were stopped
and no loopback listener remained; game process stayed responsive/running.
The ten-minute soak, direct visual field correlation and reconnect acceptance
remain incomplete. This partial capture does not complete item 02.

## Continuation

The diagnostic-only patch is now tested (17 Lua stub tests in the 83-test full
offline run) and the deployed hash is in OBSERVATION_PROTOCOL. The later terminal
launcher probe is recorded separately in 2026-10-17-terminal-launcher.md. Keep
item 02 active while any acceptance check is missing. Do not silently replace
transport or install another native DLL.
