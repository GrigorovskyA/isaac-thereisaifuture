# Observation protocol v1 (read-only by default)

## Optional boundary reward support

`firing_boundary_support_v1` requires `firing_geometry_v1` and its measured grid.
It adds only `oracle.firing.boundary_support`: version1, row-major top-left patch
index, source player position, projected patch position and nullable ground-line
`clear`. The nearest fully walkable2x2 patch is selected by squared projection
distance (row-major ties), at most sqrt(2)*40 units away. At most1024 cells and
one extra ground CheckLine(mode0,threshold0,false,false) query per capture;
default/off and unsupported weapons add no query. Failure is unknown, never clear.
Positions belong to that snapshot; consumers validate source/projection/patch.
This is reward-only ground-line evidence, not body safety or a policy feature.
Observation schemas1/2 and649/723 inputs remain unchanged. Historical v4 ignores
the extension. `--boundary-progress-reward` explicitly selects `live-firing-v5`
and requires `--firing-position-reward`; v4 checkpoints cannot resume implicitly.
See [plan and qualification](../reports/2026-10-21-boundary-progress-plan.md).

Default read-only observation was accepted on J460 in the archived item-02 evidence.
Adapter 0.2.0 adds the optional [bounded post-death mode](DEATH_RESTART.md), whose
bounded real-game acceptance passed for one normal solo character-0 death. Existing default clients retain read-only behavior.

Source adapter 0.3.0 adds optional [native safe actions](SAFE_ACTIONS.md), disabled
pending local prerequisite approval. It is now passively deployed with the gate
disabled and matching hashes/preflight, but has no 0.3.0 runtime acceptance yet.
The 0.2.0 hashes/evidence below are historical; see the
[deployment follow-up](../reports/2026-10-17-safe-actions-passive-deployment.md).

## Transport and bounds

Python is the observation consumer but the TCP **listener**; Lua connects to it.
Only IPv4 `127.0.0.1` is accepted. Default port 9528 is explicit in both CLI
and the top-level Lua Config. Port 0 is useful for simulated peers only.
Do not expose the listener or add a firewall rule. Same-user loopback peers are
not authenticated. Default mode exposes no executable operations; the optional lifecycle
capability authorizes only the fixed after-death restart described in DEATH_RESTART.

One UTF-8 JSON object per LF. Maximum 131072 payload bytes (128 KiB since frame schema 6; 48 KiB before; frame schema 7 adds item catalog facts, see ENTITY_OBSERVATION_PROTOCOL) excluding LF; no CR,
empty records, duplicate keys, nonfinite numbers or unknown model fields.
Python retains combined messages and partial input; incomplete messages expire
against an absolute deadline, even if bytes keep trickling.
Defaults: accept 10 seconds, complete handshake 3 seconds, next message 3 seconds.
Timeouts are explicit infrastructure faults, not death, pause or success.

Lua uses settimeout(0), one read of at most 4096 bytes and one send of at most
4096 bytes per render callback. It retains receive partials and advances by the
last actually sent byte. Pending output is at most one bounded record; it samples
only when that record is flushed, at most five times per second. Connect/hello/
pending-output deadline is 3 seconds; reconnect delay is 1 second. No indefinite
wait, busy loop, unbounded queue or console endpoint exists. The 0.3.0 native
input callback returns nil unless separately authorized actions are held.
Callbacks that stop firing cannot maintain these wall-clock deadlines; Python
times out, and Lua checks expiry on the next callback.

## Handshake

Python sends a fresh UUID-hex connection session. The exact hello key order below
is required by the deliberately narrow Lua parser; whitespace is allowed, escaped
keys/values or alternate field order are not. Lua validates the decoder result
against this canonical syntax because the bundled decoder admits non-JSON
extensions. Capabilities can be a unique ordered subset of supported names.
The Python client requires the three read-only names below; explicit
--restart-after-death additionally requires death_restart_v1. Missing optional
support fails the handshake; ordinary observation never requests it.

```json
{"type":"hello","protocol_version":1,"schema_version":1,"session_id":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","required_capabilities":["snapshot_v1","availability","raw_health_v1"]}
```

Lua replies (response key order is irrelevant):

```json
{"type":"hello_ack","protocol_version":1,"schema_version":1,"session_id":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","capabilities":["snapshot_v1","availability","raw_health_v1","death_restart_v1"],"mod_version":"0.2.0","lua_version":"Lua 5.3","extender_present":false,"game":{"version":null,"steam_build":null,"provenance":"unavailable"}}
```

This is an example, not a captured game handshake. Lua reports actual `_VERSION`
and whether the REPENTOGON global is truthy, not an invented extender version.
No vanilla game-version function was established. Optional Config.game_version/
steam_build are explicitly `operator_config` metadata and must be cross-checked
with a fresh process/log and Steam manifest. Defaults remain null/unavailable.
An audit value must not be presented as runtime detection.

Capabilities describe implemented wire features, not proof that each Isaac API
works on a particular binary. Missing/unknown APIs produce unavailable state.
Unsupported hello versions/capabilities or malformed requests close Lua's peer
with a bounded console diagnostic. Python reports EOF/protocol/timeout explicitly.
For default observation and death restart, there are **no further Python-to-Lua
requests** after hello; any bytes close Lua. Only separately negotiated
safe_actions_v1 permits the bounded allowlist in SAFE_ACTIONS.md; no reset,
Lua/console execution or spawning messages exist. The death-restart opt-in
hello alone authorizes the local bounded after-death lifecycle; it cannot carry
command text or request a live-run reset.

## Snapshot and units

```json
{"type":"snapshot","schema_version":1,"session_id":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","sequence":1,"game_epoch":1,"frame_id":90,"update_id":80,"status":"active","reason":null,"room":{"visit_id":1},"player":{"index":0,"character_type":0,"position":{"x":320.0,"y":280.0},"health":{"red_half_hearts":6,"max_red_half_hearts":6,"soul_half_hearts":2,"bone_containers":0}}}
```

| Field | Meaning and lifetime |
|---|---|
| session_id | Host-assigned connection ID echoed by Lua; new on every accept, not a game RNG/seed |
| sequence | Strictly increasing transmitted snapshot count in that connection; gaps allowed |
| game_epoch | Observer-local game-start count; increases on MC_POST_GAME_STARTED, including continued games; starts 0 after mod load |
| frame_id | Game:GetFrameCount integer; nondecreasing within epoch; equal values permitted on pause/render sampling; resets require a new epoch |
| update_id | MC_POST_UPDATE callback count; never reset during this mod load; not assumed equivalent to engine frames or FPS |
| room.visit_id | Observer-local visit count from MC_POST_NEW_ROOM, reset on game start; identifies current visit within epoch, not a global room/map ID |
| status | active, paused (Game:IsPaused), or unavailable |
| player.index | Exactly 0: first local player only; no claim of multi-player/character-part completeness |
| character_type | Raw GetPlayerType enum; required to interpret health |
| position | Raw player.Position coordinates, game room-space units, X right, Y down; not screen pixels or tile indexes; finite and within +/-1,000,000 |
| red_half_hearts | GetHearts raw units, generally half-heart red fill |
| max_red_half_hearts | GetMaxHearts raw red capacity in half-hearts |
| soul_half_hearts | GetSoulHearts raw soul/black-heart combined fill in half-heart units |
| bone_containers | GetBoneHearts raw container count, not half-heart fill |

Health fields are **raw engine counters**, not a universal HP total. Red fill can
overlap bone-container fill; soul and black-heart composition is not separated.
Other health mechanics/resources and multiple controlled entities are omitted.
Zero red fill is not evidence of death (e.g. soul-health characters). Do not sum
fields, clamp them against one another, or derive termination. Integer counters
are bounded to 0..2^53-1; booleans/strings do not substitute for numbers.

Only the first player and current visible-room visit are read. No seed, level
map, undiscovered secret room, entity dump or oracle channel is sent.

Unavailable example:

```json
{"type":"snapshot","schema_version":1,"session_id":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","sequence":2,"game_epoch":1,"frame_id":null,"update_id":80,"status":"unavailable","reason":"state_read_failed","room":null,"player":null}
```

`not_in_game` means no observed game-start lifetime; `state_read_failed` means
player/room/API read was absent or failed. Menus/loading can stop render callbacks
entirely, causing timeout rather than a status packet. Failure to receive data does
not prove a menu or disconnect. The observer closes on game exit/mod unload.
It is not designed for injection/reload into an ordinary active run.

## Python usage and reconnect

From the repository root, after separately approved deployment/profile setup:

```powershell
.\.venv\Scripts\python.exe -m isaac_threrisaifuture.cli observe --host 127.0.0.1 --port 9528 --samples 50
.\.venv\Scripts\python.exe -m isaac_threrisaifuture.cli observe --port 9528 --samples 3000 --accept-timeout 30 --message-timeout 5 --reconnects 2
```

These commands only listen/read; they do not install/launch or control the game.
CLI prints listener info then validated handshake and snapshots as JSON lines.
It exits after the requested sample count, Ctrl+C, or a fault. Errors go to stderr
with exit 2; Ctrl+C closes sockets normally. Optional reconnects retry transport
faults a finite number of times; protocol violations fail immediately.

Typed API: `with ObservationClient(ObserverConfig(...)) as client:`, then
`client.accept()` -> HelloAck and `client.receive()` -> Snapshot. Explicit
`accept()` closes any previous peer and clears history. Wrong session, duplicate/
regressing sequence, regressing epoch/update/room visit or engine frame causes
ProtocolError and closes that peer. A new epoch allows a new frame origin.
`close()` is idempotent; context exit also closes on interruption.

## Offline verification

Normal Python simulated-peer tests:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_observer.py -q
```

Lua behavioral tests require isolated test-only Lupa 2.6, imported specifically
as lupa.lua53. Keep its binaries outside the repository and production venv:

```powershell
.\.venv\Scripts\python.exe -m pip install --target '<scratch>/lua-test-runtime' lupa==2.6 --no-deps
$env:PYTHONPATH = '<scratch>/lua-test-runtime'
$env:ISAAC_JSON_LUA = '<Game>/resources/scripts/json.lua'
.\.venv\Scripts\python.exe -m pytest tests/test_observer.py tests/test_lua_observer.py -q
.\scripts\Check.ps1
Remove-Item Env:PYTHONPATH, Env:ISAAC_JSON_LUA
```

The Lua suite otherwise reports a skip with a reason. Its interpreter, fake Isaac/
socket objects and real JSON **source** do not load the game or socket DLL and do
not establish module ABI, callback frequency, game responsiveness or actual state.
The initial direct DLL test failed because game Lua DLL is 32-bit and Python is
64-bit; isolated Lupa is test tooling only. No lock/runtime dependency was changed.

## Deployment and rollback plan РІР‚” NOT EXECUTED

Historical prerequisites: user closes ordinary gameplay safely; verified authorized training
profile/write isolation and backup/restoration evidence from GAME_SETUP.
Current ordinary saves/Cloud/configuration must not be changed by these tests.
Specific artifact/launch authorization is still needed; РІР‚СљimplementРІР‚Сњ alone does
not identify an approved profile or authorize changing its save/Cloud settings.

1. Historical 0.1.0 artifacts and SHA-256 (not the current 0.2.0 files):

   | File | SHA-256 |
   |---|---|
   | mod/observer/main.lua | 6C9D6D82AD81D7786CE96AE85D117228C39DC9CE762B8EC167F889EF8EA19577 |
   | mod/observer/metadata.xml | 9C09C406034A7171BF3EF224834508E6673387090D1B6F43473E0E7B38FEBFFA |

2. After authorization, copy those two files into the approved game installation's
   `mods/isaac_threrisaifuture_observer/`. Do not overwrite an existing directory.
   Default metadata is unknown; if adding operator metadata or changing port,
   recompute hashes and review the resulting artifact before deployment.
3. If necessary after a permitted module probe, append `--luadebug` to the
   approved instance's launch options, preserving/restoring prior text. Debug
   console EnableDebugConsole is not a substitute. Do not change global Steam,
   Cloud or unrelated mods. No new native DLL, REPENTOGON or firewall changes.
4. Enable only this observer in the approved profile, start Python listener, and
   launch only the approved instance. If module load fails, record fault/stop;
   do not silently add another transport or binary.
5. User performs manual movement and room changes; agent only records/compares.
   Verify actual handshake metadata provenance, advancing frames, positions,
   health and room visits. For ten minutes log counts and selected sanitized
   samples plus process memory/response observations; growth/no-hang claims need
   real before/after evidence. Test Python shutdown and reconnect/new session.
6. Stop Python, user exits approved game normally, disable observer in approved
   mod list. Close game before removing only the two installed files/new folder.
   Restore only the added launch option; check ordinary-profile write isolation.
   Never overwrite a live save or accept a Cloud conflict automatically.

This original item-02 plan was subsequently executed under the specifically
authorized read-only ordinary-profile exception; see the terminal-launcher report.
For the new 0.2.0 lifecycle deployment and acceptance, follow DEATH_RESTART.md.

## API/source basis

Installed game LuaDocs and enums establish method/callback references (including
MC_PRE_MOD_UNLOAD), not runtime proof. Refreshed primary transport documentation:
[LuaSocket TCP](https://lunarmodules.github.io/luasocket/tcp.html).
Supplementary maintained API docs:
[Game](https://wofsauge.github.io/IsaacDocs/rep/Game.html),
[EntityPlayer](https://wofsauge.github.io/IsaacDocs/rep/EntityPlayer.html).
Test tooling: [Lupa](https://github.com/scoder/lupa), pinned locally to 2.6.

## Ordinary-profile authorization amendment

Adapter 0.3.1 adds the explicit user-approved ordinary-profile action exception,
private expiring JSON approval and native tear/release diagnostics described in
SAFE_ACTIONS.md. It is deployed with matching hashes/preflight. No private approval
or live action session has been activated yet. Observation fields and default
read-only behavior remain unchanged; launch/selection remain manual.
