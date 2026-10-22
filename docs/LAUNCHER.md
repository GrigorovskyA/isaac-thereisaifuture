# Terminal observation launcher

## Explicit New Run after death

```powershell
./Start-IsaacAgent.cmd --entry-mode new-run
# Optional local preflight only:
./Start-IsaacAgent.cmd --entry-mode new-run --preflight-only
```

This mode is explicit:default remains Continue. New Run requires fresh selected
file2 evidence that its game state is missing;an available or unverified Continue
is protected. It confirms the remembered character and only reports readiness
after native `[New, 2]` plus an active bridge snapshot identifies Isaac(type0).
A different character fails without gameplay or retry. No claim of arbitrary
pre-start character selection. Eight-key/60s menu/2MiB log limits,foreground and
ownership checks remain in force;no screenshots. No model/normalizer/checkpoint
or approval is created/reset and no learning starts. The launcher leaves the game
open after return. For a redirected Documents folder,use --game-log as below.

The Python observer accepts --entry-mode manual|continue|new-run;legacy
--continue-file2 remains supported but cannot be combined with --entry-mode.
The PS wrapper accepts -EntryMode new-run. Native acceptance is recorded in
reports/2026-10-20-post-death-new-run.md;earlier Continue-only limits below describe
the previous increment and still apply to Continue mode.

## Local menu-only Continue (current)

`Start-IsaacAgent.cmd` now requests local menu automation as well as observation.
It launches through Steam,uses only Enter/Escape/Left/Right in the owned game
window,and checks a fresh native log before Continue. No screenshots or agent
desktop tools are used. Do not use game menus during startup. Focus refusal,
unexpected log/menu state,more than eight keys,60 seconds menu time or a log over
2MiB stops the command. It always releases held keys and closes its listener.

Successful automatic readiness requires both fresh `[Continue, 2]` evidence and
one validated bridge snapshot. Initial startup scans of all three slots are not
selection evidence. An existing file2 run must be available; there is no automatic
New Run fallback. No gameplay keys or training are sent. On return Isaac remains
open; a separate gated controller can subsequently attach. Native acceptance is
recorded in reports/2026-10-20-local-menu-entry.md.

```powershell
./Start-IsaacAgent.cmd --preflight-only
./Start-IsaacAgent.cmd
# Redirected Documents folder or another native log location:
./Start-IsaacAgent.cmd --game-log '<Documents>/My Games/Binding of Isaac Repentance+/log.txt'
# Manual menu preparation, using the underlying observer:
./.venv/Scripts/python.exe -m isaac_threrisaifuture.launcher --samples 1 --reconnects 0
```

The remaining sections describe the earlier observation-only increment unless
explicitly stated. Their no-key/manual-selection statements apply to the Python
observer without `--continue-file2`,not the updated agent entry points.

## Agent command without desktop interaction

The CMD entry point calls project Python directly and does not require PowerShell
script execution to be enabled:

```powershell
./Start-IsaacAgent.cmd --preflight-only
./Start-IsaacAgent.cmd
```

An equivalent wrapper is available in a PowerShell host that permits local scripts:

```powershell
./scripts/Start-IsaacAgent.ps1 -PreflightOnly
./scripts/Start-IsaacAgent.ps1 -TimeoutSeconds 180
```

The second command requests Steam startup, waits for one validated bridge snapshot
and exits without a pause. It uses no screenshots or desktop input. JSON events
distinguish `launch_requested`, `waiting_for_run`, `handshake`, `bridge_ready` and
`completed`; only a validated snapshot proves bridge readiness. No gameplay or
training starts. File 2 / Continue remains manual: there is no verified direct
entry API in the installed bridge. `save_slot_verified=false` is explicit.
The timeout is configurable from 5 to 600 seconds; reconnects are disabled.
Exit 0 means observation completed, 2 means failure, 130 means interrupted.
On timeout, the listener closes and the game stays open for normal manual exit.
The script accepts optional `-GameDirectory` and works from any working directory.

## Longer observation

Double-click `Start-Isaac.cmd` at the repository root. It calls project Python
directly and keeps the terminal open after exit so errors remain visible. Steam,
Isaac and the explicitly approved observer must already be installed. It neither
installs mods nor changes PowerShell execution policy. It does not use screenshots,
mouse/keyboard injection or a development agent to launch or observe the game.

Normally exit a running game first to preserve its current run. Preflight refuses
any existing isaac-ng process; it never kills a game to make room for another.
It discovers Steam from the current user's registry and libraryfolders.vdf,
without reading Steam account data. If discovery is ambiguous, specify the actual
game directory; no personal absolute path is committed.

```powershell
.\.venv\Scripts\python.exe -m isaac_threrisaifuture.launcher --preflight-only
.\.venv\Scripts\python.exe -m isaac_threrisaifuture.launcher --samples 3000 --duration 900
# Optional explicit installation:
.\.venv\Scripts\python.exe -m isaac_threrisaifuture.launcher --game-directory '<library>\steamapps\common\The Binding of Isaac Rebirth'
```

Both installed observer artifact hashes must match the project files. Mismatch or
absence fails without overwriting anything. Review OBSERVATION_PROTOCOL before
any deployment. The listener binds 127.0.0.1:9528 before game launch; a port conflict
fails before launch. Startup uses `steam://rungameid/250900`; existing Steam
options must already include `--luadebug` for the installed LuaSocket observer.
Persistent Steam options and Cloud are not changed. Starting
the game can naturally write game saves/configuration; this launcher does not
establish profile isolation or achievement eligibility.

## Logs and limits

Terminal events record configuration and distinguish `listening`, `launch_requested`, actual `handshake`,
once-per-five-samples progress, completion and faults. Complete validated snapshots
are written to `runs/observe-<timestamp>-<id>/observer.jsonl`, ignored by Git. Do not
upload raw logs or personal data as evidence. The game process being created is
not reported as successful integration.

Default budgets: 180 seconds for a peer connection, 3 seconds per handshake/read,
3000 snapshots (about ten minutes at 5 Hz), and 900 seconds total observation time
after preflight. `--connection-timeout`, `--samples` and `--duration` configure
positive bounded values. Slow launch or callbacks unavailable in menus may time
out. Up to three reconnections are allowed by default, configurable with
`--reconnects 0..10`. A run ending may close the Lua socket; the launcher then
waits for a fresh handshake/session within the original duration/sample budget.
It does not start or reset a run itself. An observer disconnect remains an
unknown gameplay outcome; incompatible or malformed protocol data fails
immediately without retry. Ctrl+C exits with code 130; validation or
infrastructure faults exit with code 2. Client sockets and log handles close on
all paths. Isaac stays open for normal user exit. Steam URI dispatch provides no
owned game PID and does not prove the eventual executable path or save identity.

## Remaining manual step

Select **file 2** and continue the desired existing run yourself. Automatic slot
selection, slot identity verification and run start are **not implemented or
verified**. This limitation must be resolved before autonomous progression.
Historical direct-executable tests requested manual Steam confirmation of
--luadebug. They do not validate the new Steam-URI agent entry point.

No gameplay control or training is started by this launcher. Real closed-game
launch and handshake were observed, with user-selected file 2. The first live
version exited when the user died/restarted and Lua closed the socket; bounded
reconnection was then added and tested offline. The production launcher observation
loop also passed a real Lua test with deliberate Python-side peer closure: a fresh
handshake resumed observation and the sample budget completed. This is a controlled
transport-fault test, not another forced death or a full campaign test. See the
terminal-launcher evidence report. The separate 3000-snapshot observe CLI probe
also recovered one real message timeout; its cause remains unknown.

## Separate lifecycle and training modes

The user now prioritizes unattended startup; the remaining menu API is unresolved.
For the separate opt-in lifecycle mode, use Start-Death-Restart.cmd after manually
launching/continuing file 2, not Start-Isaac.cmd. The latter remains observation
only. The attach script never launches or kills Isaac. See DEATH_RESTART.md for
bounded behavior, acceptance status and closed-game deployment requirements.
