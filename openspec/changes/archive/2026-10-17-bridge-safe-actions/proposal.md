# Proposal

## Why

The accepted observer and bounded death restart cannot safely hold player inputs.
Roadmap item 03 needs a fail-closed native input contract before real control.

## What Changes

- Add optional safe_actions_v1, independent cardinal movement/shooting, neutral,
  release, heartbeat, bounded expiry and session/epoch/frame/room validation.
- Add strict Python messages and a bounded attach-only client; no automatic launch.
- Gate Lua capability on a local reviewed profile/slot authorization record. Ship
  this gate disabled: isolation, active-slot evidence and runtime permission are absent.
- Preserve default observation and existing mutually exclusive bounded restart.
- Add offline Lua/socket tests, protocol, prerequisite plan and honest runtime evidence.

## Capabilities

### New Capabilities

- `native-player-actions`: gated input negotiation, commands, expiry and cleanup.

### Modified Capabilities

- `game-environment`: record the user-approved ordinary-profile exception for bounded action tests; training isolation remains required.
- `game-observation`: allow the narrowly negotiated safe-action endpoint while
  preserving read-only defaults and existing death-restart constraints.

## Impact

Observer Lua, Python bridge, tests and documentation; no new production dependency.
No RL, Gymnasium, screen capture, desktop injection, save edits, Cloud changes,
REPENTOGON, supervisor or relaxation of reset limits. No deployment in this task
without resolved prerequisites and specific runtime authorization.

## Dependencies, risks and acceptance

Isolation requires an approved profile covering shared settings, mods/data, Cloud,
save synchronization and verified restoration. A separate slot is insufficient.
Active file 2 needs evidence tied to the actual game instance and epoch; native
slot API availability remains unknown. Ordinary-profile permissions exclude inputs.
Native MC_INPUT_ACTION semantics have documentation evidence, not live acceptance.
Offline acceptance requires strict command, stale/replay, expiry, reconnect and
cleanup tests plus Check.ps1 and strict validation. Runtime acceptance requires
50 controlled sequences with actual position/shooting effects and release after
disconnect and Python failure. Blocked runtime tasks prevent archive and item-03
completion; independent offline implementation is explicitly authorized now.

## Authorization amendment (2026-10-17)

The user explicitly approved movement and shooting directly on their ordinary
profile and asked to retain that permission for future bounded checks. This
supersedes the earlier isolation-only prerequisite for these tests. It does not
establish isolation or authorize training/save/Cloud changes, resets or startup.
Current instance and operator-confirmed active slot 2 remain required. Add a
private expiring local approval record, 120-second per-mod-load action lease and
native tear/release diagnostics so this authority is finite and observable.
