# Tasks

## 1. Negotiated mode
- [x] 1.1 Add explicit attach CLI opt-in and slot-2 confirmation, keep defaults read-only, and test capability rejection by older peers.
- [x] 1.2 Document attach commands, budgets, manual startup and unknown slot identity in the protocol and lifecycle guide.

## 2. Lifecycle guard
- [x] 2.1 Implement session/epoch-bound delayed game-over restart and confirmation; test default, victory, revival, duplicates, disconnect, exit, expiry, limits and uncertain dispatch with simulated Lua.
- [x] 2.2 Update version/provenance and evidence; verify project checks and strict OpenSpec validation, then perform separate self-review and verify workflow.

## 3. Real-game acceptance
- [x] 3.1 Deploy the reviewed adapter only after normal game exit, back up installed mod artifacts and verify hashes; preserve all saves/settings.
- [x] 3.2 On operator-confirmed file 2, observe a natural game over and exactly one fresh run, log session/epochs/confirmation, verify disconnect/default behavior and user responsiveness, and record results.

## Workflow follow-up
- Archive only after all acceptance tasks pass. Commit and push project files without private logs or saves.
