# Native safe actions v1

Roadmap item 03 / active OpenSpec change `bridge-safe-actions`. Installed source
adapter 0.3.1 supports explicit ordinary-profile action approval, a private
expiring local record and a finite attach-only probe. Default observation remains
read-only. No game has been launched or action test executed with 0.3.1 yet.

## Current authorization and prerequisites

On 2026-10-17 the user explicitly approved movement and shooting directly on
their ordinary profile, and asked to remember this for future bounded tests.
This supersedes the earlier isolation-only gate for these checks. Do not ask
again for that same ordinary-profile permission. This is an approved exception,
not evidence of isolation. Verified isolation remains required for training.
No save/Cloud edits, forced resets, startup automation, REPENTOGON, unbounded
supervision or relaxation of the three-attempt/ten-minute restart cap is authorized.

Before a live probe, verify the actual process, 0.3.1 handshake, game epoch and
operator-confirmed active slot 2 with an active solo character in a safe room.
Launch/selection remain manual. **Current pending input: game is closed and the
user has not yet confirmed the newly selected slot/room.** The Lua API still does
not attest the slot; report manual confirmation honestly. Backups and slot 2 do
not establish isolation. Existing shared options/mod-data/Cloud risks remain
shared under the user's explicit exception.

Source Config.action_authorization remains nil. After current slot confirmation,
write the private installed `<Game>/mods/isaac_threrisaifuture_observer/action_authorization.json`
with `profile_id`, `profile_mode` (`isolated` or `ordinary_profile_exception`),
`profile_evidence`, `slot_evidence`, `runtime_authorization`, `slot=2`, current
`game_epoch`, and integer Unix `expires_at` no more than 30 minutes ahead.
Evidence references must be nonblank and <=128 characters. This file stays out
of Git and is not a save. Remove it after the bounded check. Python alone cannot
populate Lua authority through the socket.

Lua reads at most 2049 bytes from this fixed local path during hello; absent
files keep observation available and can be supplied after read-only slot checks.
A successfully loaded record is cached once per mod load. Input authority expires
120 seconds after the first action handshake, with no reconnect renewal. Exit,
epoch change, local wall expiry and all existing cleanup guards invalidate it.
Do not reuse a record across launches; bind its evidence to the actual process.
No private approval file has been activated for the pending test.

## Transport and compatibility

Use the existing IPv4 loopback TCP listener, port 9528 by default, bounded LF JSON,
protocol/schema 1. No new dependencies, DLLs, REPENTOGON, screenshots or injected
keys. The three observation capabilities remain mandatory. Request
`safe_actions_v1` in hello only after prerequisites; Lua advertises it only when
its local gate validates. `death_restart_v1` and actions are mutually exclusive;
its existing three-attempt/ten-minute limit and fixed restart are unchanged.
No post-hello bytes are allowed in observation or death-restart modes.

Hello and snapshot fields retain OBSERVATION_PROTOCOL semantics. Native action
commands add at most 1024 bytes excluding LF; Lua reads <=4096 bytes, processes
at most one command and sends <=4096 bytes per render callback. The total pending
input is capped at 1025 bytes including LF. A burst exceeding that cap disconnects;
there is no unbounded request queue. Pending output remains one <=16384-byte
record with a three-second deadline. Use serialized transactions, not pipelining.
Lua disconnects on malformed/incompatible/stale/replayed requests and clears held
bridge inputs. A rejected command has no success ack; EOF/timeout is a fault.

## Commands

Canonical key order below is required. Whitespace outside strings is allowed;
escaped names/values, duplicate/unknown fields, alternate order and non-JSON
extensions are rejected. Every integer is bounded to 0..2^53-1, sequence starts
at 1 and strictly increases per fresh session. Versions must be exactly 1.

```json
{"type":"command","protocol_version":1,"session_id":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","sequence":1,"game_epoch":1,"room_visit":1,"frame_id":20,"kind":"action","move":"right","shoot":"up","frames":5}
```

| Field | Meaning |
|---|---|
| session_id | Fresh negotiated connection UUID; previous sessions never replay |
| game_epoch | Current mod-local game-start count, also covered by local approval |
| room_visit | Current room.visit_id; old-room actions rejected |
| frame_id | Exact frame of most recently fully sent snapshot, current engine frame must be in [frame_id, frame_id+15] |
| kind | action, heartbeat or release only |
| move / shoot | Independently none, left, right, up, down; no diagonal/bomb/item/menu/reset operations |
| frames | action: 1..15; heartbeat/release: exactly 0, with both directions none |

`action` with both directions `none` is explicit neutral: all eight button values
are zero for the bounded interval. `release` removes the override and returns
manual handling immediately; it does not force the operator's physical keys up.
Releasing cannot undo shots already fired or immediate velocity/inertia.

Each accepted command refreshes the heartbeat lease to 500 ms. An action holds
until the earliest of acceptance+250 ms or acceptance_frame+frames. Heartbeat
never extends the action. There is no implicit action repeat. Pause, death,
co-op/unavailable state, room/floor/run transition, exit, unload or callback fault
clears holds. Game over also disarms actions. Disconnection clears when detected;
Python failure without FIN cannot keep an override past the action deadline.
Watchdogs run on render, update and each native input poll, preventing stale
resume after a callback gap. No callback can execute in a suspended process;
the bound means no expired bridge input on the next poll, not a scheduling promise.
After heartbeat expiry the connection closes; reconnect is required.

```json
{"type":"command_ack","protocol_version":1,"session_id":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","sequence":1,"game_epoch":1,"room_visit":1,"frame_id":21,"kind":"action","status":"accepted"}
```

Ack frame is acceptance time, not a count of actual input applications. Ack
identity must match the command and frame must be within the 15-frame freshness
window. A missing ack is an infrastructure fault; never replay automatically.
Snapshots can arrive before an ack and retain normal monotonic validation.

## Native input and Python API

Installed `resources/scripts/enums.lua` declares MC_INPUT_ACTION=13,
movement/shooting ButtonAction 0..7, and InputHook 0/1/2. The
[callback documentation](https://wofsauge.github.io/IsaacDocs/rep/enums/ModCallbacks.html#mc_input_action)
defines nil as no override and boolean/value return types. The
[InputHook reference](https://wofsauge.github.io/IsaacDocs/rep/enums/InputHook.html)
and [ButtonAction reference](https://wofsauge.github.io/IsaacDocs/rep/enums/ButtonAction.html)
were checked on 2026-10-17. This is source evidence, not J460 runtime proof.

Only an entity whose native player pointer matches Isaac.GetPlayer(0) receives
an override. GET_ACTION_VALUE returns 0/1, IS_ACTION_PRESSED boolean, and
IS_ACTION_TRIGGERED false for these continuous actions. Other buttons/entities
and released state return nil. Other mods can override native input independently;
verify the approved mod set and actual effects.

`isaac_threrisaifuture.actions.ActionClient(config, approval)` is a synchronous,
single-caller attach-only context manager. `ActionApproval` requires the same
reviewed evidence references, slot and epoch. It cannot set Lua authority.
Call `accept()`, `receive()` for a fresh active snapshot, then
`command("action", move="right", shoot="up", frames=5)`,
`command("action", frames=1)` for neutral, `command("heartbeat")` or
`command("release")`. Read current snapshots before later commands. Stale sampled
frames are rejected rather than silently refreshed. Command ack deadline is at
most 500 ms; errors/interrupt/context exit close sockets and discard cached state.
There is no background sender, reconnect replay or automatic authority renewal.
Default `ObservationClient` remains compatible with earlier 0.2.0/0.3.0 peers.

## Required live acceptance (pending manual launch/slot confirmation, 0/50)

After current instance/slot checks and reviewed deployment, manually launch/select
the approved profile and record actual versions, hashes, process/mod-load, slot,
session, epoch, room visit and frames. Use a solo ordinary-shooting character in
an approved safe room. Set a finite 50-sequence / 120-second maximum, with operator
stop available; stop immediately on unexpected movement, transition, identity,
errors or effects. No forced reset/death, spawning or save manipulation.

Use ten cases repeated five times: four movement-only directions; four
shooting-only directions; right+up and left+down combined. Each sequence needs
before/after position and native projectile/fire-event evidence plus operator
correlation, then neutral and release. An input return or ack alone is not proof.
Record collisions/no shot/failures honestly; do not count those cases as passed.
Measure release deadline with the last actual input poll and action receipt,
not only with a Python process exit timestamp. Separately test socket disconnect
and Python termination while holding; demonstrate no stale poll past 250 ms,
manual control afterward, and fresh reconnect without replay. A stalled-client
(no FIN) test exercises the deadline rather than relying only on EOF.
If engine callbacks stop, report the unmeasured interval and verify expired input
on resume. Preserve private traces locally; commit a sanitized report with all
50 outcomes and cleanup measurements. Until these pass, do not archive.

## Deployment boundary

Historical passive 0.3.0 deployment: after user-confirmed normal game exit and
an installation request, the two 0.2.0
adapter files were backed up with verified hashes and 0.3.0 installed with its
action gate nil. Installed/source hashes match and launcher --preflight-only
passed. No process was launched. See the
[deployment report](../reports/2026-10-17-safe-actions-passive-deployment.md).
Accepted 0.2.0 hashes in DEATH_RESTART.md are historical; no new runtime acceptance
is implied. Manual launch/selection and read-only handshake can verify loading.
Action enablement and the 50 sequences remain blocked on the prerequisites above.

## Finite attach-only probe

After confirmation and private approval creation, use the existing project Python:

```powershell
.\.venv\Scripts\python.exe -m isaac_threrisaifuture.action_probe --approval '<private-installed-approval-path>' --confirmed-save-slot 2 --sequences 50 --output 'reports/local/action-probe.jsonl'
```

The output path must be new. The probe never launches/selects/resets. It permits
1..50 sequences / 120 seconds, closes on interruption/error, refuses paused or
changed room/epoch/health and refuses movement near room boundaries. Each case
uses one two-frame movement pulse. Shooting uses up to three refreshes; movement
is none on subsequent shooting refreshes,
then neutral/release. Actual movement and matching native tear diagnostics must
still be reviewed; `commands_completed` is not full acceptance. Disconnect,
Python termination and silent-stall cleanup need separate controlled cases.

The native MC_POST_FIRE_TEAR=61 source and
[callback reference](https://wofsauge.github.io/IsaacDocs/rep/enums/ModCallbacks.html#mc_post_fire_tear)
were checked. Diagnostics record command sequence/session/epoch, frame, local
milliseconds, actual player position and tear velocity. At most four tear events
are inspected per action, with identical diagnostics deduplicated. Other weapons
are not counted as verified tear evidence. No projectile is spawned by the bridge.

Current 0.3.1 installation and authorization amendment are recorded in
[the latest evidence](../reports/2026-10-17-ordinary-profile-action-authorization.md).
It supersedes the earlier isolation-only action-test restriction. No private
approval has yet been installed because the current slot/room confirmation is
pending; that pending confirmation is not a repeated profile-permission request.
