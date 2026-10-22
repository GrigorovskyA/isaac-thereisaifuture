# Passive oracle callback probe

Observer 0.4.5-dev is installed with source-matching hashes after closed-game
deployment; later-frame raw sampling has bounded manual-combat evidence. Diagnostics are
inactive unless Python explicitly requests oracle_probe_v1. There is no
oracle_probe source flag, patched diagnostic bundle or per-test file replacement.
The 0.4.2-dev reports describe the historical procedure only.

## One-time update and operator-directed launch

Update reviewed main.lua/metadata.xml once while Isaac is closed, with a private
backup and hash comparison. Normal launcher preflight must pass unchanged. Saves,
Cloud, other mods, action approval and reset limits are outside this update.
Further mode changes require no file edits. Future software upgrades still need
normal closed-game deployment; do not replace a loaded mod.

Launch is operator-directed: the user may launch or request one agent launch
after preflight. Save-file selection/Continue and normal exit remain manual;
there is no unattended startup or recovery. For a diagnostic session, launch
from PowerShell in the game directory:

```powershell
Set-Location 'C:\Program Files (x86)\Steam\steamapps\common\The Binding of Isaac Rebirth'
.\isaac-ng.exe --luadebug
```

Select file 2 and Continue the existing run. Do not discard a run, reset or force
a scenario. Wait until ready for manual combat before starting the diagnostic
client. Ordinary observation does not consume the diagnostic window. If another
observer is listening on port 9528, close that client first; the game stays open.

From D:/isaac, start one bounded read-only diagnostic attach:

```powershell
.\.venv\Scripts\python.exe -m isaac_threrisaifuture.cli observe --oracle-probe --samples 600 --accept-timeout 60
```

This requests the capability through the existing hello, not a gameplay command.
No action/restart/native-step mode may be combined. Diagnostic facts stay in the
separate game log; stdout contains normal validated snapshots, not outcome events.
The client closes after 600 samples or 120 seconds from attach; one in-progress
receive may take at most three more seconds. Reconnects are forbidden in this CLI
mode. Accept/handshake/message timeout maxima are 60/3/3 seconds.

## Budgets and facts

The Lua window is nonrenewable per mod load: at most 120 seconds, 1024 log attempts
including a final count stop, 400 bytes per line and 128 local entity labels.
Disconnect, exit, unload or read/logger failure ends it. Old, unsupported or
exhausted peers reject the explicit request; there is no silent fallback.
Normal read-only observation remains available. Closing/reopening Python does
not renew the window; a later diagnostic run requires a normal manual game
restart. Do not automate restart or increase limits to cover more scenarios.

Play normally during recording. No input is supplied by this tool; intentional
death or debug damage/spawn commands are unnecessary. Missing death/revival/floor
scenarios remain not_run. Extract only current-session [Isaac Future OracleProbe]
lines into ignored private evidence; do not commit raw game logs or saves.

Labels are diagnostic, not verified spawn generations. Pointer hashes/seeds are
not logged. Damage amounts are attempts; npc_update_hp is a later raw callback
sample and can still show old HP before application. Neither is a realized damage
or reward event. Removal is not a kill, clear/death readings are candidates, and
concurrent healing/damage cannot be attributed from net health changes.

See reports/2026-10-18-oracle-combat-runtime.md for the measured counterexample.
The post_update_hp record adds a sample at this observer's post-update callback.
At most 16 pending targets are retained; repeats coalesce and removed targets
release their reference immediately. queued_frame/queued_update and attempts/init
describe the staging context. status is sampled (raw HP may be negative), removed,
missing or identity_changed; unavailable statuses carry no fabricated HP. The
seventeenth pending target stops the probe with reason=pending. Transitions,
faults, reentrancy and disconnect clear references. NPC-update and post-update
readings remain independent; neither is an engine-wide synchronization barrier.
The 0.4.4-dev live run confirmed a first post-update sample in the same frame as
the damage attempt still showing old HP before a later kill record changed HP.
See [runtime counterexample](../reports/2026-10-18-post-update-hp-runtime.md).

Observer 0.4.5-dev (deployed, bounded later-frame sampling verified in Isaac) keeps staged entries across up to
four observer post-update callbacks for later-frame sampling. Each entry takes at
most three raw samples: the first at its first callback (it may share the attempt
frame, `post_update_hp` unchanged) and up to two more in strictly later game frames
than the previous sample (`post_update_hp_later`). Fields: label, queued_frame,
queued_update, attempts, init, sample (2 or 3), prior_frame, then status=sampled
with raw HP or status=removed/missing/identity_changed with none. Callbacks in an
unchanged frame perform no later HP read but still count toward the four-callback lifetime. An
unfinished entry then logs `post_update_hp_expired` (samples, callbacks=4) if the
budget permits and releases its reference. Opportunity precedes expiry; the third
sample or any unavailable status finishes an entry without expiry. At most 16
entries exist across both stages and the seventeenth stops with reason=pending.
Budgets (120000 ms, 1024 records, 128 labels, 400 bytes) are shared and
nonrenewable. Values are timing facts, not applied damage, settlement or a barrier.
The live 0.4.5-dev check recorded 99 first and 197 later records, including 16
removed facts without HP; 87 of 99 windows had a changed numeric later value.
The 1024-record budget stopped diagnostics after 57.825 seconds while ordinary
observation continued to 120 seconds. Expiry/missing/identity changes and death/
revival were not observed. See [runtime evidence](../reports/2026-10-18-later-frame-hp-runtime.md).
This probe enables no completion receipt, event emitter, real GameBackend or
training. It cannot satisfy the 100-real-episode requirement by itself.

## Stop and cleanup

Ctrl+C or normal client exit closes the socket and ends an active diagnostic
window. No file restoration is needed: the same installed/source hashes remain
valid. After the user closes the game normally, optional launcher --preflight-only
verification launches nothing. Keep private logs/backups excluded from Git.
Record actual context, callback coverage, faults/truncation and observed stop.
