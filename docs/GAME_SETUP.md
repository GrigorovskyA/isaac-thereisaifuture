# Connecting the real game

The [completed compatibility audit](../archive/docs/COMPATIBILITY_AUDIT.md) records the actual
2026-10-17 inventory, source comparison, isolation risks and exact next task.
Repentance+ was installed following the user's separate request during the audit.
Project tooling does not install game mods. Read-only bridge acceptance is now
recorded in the archived item-02 evidence; action/training isolation is unverified.
The checklist below governs future refreshes.

The [observer deployment/rollback plan](OBSERVATION_PROTOCOL.md) now contains
concrete project artifacts/hashes and client commands. Implementation and offline
tests are complete; the observer was subsequently deployed for the user-authorized
ordinary-profile read-only exception, with a partial real handshake/snapshot probe.
This does not establish training isolation. See STATUS and the runtime evidence.

Use [the terminal launcher](LAUNCHER.md) for future process launches and logs.
The requested target is file 2; selecting and verifying it automatically remains
unimplemented. The script does not use monitor capture or desktop input injection.

After the user's cleanup request, seven legacy mods were disabled with reversible
disable.it markers while the game was closed, preserving four existing disabled
mods and keeping only observer enabled. Previous marker state is backed up locally.
No Workshop subscriptions or saves were edited. A subsequent user-confirmed
file-2 continuation, fresh log showing only observer mod Lua, and 50 real paused
snapshots verified short loading/observation for this configuration. The accepted
long soak used the prior mixed profile; a ten-minute active observer-only soak is
not claimed. Changing mod sets can affect Continue availability: preserve the run,
and do not replace saves or force a restart to resolve a modding-state mismatch.

## Read-only inventory first

Find the actual Steam library and game manifest. Record path, branch/build ID,
DLC, in-game version, and Repentance+ installation. Determine whether REPENTOGON
is present and its version. List active mods and potential conflicts. A folder
name alone is not proof of support.

Record whether the game is closed, at a menu, or in a live run. Do not reset an
active user run. Establish actual local-save and Cloud behavior. Confirm profile
and mod paths on this computer.

## Compatibility matrix

| Field | Record | Evidence |
|---|---|---|
| Game | Repentance+ version/build/branch | Steam manifest and in-game version |
| Mod runtime | REPENTOGON version/capabilities or absent | Installed files/game log |
| Lua API | Required callback/input/state/reset APIs | Documentation and minimal probe |
| Candidate bridge | URL, commit, license, supported game | Source, tests, actual run |
| Transport | Socket/file/other, framing, blocking | Code and observed communication |
| Training profile | Path, isolation, restoration procedure | Verified configuration |
| Saves/Cloud | Write locations and main-profile isolation | Configuration inspection |
| Verdict | supported/unsupported/unknown per capability | Specific evidence reference |

Required capabilities: player/entity reads, input application and release, frame
counter, episode-ending detection, and controlled reset. Optional capabilities:
custom scenarios, speed control, and multiple instances. Missing optional features
need not block the first MVP.

## Choosing a bridge

SocketBridge is the first candidate from the discussion, not an adopted dependency.
Compare its current implementation with a small custom adapter: Repentance+
support, licensing, blocking operations, bounded messages, recording/replay, and
maintenance. External reuse must not introduce unverified executables or DLLs.

Record the choice in the active change's design. Do not copy an implementation
without a compatible license. Investigate public behavior and choose a permitted
approach instead. Do not dump every related repository into the source tree.

## Before installing or activating a mod

Prepare specific actions: artifact source/version/hash, exact destination, affected
settings, and disable/rollback procedure. Obtain authorization for those actions.
Do not reinstall an existing game just to add a bridge. Do not delete or replace
user saves with training data.

A separate save slot alone does not prove isolation of global settings or Cloud.
Verify the available profile mechanism, backup, and restoration procedure. Keep
backups outside Git and do not upload them.

## First real-game smoke

1. Use an approved training profile, safe room, and clear stop mechanism.
2. Establish a handshake with actual game/mod versions and advancing frame IDs.
3. Verify read-only state: actual player movement changes received coordinates.
4. Apply a short movement/shooting action and observe its effect.
5. Verify neutral/stop, Python shutdown, and connection loss all release actions.
6. Record results, exceptions, and fresh logs. Partial success is not the whole
   milestone. Test reset only after isolation is confirmed.

Measure rendering FPS, game updates, and RL decisions/sec separately. Speed control
and multiple Repentance+ instances remain unverified. Write the audit and evidence
in English.

## Background operation (user-requested, 2026-10-17)

With Isaac closed, the active Repentance+ options.ini was backed up locally and
only `PauseOnFocusLost=1` changed to `PauseOnFocusLost=0`. Readback and comparison
confirmed every other key/value was preserved. This is a shared game option,
not a per-save-file setting. No save or Steam Cloud setting was edited.

The [native Options reference](https://wofsauge.github.io/IsaacDocs/rep/Options.html#pauseonfocuslost)
exposes the same boolean. Background operation was then verified in a real J460 session: the user
confirmed leaving the game unfocused for 15 seconds, and timestamped observer
samples spanning 18:25:49–18:26:18 CEST advanced from frame 30352 to 31248 with
status active throughout. No adjacent equal frame counters occurred in that
150-sample interval. This verifies the observed window, not every display mode
or future configuration. Manual pause remains available. To roll back, close Isaac normally
and change only this key to 1; do not restore an entire options backup over newer
unrelated settings.

## Item 03 action gate (2026-10-17)

Safe actions are implemented offline in adapter 0.3.0. After user-confirmed normal
exit and installation approval, its two files were deployed with the action gate
nil; backups/hashes/preflight passed. Actual loading is still unverified. No
current run, save, Cloud option or Steam configuration was changed. The active-slot and isolation prerequisites remain blocked;
see SAFE_ACTIONS.md for the exact evidence/authorization plan. Do not repurpose
the accepted ordinary-profile read-only or natural-death restart exception for
movement/shooting. Keep initial launch and file selection manual.

## User-approved ordinary-profile action exception

The user subsequently explicitly approved bounded movement/shooting tests directly
on the ordinary profile and asked to retain that permission for future checks.
This supersedes the earlier isolation-only requirement for these tests, not
training. Adapter 0.3.1 is installed; current manual slot/room confirmation and
live evidence remain pending. Do not ask for ordinary-profile action permission
again. SAFE_ACTIONS.md describes the private expiring approval, current-instance
checks and 120-second bound. Do not change saves/Cloud or force a reset.
