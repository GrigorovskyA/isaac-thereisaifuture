# Game compatibility audit

Audit date: **2026-10-17, Europe/Amsterdam (CEST, UTC+02:00)**.
Change: `audit-game-compatibility`. Evidence: [audit report](../reports/2026-10-17-audit-game-compatibility.md).

**Verdict:** the installed target is now **Steam Repentance+ v1.9.7.17.J460,
build 22878971**. No bridge is verified on it. Implement a minimal original,
observation-only Lua/Python adapter using bundled LuaSocket, subject to a permitted
module-load probe and verified training isolation. Do not install REPENTOGON or
reuse SocketBridge unchanged for this first slice.

## Evidence levels and boundaries

- **L:** local file/configuration or process inspection; establishes installed
  artifacts/configuration, not API behavior.
- **S:** primary source/documentation inspection; establishes code paths or intended
  APIs, not successful execution on this machine.
- **R:** controlled real-game probe on an authorized isolated profile. None performed.
- **Unknown:** runtime behavior not probed; no mock/README can promote it to verified.

The audit initially found Repentance. The user then explicitly requested installing
Repentance+. Steam completed the update and an already queued launch started the
game. The assistant navigated Steam and attempted to cancel that queued launch;
it did not initiate a game launch or game test. Computer Use was stopped by the
user; subsequent inspection used read-only filesystem/process access.
The new runtime created options, backups and Cloud-cache files. Therefore this is
not a claim that the machine stayed byte-for-byte unchanged during the audit.
No audit code installed/activated mods, edited saves/options/Cloud, applied input,
reset a run, or started training. The current game is not an approved test instance.

## Local evidence register

Paths deliberately omit Windows/Steam account identities. These aliases describe
the actual discovered locations, not arbitrary default-path assumptions:

| ID | Actual location, sanitized | Observed evidence |
|---|---|---|
| L1 | `<Steam> = C:/Program Files (x86)/Steam`; `steamapps/libraryfolders.vdf` | Registry SteamPath and VDF agree; one registered library, on C:. No other library is registered, including D:. |
| L2 | `<Steam>/steamapps/appmanifest_250900.acf` | Initially build 10102354, target 17360122; finally build 22878971, target 0, StateFlags 4, UpdateResult 0, downloaded/staged bytes equal totals. No BetaKey recorded: no explicit beta selection evidenced; exact named branch remains unknown without Steam properties verification. |
| L3 | `<Game> = <Steam>/steamapps/common/The Binding of Isaac Rebirth` | Current isaac-ng.exe SHA-256 `3BDFC8BAE0DC7E334B76009D0AD45DFBB16EE5F00C06FFBC3A0094E34D44616B`; current process title v1.9.7.17. |
| L4 | `<Documents>/My Games/Binding of Isaac Repentance/log.txt` | Historical log last modified 2024-11-19: v1.7.9b.J835. Its version is historical, not the final installed edition. Old changelog still starts v1.7.9b after update, so changelog alone is unreliable. |
| L5 | `<Documents>/My Games/Binding of Isaac Repentance+/log.txt` | Fresh startup reports v1.9.7.17.J460; command line has no --luadebug. No controlled bridge probe appears. Active log may still be buffered/changing. |
| L6 | `<Game>/savedatapath.txt` | Reports Repentance+ Documents save-data directory and shared `<Game>/mods`; explicitly informational, editing it does not redirect saves. Earlier file reported Repentance directory. |
| L7 | Both edition directories' `options.ini` | SteamCloud=1, EnableMods=1, EnableDebugConsole=1, PauseOnFocusLost=1, SaveCommandHistory=1. Debug console and --luadebug are distinct. |
| L8 | `<Steam>/userdata/<account>/250900/remote` and `remotecache.vdf` | Repentance persistent data for slots 1–3 and rerun state; after launch Repentance+ persistent data for slots 1–3 and a game-state file appear. Older edition saves also present. Content not opened or copied. |
| L9 | `<Game>/mods`, `<Game>/data`, workshop manifest for 250900 | Eleven mod directories; disabled markers and fresh script-load entries listed below. Shared mod-data root exists. |
| L10 | `<Game>/resources/scripts`, `tools/LuaDocs`, root file inventory | json.lua, socket.lua, socket/core.dll (46080 bytes), Lua 5.3 DLLs and baseline API docs/enums present. No REPENTOGON installation/launcher directory or startup version evidence found in game root; installed REPENTOGON version: **not detected**. This does not exclude a standalone launcher elsewhere. |

### Installed edition and DLC matrix

| Component | Local installed evidence | Compatibility status |
|---|---|---|
| Rebirth app 250900 | L2/L3 | Installed base app; Steam title remains Rebirth for all DLC |
| Afterbirth 401920 | Depot 250905 in L2 | Installed |
| Afterbirth+ 570660 | Depot 250908 in L2 | Installed |
| Repentance 1426300 | Depot 250911 in L2 | Installed |
| Repentance+ 3353470 | Depot 3353471, manifest 229910742625134068 in final L2; L5 | Installed and version identified; bridge compatibility **unknown** |
| REPENTOGON | L10; no runtime version | Not detected in current game; no version to claim |
| SocketBridge/custom bridge | No candidate/project bridge in mod inventory | Not installed or tested |

The [official DLC page](https://store.steampowered.com/app/3353470/The_Binding_of_Isaac_Repentance/)
identifies Repentance+ and its other DLC prerequisites. Ownership was visible in
Steam, but installed depots and the fresh game version establish the final inventory.

### Existing mods and potential conflicts

| Workshop directory/name | disable.it present | Fresh Repentance+ Lua script-load evidence |
|---|---|---|
| Animated Beggars 2623638283 | Yes | No |
| Boss Rush Wave Counter 2492654252 | No | Yes |
| Detailed Respawn 2729252633 | No | Yes |
| Edu's Better Lucky Pennies 2719343606 | No | No |
| Enhanced Boss Bars 2635267643 | No | Yes |
| External Item Descriptions 836319872 | No | Yes |
| Planetarium Chance 2489006943 | No | Yes |
| Rare Chests 2782715504 | Yes | No |
| Regret Pedestals 2766379837 | Yes | No |
| Specialist for Good Items 2575911103 | Yes | No |
| TimeMachine 2617557401 | No | Yes |

Content-load listing includes all folders, including disabled ones; it is not proof
of Lua activation. These mods can affect UI, timing, pickup/entity state, death/
respawn behavior and observations. Their mutual runtime compatibility is unknown.
Do not disable ordinary mods as part of this audit.

## Saves, Steam Cloud and isolation

L6–L8 identify two distinct roots: Documents holds edition options/logs/backups;
Steam userdata/250900/remote holds the observed Cloud-cache progress/run files.
Repentance Documents contains dated backups for all three slots; Repentance+
created `save_backups`. No backup completeness or restoration was tested.
No private save bytes, raw logs, Steam IDs, or full configuration are included here.

The Steam client previously recorded `last_sync_state=synchronized`, and the UI
displayed synchronized Cloud saves. This is local/historical metadata, not an
independent verification of server contents. [Valve documents](https://partner.steamgames.com/doc/features/cloud)
Cloud synchronization around sessions and separate global/per-game switches.
Game `SteamCloud=1` alone does not prove the present effective client toggle or
server freshness. Cloud behavior must be rechecked before a test launch.

| Isolation option | Benefit | Remaining risk / required evidence |
|---|---|---|
| Another save slot | Different slot-specific progress | **Insufficient**: same options, mods/data, Steam account/Cloud and achievements; no full isolation |
| Disable Cloud and use local saves | Can remove Cloud-cache writes after verification | Settings change requires authorization; local edition directory, automatic imports, Steam achievements and shared mod data still matter |
| Dedicated Windows training user with approved Steam identity/Cloud policy | Separates Documents/configuration | Same Steam identity can restore the same Cloud progress; game install/mods/data remain shared; verify write set |
| Fully separate authorized training account/profile plus isolated mod data and backups | Stronger separation of progress and settings | Game entitlement and exact paths need checking; no unsupported command-line save redirection assumed |
| REPENTOGON-managed installation | Separate runtime and persistent-save filenames | **Not isolation**: automatic vanilla synchronization and shared game state; source details below |

Preferred next preparation: a dedicated training OS/profile context with an
explicit Steam/Cloud policy and an independently verified write set; do not call
any option verified yet. No supported arbitrary `--savedir`/profile flag was
established. Copying the executable or editing savedatapath.txt does not establish it.

Before later testing, close the game normally under user control; inventory and
back up all edition save directories, Steam remote/cache metadata, options, mods
and mod data outside Git. Record private hashes and test restoration on disposable
copies. Set up only the specifically authorized profile/Cloud changes, then
compare write locations and main-profile hashes across launch/exit. Resolve any
Cloud conflict with the user; never restore files under an active game or blindly
overwrite Cloud data. All of this remains **blocked for execution** in this audit.

## Candidate source audit

Fetched/read on 2026-10-17; no downloaded code or DLL was executed. The source
checkouts are scratch data outside the target repository and are not dependencies.
Commit links pin every comparison; README version statements are only claims.

| Candidate, pinned commit/date | License | Claimed target / source findings | Transport, blocking, runtime dependencies | Decision |
|---|---|---|---|---|
| [SocketBridge](https://github.com/EmptyEmeraldTablet/SocketBridge/tree/89dab7852c987a4ef4f62f168c309fe27a91a598), 2026-04-28 | MIT, LICENCE; retain notice if reused | README says Repentance/Repentance+; main.lua v3 uses extender callbacks absent from local baseline enums. Exact J460 support **unknown** | Lua TCP client -> Python 127.0.0.1:9527, JSON lines, socket.core + json, README requires --luadebug. Lua 10 ms block timeout in update callback; Python asyncio server, pydantic>=2 and typing-extensions>=4. No REPENTOGON version pinned. | Reject unchanged; adaptation possible but substantial |
| [The-RL-of-Isaac](https://github.com/Seladus/The-RL-of-Isaac/tree/649041f90b8e6d01eef89144b3c8c9bdf1a1d26a), 2022-08-24 | MIT, LICENSE; third-party bundled binaries need separate provenance | Repentance proof of concept predates Repentance+; no J460 evidence | Game TCP server 127.0.0.1:6942; blocking accept and receive in update callback; newline requests/raw JSON replies, Python single recv assumptions. Bundled socket/core.dll, Gym, NumPy, OpenCV, pywin32 keyboard/capture, torch code, speedhack/injector components. | Reject for first integration |
| [Aiisaac](https://github.com/papaspamvicky-dev/Aiisaac/tree/c4a43e8c3381551375eafbd0c216beeaa3c64726), 2026-02-11 | No repository license found; no permission to copy assumed | README claims Rebirth/Repentance; no Repentance+ proof. Lua calls ModReference:OpenFile, not established in installed API | state/action JSON files; synchronous file read/write from callbacks, no bounded disk latency. Python agent primarily standard library. Action age is displayed, not enforced; old action file can remain live. Windows writer unlinks before rename with non-atomic fallback. | Reject reuse; file transport adds races/stale-state concerns |
| [isaac-rl-agent](https://github.com/Monster7704/isaac-rl-agent/tree/d332388d2cbd1bdc6f5cb56e1fe934ecdad5ebac), 2025-06-11 | LICENSE.txt contains MIT heading/copyright only; grant text incomplete | README claims Repentance + REPENTOGON/PPO; tree has only README, requirements and incomplete license | No Lua bridge or environment implementation to inspect; blocking and runtime capability **unknown**. Requirements name RL packages, not a proven transport. | Not a usable bridge |

### SocketBridge code findings

At the pinned [main.lua](https://github.com/EmptyEmeraldTablet/SocketBridge/blob/89dab7852c987a4ef4f62f168c309fe27a91a598/main.lua):

- Lines 103–175: `connect` sets 0.01 seconds and checks pcall success plus socket
  object, losing the actual connect return status; a refused connection need not
  throw. `send` ignores nil/error/partial results; `receive("*l")` discards partial
  input. Under fragmentation/backpressure this can lose framing/data.
- Lines 146–152 and 1137–1189: disconnect closes socket but does not reset held
  actions; AUTO can retain an action in combat, FORCE_AI continues input. No
  heartbeat/deadline/session/episode validation was found in the active Lua file.
- Lines 1371–1382 expose `EXEC_CONSOLE` -> arbitrary `Isaac.ExecuteCommand`.
  This conflicts with the project protocol boundary; reset must be a narrow
  authorized operation in a later change.
- Lines 1387 onward perform collection/send/receive in update; local update/render
  counters are not a verified engine-step contract. No claimed TPS is accepted
  without measurement.
- Lines 1639 and 1674 unconditionally register `MC_POST_PLAYER_DEATH` and
  `MC_POST_ADD_COLLECTIBLE`, absent in installed baseline enums. The latter is
  documented by REPENTOGON; source registration does not prove this mod loads.

Python [connection/server.py](https://github.com/EmptyEmeraldTablet/SocketBridge/blob/89dab7852c987a4ef4f62f168c309fe27a91a598/python/connection/server.py)
has asynchronous line reads with 5-second retrying timeouts. This does not repair
Lua callback stalls or implement an input watchdog. [LuaSocket's own TCP reference](https://lunarmodules.github.io/luasocket/tcp.html)
specifies default blocking I/O and nil/error/partial returns. Current upstream
features must not be assumed present in the game's older bundled DLL.

### REPENTOGON runtime and save implications

Read [REPENTOGON commit 8c00feff4536d66ac72fb818eb8e52b0fd3d19c1](https://github.com/TeamREPENTOGON/REPENTOGON/tree/8c00feff4536d66ac72fb818eb8e52b0fd3d19c1)
(2026-10-16), [Launcher commit ad7ce0cca5ef5e94b9f1bca5df7ad8f10e5c3455](https://github.com/TeamREPENTOGON/Launcher/tree/ad7ce0cca5ef5e94b9f1bca5df7ad8f10e5c3455)
(2026-10-12); both repository licenses are GPL v2 text. Using the runtime is
different from copying its implementation; no runtime source was incorporated.

The [current installation guide](https://repentogon.com/install.html) accepts current
official Steam Repentance+ as an installation source but runs **v1.9.7.12.J273**,
not the installed vanilla J460. It uses a launcher-managed installation; the
[Lua changes](https://repentogon.com/changes/General.html) include Lua 5.4.
An existing Lua 5.3 binary/module cannot be assumed ABI-compatible.

Critically, pinned `repentogon/SaveSyncing/SaveSyncing.cpp` lines 52–72 define
separate `rgon_steam_persistentgamedataN.dat` Cloud names and local
`Repentogon/rgon_persistentgamedataN.dat`, but **share** the Repentance+
game-state path. Lines 610–644 synchronize vanilla saves on startup/shutdown
when enabled. The runtime also has options/mod-enabled synchronization settings
in REPENTOGONOptions.h. Thus a separate launcher, runtime directory or rgon save
name is not proof of training isolation. Runtime installation, exact binary/release
hash, syncing configuration and restoration tests require a separate approved plan.

## Required capability matrix

All runtime statuses below are **unknown** on the proposed adapter. The fresh
startup log establishes version/mod loading, not bridge functionality.

| Capability | Source/API evidence and proposed method | Runtime result | Required later probe |
|---|---|---|---|
| Player observation | Installed LuaDocs EntityPlayer/GetHearts, Entity Position/Velocity; Isaac.GetPlayer | Unknown | Manually move approved player; compare streamed position/health to screen |
| Entities/current room | Isaac.GetRoomEntities, Game:GetRoom; baseline installed docs and candidate collectors | Unknown | Controlled visible room objects change snapshots; no hidden map fields |
| Frames | Game:GetFrameCount in installed LuaDocs; MC_POST_UPDATE/MC_POST_RENDER in enums | Unknown | Record engine vs callback counters over movement, pause/resume and room transition; measure rates rather than assuming FPS=steps |
| Transport/module load | Bundled socket/core.dll and json.lua exist; candidate requires --luadebug | Unknown | Authorized diagnostic mod checks module/API availability and version, nonblocking connect and partial I/O; no new DLL |
| Input application | MC_INPUT_ACTION exists; pressed/triggered/value hooks require correct semantics | Unknown | Later actions milestone: bounded independent movement/shooting and observed effect, including neutral |
| Input release | Custom deadline/watchdog required; candidate disconnect does not clear input | Unknown | Kill Python, close client, pause/resume, reconnect; prove release within specified measured bound |
| Episode endings | Baseline MC_POST_GAME_END(GameOver), MC_PRE_GAME_EXIT(ShouldSave), Entity:IsDead; exit != death | Unknown | Later lifecycle test distinguishes death, win, saved exit, room clear, respawn, truncation and transport fault |
| Controlled reset | Isaac.ExecuteCommand documented; reset/restart available only as future allowlisted lifecycle operation | Unknown | Isolated profile only: approved seed/run restart and new episode identity; validate progress/write set; no reset in this audit |
| Seed determinism, speed, multiple instances | No local probe | Unknown, optional | Separate design/authorization and evidence; not needed for initial observations |

Local game-shipped LuaDocs are the primary installed API reference.
[Game](https://wofsauge.github.io/IsaacDocs/rep/Game.html),
[Isaac](https://wofsauge.github.io/IsaacDocs/rep/Isaac.html) and
[callback maintainer documentation](https://wofsauge.github.io/IsaacDocs/rep/enums/ModCallbacks.html)
are supplementary current API references, not binary/runtime validation.

## Recommendation and concrete next task

**Implement a minimal custom adapter**, using original code and the game's
bundled LuaSocket after its availability is verified. Reuse unchanged fails the
required safety/identity contract. Adapting SocketBridge is legally plausible
under MIT but requires replacing networking/input lifecycle, removing console
execution and extender-only callbacks, and auditing excess sensors/oracle fields.
An original observation slice is smaller and avoids requiring REPENTOGON's
different runtime/save synchronization. The cost is implementing framing,
partial I/O and soak tests ourselves; do not pretend these already exist.

Next change: **bridge-handshake-and-observation**, native Windows, no RL/control.

1. Implement project-local Lua adapter and Python client with offline contract
   tests: bounded newline JSON v1, size/work limits, partial messages, incompatible
   version rejection, malformed input, clean exit and reconnect/new session.
2. Handshake reports protocol/mod/observation versions, actual game identity,
   runtime type, session ID and verified capability flags. Do not hardcode a claim
   of J460 compatibility or invent a build ID API; use explicit inspected metadata
   with provenance where the Lua API cannot report it.
3. Snapshot engine frame, callback counters, player position/health and current
   room only. Exclude seed/hidden room map and arbitrary engine object dumps.
   Use `settimeout(0)` before socket operations, bounded retries, output queue/
   backpressure policy, and correct partial I/O handling. No busy waiting.
4. Before any game probe, present the finished artifact hash and exact destination
   `<Game>/mods/isaac_threrisaifuture_observer/`, required launch option
   `--luadebug` if confirmed necessary, approved profile/write set, backup/
   restoration evidence and disable/removal procedure. Port selection must be
   verified free and bound only to 127.0.0.1; no firewall rule.
5. Only after specific authorization and verified isolation: activate that
   observation mod, launch approved instance and probe module loading first.
   If loading fails, record a capability fault and stop the game-test branch.
   Re-audit transport/runtime choice; do not install an alternate DLL silently.
6. On success, manually vary the approved player/room and correlate snapshots.
   Read for ten minutes with bounded queues and no leaks/hangs; test pause,
   malformed data and reconnect/new session. Record real frame/session evidence
   and cleanup. Control/watchdog tests belong to item 03; resets to item 05.

**Required user actions/decisions remaining:** finish/close the ordinary game at a
safe point; choose/authorize the training profile and Cloud policy; authorize
backup/isolation verification and later observer-mod/launch-option changes after
reviewing concrete artifacts. Repentance+ installation is already completed and
does not need repeating. No action-time authorization is requested by this audit.
