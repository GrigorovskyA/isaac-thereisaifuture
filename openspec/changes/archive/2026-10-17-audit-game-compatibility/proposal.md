# Proposal

## Why

The project targets Repentance+; the initial installed manifest and historical log
identified Repentance. Selecting a bridge before checking source, saves, and runtime
requirements risks an incompatible integration or damage to ordinary progress.

## What Changes

- Deliver a read-only installed-game inventory and evidence-backed compatibility matrix.
- Audit pinned candidate source and licenses, including transport and callback blocking.
- Document save/Cloud isolation risks, runtime unknowns, and exact gated next actions.
- Recommend a minimal first integration and define the observation-only next task.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `game-environment`: make compatibility evidence levels and read-only audit
  completion explicit; require save/Cloud isolation evidence beyond a save slot.

## Impact

Documentation, OpenSpec requirements, evidence, and roadmap only. No production
dependencies, game installation, Steam settings, saves, bridge, or RL agent change.

## Scope and non-goals

Inspect local files/configuration/logs and current primary documentation/source.
Do not run downloaded code or launch the game. Runtime probes, installation,
input, resets, training, speed control, and full bridge implementation are excluded.

## Dependencies and risks

Depends on baseline tooling, readable Steam metadata, and accessible upstream
source. Historical logs cannot establish current runtime behavior. Repentance+
and REPENTOGON may require separate installation and save migration authorization.

The user subsequently authorized installing Repentance+ during the audit. Steam
completed the DLC installation and an already queued launch started the game.
The final inventory must reflect this change; no bridge probes are implied by it.

## Acceptance criteria

1. Matrix records installed build/branch evidence, DLC, mods/runtime, saves/Cloud,
   candidate commits/licenses/dependencies/blocking and required API capabilities.
2. Each runtime capability without an authorized real probe is explicitly unknown.
3. Recommendation compares reuse, adaptation, and a custom adapter with source evidence.
4. Required user actions and a concrete handshake/observation task are documented.
5. Evidence report separates passed offline inspection from blocked/not-run game
   checks; Check.ps1, change strict validation, and a separate self-review pass.

These are audit acceptance criteria. Completing this change does not establish
game compatibility or fulfill future runtime integration requirements.
