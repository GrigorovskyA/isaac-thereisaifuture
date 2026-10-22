# Restart after game over

Implementation 0.2.0 passed bounded real-game acceptance on J460 (2026-10-17):
one natural game-over restart on operator-selected file 2, character type 0.
See [evidence](../reports/2026-10-17-restart-after-game-over.md). Initial game launch and save-file selection remain manual, as requested. This starts a new run inside Isaac; it never relaunches the executable.

## Use

After the reviewed 0.2.0 adapter is deployed with the game closed, launch Isaac manually with temporary `--luadebug`, select **file 2**, and continue a normal solo run. Only then run `Start-Death-Restart.cmd` and confirm the selected file in its terminal. Alternatively, from the repository root:

```powershell
.\.venv\Scripts\python.exe -m isaac_threrisaifuture.cli observe --restart-after-death --confirmed-save-slot 2 --samples 3000 --accept-timeout 180 --reconnects 10
```

This is operator confirmation, not slot detection or full isolation. The mode can change the game's run/progress through ordinary gameplay. It is the user's narrow authorization for after-death restart, not general reset, player control, training or achievement eligibility. Do not select another file with this mode active. A normal run exit disables restart for this game instance; restart Isaac and explicitly confirm the desired file before a new test session.

Default `observe` and `Start-Isaac.cmd` remain read-only. Ctrl+C stops the consumer and disconnect cancels pending restarts. Up to ten finite transport reconnects await a new session; transport failure never counts as death. The script does not launch Isaac or select menus.

## Behavior and limits

The optional hello capability `death_restart_v1` arms only after its full acknowledgement is sent. A future `MC_POST_GAME_END(true)` schedules the fixed command `restart` after 1500 ms. It requires the same session/epoch and one still-dead player. Victory, revival, exit, run change, disconnect, expired lease or a pending event older than five seconds cancels. Zero health alone does nothing. Attaching on an existing death screen does nothing.

Limits: **three attempts within ten minutes per mod load**. Reconnection never replenishes either limit. A fresh non-continued game-start must confirm the transition within five seconds; uncertainty or command failure disables further attempts, with no retry. Restart uses the current character according to the API reference; special character, challenge, daily, co-op and revival cases are not runtime accepted.

Native diagnostics prefixed `[Isaac Future Observer] Death restart` record arming, session/epoch scheduling, dispatch, confirmation, cancellation and faults. The CLI emits handshakes and snapshots; correlate a fresh connection and larger `game_epoch`, rather than inferring success from a command return. Raw logs stay in ignored local storage.

## Acceptance and rollback

Never deliberately kill or reset a living user run to test this feature. Deploy only after normal game exit, backing up the two existing mod artifacts and checking new hashes. Use a natural death in the authorized file-2 session, record the game log plus snapshot epochs, and obtain user correlation that a new run began with the expected character and manual control remains responsive. Test default observation and disconnect without forcing death. Full revival/ending behavior remains unknown until separately observed.

On faults stop the consumer. While Isaac is closed, restore only the prior observer artifacts if rollback is needed. Do not restore saves, edit Steam settings or install REPENTOGON. The declared bounded real-game acceptance passed; do not generalize that evidence to all characters or game modes.

## Primary API references

Checked 2026-10-17: [callbacks](https://wofsauge.github.io/IsaacDocs/rep/enums/ModCallbacks.html), [restart command](https://wofsauge.github.io/IsaacDocs/rep/tutorials/DebugConsole.html), [ExecuteCommand](https://wofsauge.github.io/IsaacDocs/rep/Isaac.html). These document intended behavior; simulated tests do not establish J460 compatibility.

## Reviewed artifact hashes

Windows working-tree SHA-256 (0.2.0); recompute from actual files before deployment:

| Artifact | SHA-256 |
|---|---|
| mod/observer/main.lua | C53EFB0E735C191AC1B72D7AD9C93CF8E03808C858D719E3B7F88CFE98245B09 |
| mod/observer/metadata.xml | 25C4980FD19565489BA4F92B91008BAFC89D4DDFE3B05F104CC5EE1AAEFAA59D |

Git normalizes line endings; use a fresh local hash rather than assuming these Windows byte hashes apply to every checkout.
