# Episode lifecycle: native gap review

Offline desk review. No code, tests, specs or STATUS were changed; no checks were run; no game
was launched. Sources: `episodes.py`, `actions.py`, `observer_client.py`, `entity_probe.py`,
`mod/observer/main.lua` (0.4.0), `docs/SAFE_ACTIONS.md`, `docs/ENTITY_OBSERVATION_PROTOCOL.md`,
`openspec/changes/episode-lifecycle/*`, `tests/test_episodes.py`. Anything not read is `unknown`.

## 1. Requirement -> code

| Requirement | Offline status | Native status |
|---|---|---|
| Death / clear = terminated, timeout = truncated | Done: `EpisodeController` (tests: timeout, clear, death-wins-tie) | Native missing: no oracle death/clear event is exported by `main.lua` (only `entity_frame`, health, room) |
| Infrastructure fault is not a transition | Done: `EpisodeFault(BridgeError)`, test_transport_fault | Runtime blocked: needs a real `GameBackend` that maps `BridgeError`/`PeerDisconnected` to it |
| Identity/freshness (session, epoch, room, frame, event interval) | Done in controller (stale frame check ~`episodes.py:208`) | Partly: Python clients validate snapshots; no adapter feeds them to the controller |
| Control release, idempotent stop | Done (`GameBackend.release`, test_stop) | Native: `release` command + Lua disconnect/watchdog exist; no `GameBackend.release` wired to `ActionClient.command("release")` |
| Consecutive episodes, new IDs | Done on the offline sim (100 episodes) | Native missing: no general episode start/reset backend; accepted bounded natural-death restart remains available. Runtime blocked |
| Synthetic labeling | Done | n/a |

`GameBackend.start_episode` and `step(action, repeat)` have no complete native
implementation. General episode start/reset and automatic slot selection are
missing; the accepted bounded natural-death restart is a separate existing mode.

## 2. Contract conflicts to resolve before claiming a synchronous GameBackend

1. **Entity vs action negotiation.** Both `ObserverConfig.__post_init__` and `main.lua` (~L174) reject
   `entity_observation_v1` together with `safe_actions_v1`/`death_restart_v1`. A policy loop needs
   entities and actions on one session. Needs a protocol change (new capability or lifted exclusion).
2. **No oracle stream.** `OracleEvent` exists only in Python/synthetic; death, clear and damage
   have no native source. Separation does not require a second port or mutually exclusive oracle
   access. Options: (a) separate port/connection; (b) one explicitly negotiated, bounded, typed
   multiplexed transport whose messages decode into distinct validated objects and distinct
   recording streams, with oracle data never reaching the policy/normalizer. Tradeoff: (b) needs
   one extra capability and a typed envelope but keeps one session/identity; (a) is simpler but
   doubles lifecycle/identity handling. No rule is invented here; the choice is for the spec.
3. **Action repeat vs timing.** Controller `repeat` is 1..15 game updates (default 3).
   Game logic runs at 30 updates/s (`env.py` `UPDATES_PER_SECOND`; 60 Hz is render rate). The
   accepted live probe advanced 296 engine frames in ~10 s, so 200 ms snapshots (`sample_ms`)
   normally span ~6 updates; pause and latency can change this (unknown). A native action holds
   until min(acceptance+250 ms, frame+frames) (<=15 frames); the ack frame is acceptance time, not
   an application count. "Step exactly N updates then observe" is not provided natively; a
   contract must distinguish requested action duration from actual observed elapsed updates.
   Preserve existing requirements; do not silently replace bounded step semantics with
   an arbitrarily later snapshot. Resolve frame-driven capture in the next design.
4. **Pause / reconnect.** `Snapshot.status` is active/paused/unavailable; `EntityFrame` has no
   paused field, `EntitySnapshot` carries the status. This is an integration decision (see D1),
   not a controller defect. Heartbeat lease is 500 ms; expiry closes the connection; reconnect
   gives a new session. A slow Python update between commands can drop the session, so the loop
   must be heartbeat-aware.
5. **Outcome classification.** `Snapshot.status` (observation.py) is only active, paused or
   unavailable; there is no exported distinct death/game-over outcome. Which callback fires in
   special death/revival cases is a runtime unknown. A disconnect must remain a fault, not death.
6. **Action lease.** The 120 s authority is nonrenewable within a mod load; no new approval or
   handshake may renew it and none is proposed. Natural-death bounded restart is already
   implemented and accepted; the missing piece is a general authorized episode lifecycle, not a
   reimplementation of that restart.

## 3. At most three native vertical increments

Each is observation-first and separate from start/reset and training.

**A. Observation-only monitor, outside `GameBackend`.** A separate attach-only class (not a
`GameBackend`) over `ObservationClient` with entity capability, yielding fresh frames with
bounded-wait filtering of `paused`/`unavailable` snapshots; stale active frames still fault and
`EpisodeController` freshness is untouched. It has no `step`/`reset`; any action/reset entry point,
if ever exposed, must raise explicitly (never ignore actions). Compat: no wire change. Offline
tests: fake peer, bounded pause wait, stale-active fault, disconnect -> fault. Acceptance scope:
observation diagnostics only; it does NOT satisfy GameBackend or the 100-episode criterion.

**B. Oracle event transport.** Opt-in negotiated capability (`oracle_events_v1`), either separate
connection or bounded typed multiplexing (section 2.2); distinct validated types and recording
streams, never in policy frames. Tests: schema/size bounds, separation test. Evidence needs a
future authorized runtime check (none authorized now).

**C. Contract-first controllable backend.** Spec first: combined entity+action capability
(lifting the current exclusion), frame synchronization and actual elapsed updates, explicit unsupported
reset/start, heartbeat handling, no lease renewal, explicit faults. Implementation follows reviewed specifications. Existing bounded ordinary-profile
action permission persists; verify current instance/slot and finite runtime authority
before testing, and obtain any genuinely additional authorization only when needed.

Primary-agent decision: prepare the contract for **C** first; **A** is optional
diagnostics and is not selected as another wrapper around the accepted recorder.
The review itself grants no runtime authority; existing permissions persist.
Training isolation and general reset authority remain blocked.

## 4. Permissions/prerequisites for 100 real episodes

- Ordinary-profile exception covers bounded action probes only; it is not training isolation.
  Training needs verified isolation (SAFE_ACTIONS).
- Restart cap: 3 attempts / 10 min per mod load; no 100-episode loop can rely on automatic restart.
- Action authority: 120 s, non-renewable, expires with epoch; private approval file for slot 2,
  `expires_at` <= 30 min; evidence per launch. Slot is operator-confirmed, not attested.
- Launch and slot selection manual; no save/Steam Cloud edits, no REPENTOGON, no forced resets.
- Approved experiment budget (steps, wall time, disk, stop conditions) before any run.
- Consequence: 100 real episodes are blocked until reset/start has an authorized design; do not
  count manual runs as test episodes.

## 5. Integration decisions (not demonstrated defects)

- **D1 pause vs freshness.** The controller correctly faults on a non-increasing `frame_id`.
  Paused snapshots may repeat frames; an adapter should filter `status == paused` snapshots
  within a bounded wait before yielding a fresh `StepResult`. Stale active frames must still
  fault. Do not weaken controller freshness.
- **D2 repeat vs sampling.** Default `repeat=3` updates (~100 ms) against 200 ms (~6 update)
  snapshots; the step contract must be redefined (2.3), not the sampler assumed.
- **D3 entity/action exclusion** blocks a controllable backend; resolve in the spec (increment C).

## Unknown

Runtime snapshot behavior at death/revival/game-over; actual update rate under pause/latency;
`update_id` vs engine frames when paused.

## Primary-agent review of revision 2

Accepted as an offline gap assessment, not runtime acceptance. Corrected the
remaining general-reset wording and avoided prescribing weaker step semantics.
An extra observation-only wrapper is not selected now because item 04 already
provides attach-only recording. Next: update the existing item-05 proposal,
specification, design and task breakdown for actual native integration before
code generation. Keep all current limits and the 100-episode acceptance gate.
