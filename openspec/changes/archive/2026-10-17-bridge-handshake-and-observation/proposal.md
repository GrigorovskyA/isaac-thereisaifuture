# Proposal

## Why

The completed audit selected an original LuaSocket adapter, but Python cannot
observe the game yet. A small read-only slice establishes the protocol before
any character control or reinforcement learning.

## What Changes

- Add a bounded Lua observer, typed Python listener/client and observe CLI.
- Add a bounded observation launcher with a visible terminal and local logs;
  start the listener before the game without screen capture or injected keys.
- Preserve the observation process across bounded transport reconnections; a user
  death/restart closing the peer must not immediately terminate the session.
- Specify protocol/observation v1, availability, health units, identities and faults.
- Add offline socket-peer and Lua-stub behavioral tests, deployment/rollback plan
  and separate real-game acceptance evidence.

## Capabilities

### New Capabilities

- `game-observation`: negotiated read-only game snapshots and connection lifecycle.
- `observation-launcher`: explicit process launch, bounded logging and owned-process cleanup.

### Modified Capabilities

None. Existing game-environment safety/isolation requirements remain in force.

## Impact

New source under src and mod, CLI, tests and documentation. Use existing Pydantic
and Python standard library; no new production dependencies or second transport.
No actions, RPC, console, reset, item spawning, hidden map state or RL.

## Dependencies and risks

Bundled LuaSocket/json files and baseline API references exist on installed
Repentance+ J460 / build 22878971; actual module loading and callback behavior
were initially unverified. Later authorized probes established socket loading and
partial observation with temporary --luadebug. The user's explicit ordinary-profile
read-only exception after backup is recorded in the runtime reports; it does not
establish training isolation or authorize future actions/reset/Cloud changes.

## Acceptance

1. Protocol, typed client, Lua observer and CLI implement the delta with meaningful
   offline behavioral tests and bounded error handling.
2. Check.ps1, targeted tests and OpenSpec strict validation pass; separate
   self-review and evidence distinguish simulated peers from game observations.
3. Authorized real handshake reports actual version provenance/session; active
   game frames advance and coordinates/health/room agree with manual gameplay.
4. Ten-minute authorized observation soak, disconnect/reconnect and Python
   shutdown leave the game responsive without evident resource growth.

Criteria 3–4 stay incomplete when deployment/isolation is blocked. Do not archive
or mark roadmap item 02 complete on offline evidence. Stop before safe actions.

5. The launcher discovers a Steam library or accepts an explicit game directory,
   validates the deployed observer, refuses a running game, opens the observer
   before launch, exposes logs and closes only observer resources on interruption.
   Offline guard checks and a separately recorded authorized real launch are required.
   File-2 automatic selection remains unknown; print that limitation explicitly.
