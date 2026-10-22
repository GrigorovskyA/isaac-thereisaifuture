# Deferred unattended startup

On 2026-10-17 the user deferred fully automatic application launch and save-file
selection as minor issues. Current priority is bounded automatic run restart
after natural game over; initial game launch and file-2 selection remain manual.
This is research context, not an active implementation change.

# Earlier proposal retained as deferred research

## Why

The earlier requested target was one invocation to launch Isaac, select file 2, continue its run
and connect the observer without human menu input. The existing launcher already
executes isaac-ng.exe directly with --luadebug; Steam still requested confirmation.
Changing from a Steam URL to a binary is therefore not a fix for this installation.

## What Changes

- Define an unattended startup state machine, trusted slot readback and readiness.
- Preserve existing read-only/manual launch while the new mode is unverified.
- Research a supported native route first; compare a separate REPENTOGON trial.
- Keep failures explicit instead of guessing menu timing, using screenshots,
  sending desktop keys, overwriting saves or silently choosing a different slot.

## Capabilities

### New Capabilities

- `unattended-startup`: bounded launch-to-approved-slot readiness without human input.

### Modified Capabilities

None yet. The existing observation-launcher remains a truthful manual-mode entry
point. Its contract will be reconciled explicitly when a verified new mode exists.

## Impact

Future launcher, startup adapter, slot-aware readiness and tests. No runtime or
mod installation, save migration, Steam settings change, run reset or training in
this discovery phase. Existing observation protocol v1 has no slot attestation;
do not silently reinterpret it as containing one.

## Dependencies, decisions and risks

No native file-selection API/argument is verified on installed J460. Binary
string inspection found the known stage/room/debug flags, not a save-slot flag;
absence of a string is not proof that no undocumented option exists. Stage/room
flags can start a different run and must not be used as an unverified workaround.

REPENTOGON has menu accessors in source, but its selection setter only assigns
SelectedSave: loading, slot-index mapping and identity attestation remain unknown.
Its launcher runs J273 instead of J460, uses Lua 5.4, has automatic save syncing
and shares game-state paths. It is a candidate requiring a separately approved,
isolated trial, not an adopted dependency or promised solution.

## Acceptance

Three cold starts from an approved disposable profile reach a verified resumed
file-2 room with no human input, screen capture or desktop input injection.
Actual run frames follow the existing run; wrong/unknown slot or missing Continue
fails before gameplay. No new run is created as fallback. Logs distinguish each
startup phase and faults. Existing-instance and timeout paths preserve the run.
Write-set/backup checks prove approved isolation before any migration or runtime
probe. Offline checks and strict validation pass; archive only after real evidence.

## Source pins for deferred research

Local read-only source inspection used REPENTOGON commit
8c00feff4536d66ac72fb818eb8e52b0fd3d19c1 and its Launcher commit
ad7ce0cca5ef5e94b9f1bca5df7ad8f10e5c3455. See
[official installation documentation](https://repentogon.com/install.html),
[REPENTOGON source](https://github.com/TeamREPENTOGON/REPENTOGON), and
[Launcher source](https://github.com/TeamREPENTOGON/Launcher).
No launcher/runtime binary was downloaded, installed or executed for this research.
