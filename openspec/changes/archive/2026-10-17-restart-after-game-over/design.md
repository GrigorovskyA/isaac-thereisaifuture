# Design

## Context
See proposal.md. Native J460 observation works; REPENTOGON is absent. The active slot cannot be attested by the current protocol. Initial launch/selection are manual.

## Goals / Non-Goals
Provide a bounded first lifecycle integration. Do not reset live runs, drive the character, run training, automate menus, or relaunch the executable.

## Decisions
- Add optional `death_restart_v1` to protocol/schema 1 capability negotiation; default clients still request only the three read-only capabilities. Require explicit CLI opt-in and operator confirmation of file 2. An older peer must fail negotiation. No commands after hello and no arbitrary console endpoint.
- Arm only after the complete acknowledgement is sent. MC_POST_GAME_END(true) schedules a restart 1500 ms later for the connection session and game epoch. False means an ending and cancels. Zero health and transport errors are not death evidence.
- At dispatch require the same active session/epoch, exactly one player, and IsDead(). Cancel if revived, disconnected, exited, unloaded, changed run, expired, or delayed more than five seconds. Process transport before lifecycle work.
- Execute only Isaac.ExecuteCommand("restart"), once per ended epoch. Count the attempt before dispatch; do not retry a failed/uncertain command. MC_POST_GAME_STARTED with IsContinued=false and increased epoch confirms it. A five-second confirmation timeout disables the mode for the mod lifetime. Preserve pending confirmation through the restart's game-exit callback, but disarm connection authority.
- Three attempts and a ten-minute lease per mod load, starting at first opt-in handshake; reconnect never refreshes either. These are explicit experimental limits, not a permanent campaign supervisor.
- Keep snapshots unchanged. Bounded native diagnostics record scheduling, dispatch, confirmation and faults; snapshots correlate the new epoch. Python Ctrl+C closes sockets. It does not kill the game.

Alternatives: HP polling misclassifies revival; always-on reset lacks session authorization; external key injection violates the structured integration goal. A separate always-on mod could also affect other manually selected files.

## Risks / Trade-offs
Native callback/restart behavior on J460 is not runtime verified yet. Test only after closed-game deployment and operator-selected file 2; never force death. Debug/mod achievement eligibility and full profile isolation remain unknown. A loopback process is trusted, not an authentication boundary. Operator confirmation is not automated slot attestation.

## Migration Plan
Back up the two installed observer files while the game is closed, update to 0.2.0, hash-check them, then attach in opt-in mode only after manual selection. Default observation remains inert. Roll back those two files only while closed; never restore or edit saves as part of this change.

## Sources
Checked 2026-10-17: https://wofsauge.github.io/IsaacDocs/rep/enums/ModCallbacks.html (MC_POST_GAME_END, MC_POST_GAME_STARTED); https://wofsauge.github.io/IsaacDocs/rep/tutorials/DebugConsole.html (restart retains current character); https://wofsauge.github.io/IsaacDocs/rep/Isaac.html (ExecuteCommand). These API references inform implementation, not runtime acceptance.
