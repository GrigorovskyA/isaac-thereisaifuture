# Proposal

## Why
The user explicitly prioritizes starting another run after death. Initial game launch and save-file-2 selection remain manual; unattended startup is deferred. This is a narrow lifecycle action, not authorization for player control or training.

## What Changes
Add an explicitly opted-in, bounded death-restart mode to the existing observer. Only a future confirmed game-over event can schedule the fixed native restart command. Keep ordinary observation read-only. Expose an attach-only terminal command and document deployment and real-game acceptance.

## Capabilities
### New Capabilities
- `post-death-restart`: negotiated, bounded restart after game over with cancellation and confirmation.
### Modified Capabilities
- `game-observation`: optional lifecycle capability alongside the unchanged default observation contract.

## Impact
Lua observer, Python handshake/configuration and attach CLI, offline tests, protocol guide, evidence and roadmap. No dependencies, Steam settings, save edits, input injection, RL, REPENTOGON, or application relaunch. User confirms the manually selected file; this does not prove slot identity or isolation.

## Acceptance Criteria
Offline guards and full project checks pass. On the approved manually selected file 2, a natural game over produces exactly one new run, confirmed by a fresh game-start event and increasing epoch, with user correlation. Disconnect and normal observation do not restart. Archive only after recorded runtime acceptance; unknown APIs remain unknown until tested.
