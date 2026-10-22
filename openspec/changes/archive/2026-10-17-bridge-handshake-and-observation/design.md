# Design

## Context

See proposal and audit. The initial baseline contained diagnostics only. The audited
transport is Lua connecting to a loopback Python listener; “client” means the
Python observation consumer, not TCP connection initiator. No transport change.

## Goals / Non-Goals

**Goals:** narrow typed wire boundary, observable faults and bounded callbacks.
**Non-Goals:** actions, learning, reset, oracle data, runtime installation.

## Decisions

### Observation launcher

Start-Isaac.cmd opens a terminal and calls the project Python launcher directly.
The launcher discovers Steam libraries (registry and local VDF)
or accepts --game-directory. It compares both installed observer artifacts with
project hashes and refuses an already running isaac-ng process. It does not copy
mods, alter options/Cloud, or touch saves. An in-process ObservationClient context
manager and event log under ignored runs/ complement the existing observe CLI.
Bind the listener before launching isaac-ng.exe with temporary --luadebug. No
readiness probe connects to the protocol port. Flush events and sampled progress
to the console; always close the owned listener, peer and log. Never terminate
the game, whose Steam launcher PID may
exit before the real game process appears. Record launch-requested separately
from the handshake as actual observation readiness. Defaults: 180 seconds to
connect, 3000 samples (approximately ten minutes at 5 Hz), 900 seconds total
session deadline. --preflight-only launches nothing; there is no running-game
bypass. Up to three reconnect attempts share the original duration/sample budget;
--reconnects permits 0..10. Transport failures wait for a fresh session;
malformed/incompatible protocol data fails immediately. Disconnects do not imply
death. The first live launcher exited on a user death/restart closing the peer;
that evidence motivated the bounded reconnect amendment. No game restart, training
or automated menu inputs. The initial PowerShell
entry was replaced after Windows PowerShell refused script execution; no
execution policy or security setting was changed.

The requested eventual target is Dead God on file 2. This launcher does not select
or attest the slot; display an explicit manual-selection requirement. Automatic
menu/slot API research and a future file identity check precede autonomous control.
Dead God progression/achievement eligibility are future milestones, not launcher
acceptance and not permission for gameplay automation in this change.


- Python standard-library sockets plus existing Pydantic strict/frozen models.
  Reject unknown/duplicate JSON keys, nonfinite numbers and type coercion.
- Python hello carries UUID-hex session and required capabilities. Lua echoes
  it in hello_ack; this is a host-assigned connection identity, not a game RNG
  value. It changes every accepted connection. Epoch/room-visit counters are
  observer-local lifetimes, not global map identifiers.
- One 16 KiB LF-delimited UTF-8 JSON message; no CR terminators or blank lines.
  Python retains combined input and uses an absolute deadline even for trickles.
  Accept/handshake/message defaults 10/3/3 seconds; configurable positive finite
  limits. Python owns listener and peer context managers.
- Lua single-file mod: nonblocking connect completion via getpeername, at most
  one 4096-byte read and one 4096-byte send per render callback. Preserve receive
  partials and send offsets; one <=16 KiB pending output, no accumulating queue.
  Retry connection once/second; handshake and stalled output expire after 3
  seconds measured by Isaac.GetTime. At most 5 snapshots/second; callbacks that
  do not fire cannot deliver status and Python must time out explicitly.
- Observe player 0; position is game room-space X-right/Y-down. Raw health
  includes red/max-red/soul in half-hearts and bone containers as counts, plus
  character type. Do not sum these or equate zero red hearts with death.
- MC_POST_GAME_STARTED increments epoch, MC_POST_NEW_ROOM increments room visit.
  MC_PRE_GAME_EXIT marks unavailable and closes transport. Capture in pcall;
  absent/failing state becomes unavailable. Frames may repeat on pause or
  render sampling but sequence never repeats. Game epoch permits frame reset.
- Handshake includes mod version, Lua _VERSION and extender presence, plus
  nullable game/build metadata with explicit operator-config/unavailable
  provenance. Vanilla game-version API not established: never hardcode audited
  version as runtime proof. Supported capabilities describe adapter wire
  features; successful capture is separate evidence.
- Use isolated test-only Lupa 2.6 (lua53) to execute original adapter code against
  fake Isaac/socket objects and the installed JSON source. Direct loading of the
  game's 32-bit DLL into 64-bit Python failed with WinError 193, so the test runtime
  is separate scratch tooling, not a production dependency. This tests callback/
  transport logic, not real-game ABI/module compatibility. No game files change.

## Risks / Trade-offs

- Rendering callbacks may stop in menus/loading -> unavailable when possible,
  explicit timeout otherwise; do not fabricate heartbeats.
- LuaSocket connect/error strings vary -> use numeric loopback, no DNS, test
  nil/error/partial handling; actual module/callback behavior remains gated.
- Same-user loopback has no authentication -> observe public current-room data
  only, no secrets, execution or controls; one connection, no public bind.
- Installed API docs support methods but do not prove J460 execution -> retain
  runtime acceptance tasks and exact deployment/rollback plan.

## Deployment

Project-local files only until approved profile and artifact authorization exist.
Prepare mod hash/destination, optional --luadebug and rollback in protocol docs.
Do not activate in the current ordinary profile. Keep the OpenSpec change active
if real-game acceptance is blocked.
