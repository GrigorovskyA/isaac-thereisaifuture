## Context

`ObservationClient`/`ActionClient` provide a validated single-peer transport; nothing owns
episodes. AGENTS.md requires `terminated`, `truncated` and infrastructure faults to stay distinct.

## Decisions

- **Backend seam**: a `GameBackend` Protocol (`start_episode`, `step(action, repeat)`, `release`,
  `close`) returns `StepResult(frame, events)`. The real bridge backend is future work.
- **Outcomes**: `death` and `cleared` are terminal, `timeout` is truncation. A same-interval death
  and clear resolves to death (conservative). `unknown` is a further truncation for results whose
  terminal-event coverage is incomplete (see "Terminal outcome coverage").
- **Faults**: a backend `BridgeError`/`ValueError` or an identity violation raises `EpisodeFault`,
  appends a `FaultRecord`, releases control and ends the episode. Faults are never transitions.
  Non-infrastructure exceptions (for example `KeyboardInterrupt`) still release and propagate.
- **Identity**: the first frame fixes session, epoch and room visit. Later frames must keep session
  and epoch, strictly increase `frame_id`, keep the room visit unless the scenario allows room
  changes, and every event must lie in (previous frame, frame] with the frame's session and epoch.
- **Time**: elapsed game updates are `frame_id` differences, not wall time; the limit is the
  scenario's `max_game_updates`.
- **Summary**: gameplay facts (damage taken, enemy HP removed, kills, clear, death) are accumulated
  from oracle events independent of any reward. The clear and death facts are tri-state (see
  "Terminal outcome coverage"): an absent event is not evidence of absence without coverage.
- **Toy backend**: `SyntheticRoomBackend` is deterministic per seed, labels its data `synthetic`
  and supports an injected timeout for fault tests.

## Risks / Trade-offs

- `repeat` and the 15-update bound mirror the action protocol; real latency is unmeasured.
- Exact mid-episode resume is not promised (matches ARCHITECTURE).

## Native integration decisions (revision 2)

- **Negotiation**: add one explicit capability (working name `entity_action_v1`) combining entity
  frames with bounded actions on one session. Missing capability fails the handshake; default
  clients are unchanged; death restart stays mutually exclusive; approval, heartbeat (500 ms),
  per-command freshness (<=15 frames) and the nonrenewable 120 s lease are unchanged.
- **Step contract**: game logic runs at 30 updates/s (rendering 60 Hz is not used); a 200 ms
  snapshot spans about six updates, unmeasured under pause/latency. A native step returns requested
  repeat, actual elapsed updates (`frame_id` delta), and separate `accepted`/`completed` flags.
  An ack is acceptance only. Early expiry (hold deadline, transition, input fault) is reported or
  faults. A bounded wait elapses into `EpisodeFault`. The step is never satisfied by an arbitrarily
  later snapshot.
- **Oracle events**: typed bounded messages with session, epoch, frame and event ID, validated into
  `OracleEvent`, deduplicated per session, in-interval. Multiplexing on the one connection is
  allowed; a second port is not required. Oracle objects and recordings stay separate from
  policy frames and the normalizer. No death/clear inference from disconnect, zero health or empty rooms.
- **Pause/transitions**: the adapter drops paused/unavailable snapshots within a bounded deadline;
  stale active frames still fault; `EpisodeController` is untouched.
- **Gate**: start/reset and training stay blocked; unsupported methods raise explicitly.
- **Unknown (needs a runtime probe before claiming support)**: callback order and snapshot status in
  death, revival (extra lives) and room/floor transitions; whether input hooks fire during a pause;
  actual updates per 200 ms sample; whether MC_POST_GAME_END precedes disconnect on death.
  The probe is observation-only, uses the existing bounded attach path and needs explicit
  authorization; none is authorized by this change as written.

## Native integration decisions: remaining open items

Capability and receipt shapes are frozen below. The 16384-byte wire limit is
unchanged; oracle events are separate messages, never added to a policy frame.
Native multiplexing still needs a bounded event budget and explicit delivery
ordering/watermark so a completion cannot silently omit late interval events.
Lua callback/application timing still requires probes before runtime acceptance.

## Migration

Additive.

## Frozen first coding slice: native step models

Capability name: entity_action_v1, advertised only when entity APIs and existing
action authority are available. Existing modes remain unchanged and cannot mix
with this capability; death_restart_v1 is incompatible. Initial code is offline
Python models only, not a deployed protocol or complete GameBackend.

StepCommand derives the existing Command format but changes type to step_command
and restricts kind to action and frames to 1..15. Its other fields and canonical
ordering remain as in Command. This prevents an old peer from silently applying
a new command as a legacy action. Existing CommandAck is acceptance only.

StepCompletion has type step_completion, protocol_version=1, session_id,
sequence (command sequence, >=1), game_epoch, room_visit, accepted_frame,
requested_updates (1..15), elapsed_updates, status, reason and frame (EntityFrame).
All counters use the existing strict bounded counter type. Nested frame identity
must match session/epoch/room, provenance must be game_api, and its frame_id must
be >= accepted_frame. elapsed_updates must equal that frame delta exactly.

Status is completed, expired or cancelled. Reasons are interval_elapsed,
wall_deadline, pause, transition, input_fault or explicit_release. completed
requires interval_elapsed and elapsed_updates == requested_updates; expired
requires wall_deadline; cancelled requires one of the other four reasons. A
frame arbitrarily later than the requested interval must never count completed.
Noncompleted results are failure facts, never successful episode transitions.
Lost/crossed identity that cannot produce a consistent result must fault instead.

validate_completion(command, ack, result) checks all three session/sequence/
epoch/room identities, action kind, accepted_frame == ack.frame_id,
requested_updates == command.frames, and acceptance freshness (ack.frame_id is
between command.frame_id and command.frame_id+15). It validates a coherent
receipt; it does not manufacture engine application evidence. Native callback
order/input exposure still require implementation and real probes before any
completion is accepted as installed-game support.

Serialize/parse with existing bounded decode: 16384 wire bytes, unknown fields,
invalid JSON, bool-as-integer versions/counters and incompatible versions fail.
No oracle events are inserted into these policy frames. Oracle envelope and
bounded ordered deduplication are a later separate coding task.

## Frozen next coding slice: native oracle envelopes

NativeOracleEvent is a separate WireModel with type native_oracle_event,
protocol_version=1, session_id, game_epoch, room_visit, frame_id, event_id (positive
bounded strict integer) and event (the existing OracleEvent). Require game_api
provenance and exact nested session/epoch/room/frame agreement. Do not change
OracleEvent or actor fields. Event identity must survive recording/replay.

NativeEventCursor is fixed to one validated session and game epoch and retains
only the last contiguous event_id (initially zero). take(envelope, start_frame,
end_frame) returns the entire native envelope or None for an already consumed
ID. Always validate session/epoch first. Duplicates <= last_id are suppressed
before interval validation so replay from a previous step is harmless. A new ID
must be last_id+1; gaps fault. Its frame must be in (start_frame,end_frame].
Both bounds must always be strict bounded integers with start_frame < end_frame;
validate these parameters even for duplicates. The duplicate exception applies
only to the event frame being outside the current interval.
Invalid context/gap/interval must not advance the cursor. Keep O(1) cursor state;
no unbounded seen-event set. Reconnect constructs a new cursor and never renews
runtime authority. This is deduplication, not reward/outcome inference.

Add native_oracle_events as an explicit recording stream with NativeOracleEvent
as its only record type. Preserve policy_frames and oracle_events behavior.
For the recorder provenance check, derive provenance from envelope.event
(either an internal read-only property or a recorder helper); do not add an
unplanned serialized actor field.
Manifests still use observation schema 1; old readers reject the new stream
explicitly. The native stream preserves event_id; do not discard the envelope
and silently lose identity. Existing bounded line I/O/provenance/version checks
apply. Mixed streams remain rejected. No encoder or policy accepts oracle data.
No sockets, native event generation, inference of outcomes or Lua changes in
this coding slice; those require later tasks and real API evidence.

### Task 3.6 export eligibility gate (2026-10-19)

The envelope, cursor and Python outbox define transport shape; they do not establish
that a game callback has the meaning required by `OracleEvent`. The model requires
exact entity generations for enemy events, realized amounts for damage/healing,
and a damage source for player damage. Keep callback facts in the default-off
diagnostic stream until each field has a verified source. Never convert attempted
damage, net HP deltas, removal, an empty enemy list, or a clean-award candidate
directly into an oracle label.

The installed callback names and the earlier primary-source audit are candidate
evidence only. The audit found no complete producer mapping for any of the seven
existing kinds:

| Oracle kind | Candidate signal | Evidence still needed before export |
| --- | --- | --- |
| `enemy_spawned` | `MC_POST_NPC_INIT` | Stable spawn generation through morph/re-init and complete initial identity. |
| `enemy_damaged` | `MC_ENTITY_TAKE_DMG` plus later HP samples | Applied amount, cancellation/clamping and concurrent-hit attribution. |
| `enemy_killed` | `MC_POST_ENTITY_KILL` / `MC_POST_NPC_DEATH` | Verified terminal timing and identity across death, removal and room unload. |
| `player_damaged` | `MC_ENTITY_TAKE_DMG` plus player samples | Realized health loss and exact enemy/self/environment source. |
| `player_healed` | No suitable source established | Attributed healing amount distinct from damage, max-HP and other net changes. |
| `room_cleared` | `MC_PRE_SPAWN_CLEAN_AWARD` | Verified clear semantics and delivery for the supported room classes. |
| `player_died` | `MC_POST_GAME_END` game-over flag | Extra-life/revival timing and reliable event delivery before disconnect. |

Capability decision (contract review, 2026-10-19): negotiate per kind; there is no
aggregate all-kinds capability. Each exportable kind gets one exact versioned name
(working form `oracle_<kind>_v1`, for example `oracle_enemy_killed_v1`). The generic
"native-step capability" is the exact existing name `entity_action_v1` (Python
constant `NATIVE_EPISODE_CAPABILITY` in `observer_client.py`), the already-defined
native-step transport gate; no additional aggregate all-kinds or transport-mode
capability is introduced. Each of the seven `oracle_<kind>_v1` names is a new
advertised per-kind capability entry. Per-kind names are
valid only together with `entity_action_v1`, which owns envelope, cursor and barrier
transport. A future negotiation test must assert that a per-kind name with any other
combination (default, live loop, probe, actions, restart) fails, and that a required
kind without `entity_action_v1` in the same ack fails. A producer
advertises a kind only while its verified source and every per-load resource it
needs are available. Python requires exactly the kinds its consumers use, by exact
name with no prefix or version fallback. Changed field semantics need a new version.
The worst-case HelloAck list is exactly the existing 16-entry limit: eight other
currently advertised names, `entity_action_v1` and seven per-kind names. Export must
stay within it; do not raise the limit.

Fail closed: an old producer lacks kind names, so any required kind fails the hello
before a snapshot or command; a partial producer fails for any missing required
kind; an unsupported kind is never advertised. The handshake is immutable, so
exhaustion of a required source or per-load resource is handled by timing. Before
hello, the producer omits that kind and a client requiring it fails the hello. After
`hello_ack`, the negotiated capability cannot be withdrawn from that ack, so the
producer must fault and close the active session (Python treats it as an
infrastructure fault) and omit the kind from later handshakes. It must never keep
the session running silently while events stop. An
envelope whose kind was not negotiated is a protocol fault. Never substitute
frame-delta derivation, diagnostic probe records, disconnects, zero health or an
empty enemy list for a missing kind.

Missing is not negative. Only a negotiated kind's absence from a completed,
barrier-validated interval inside its producer's coverage window means none
occurred. Otherwise, including faulted, cancelled or expired steps, absence is
unknown: derive no zero counts, false died/cleared flags, reward terms or timeout
claim. A native backend lacking a terminal kind its scenario needs must refuse to
start. Consumers require identity-linked kinds together (`enemy_damaged` and
`enemy_killed` rewards need the same generation's `enemy_spawned` initial HP) and
receive the negotiated kind set with the session and any native recording.

Eligibility (2026-10-19): no kind is eligible for Lua export. One bounded passive
0.5.0-dev run (`reports/2026-10-19-oracle-probe-live-runtime.md`) observed candidate
callbacks for `enemy_spawned`, `enemy_damaged`, `enemy_killed` and `room_cleared`
but established no spawn identity, applied damage, room clear, terminal outcome,
universal ordering, delivery or transaction barrier. Player-target damage, healing,
death/revival, floor change and game end were not reported; `player_healed` still
has no candidate source. Room/floor transitions and game end are context facts, not
oracle kinds; game end alone is not player death. Each kind must still pass its
bounded runtime gate, including envelope identity, attach baseline, callback order,
event retention/delivery and cleanup; offline serializer, queue and fake-callback
tests cannot satisfy it. Until then emit no `native_oracle_event` and leave tasks
3.6 and 3.8 open. See `reports/2026-10-17-native-oracle-api-audit.md` and
`reports/2026-10-19-oracle-event-contract-review.md`.

### Python per-kind negotiation groundwork (offline, 2026-10-19)

Implemented in `observer_client.py` as handshake groundwork only: no Lua advertisement,
`OracleEvent` emission, producer coverage claim or runtime eligibility. Append
`native_oracle_kinds: tuple[OracleKind, ...] | None = None` to `ObserverConfig`
(positional compatibility preserved; `None` requests nothing). A non-`None` value must be an
actual nonempty tuple of unique, exact `OracleKind` strings and requires
`native_episode_steps=True`. Unknown, non-string, duplicate, empty, list/set/string,
no-native-mode and every other-mode combination raise `ValueError` at construction, before
a listener opens or a hello is sent. `oracle_kind_capability(kind)` returns the exact
`oracle_<kind>_v1` name.

For native mode the hello requires the three base names, `entity_action_v1`, then the requested
per-kind names in request order. Default and all existing modes build the same lists as before,
even when the peer advertises per-kind names. The existing subset check against the ack owns
fail-closed behavior: an old or partial peer, a missing `entity_action_v1`, or any version,
prefix, aggregate or different-kind name fails before a snapshot or command and clears the
peer. `HelloAck` keeps `max_length=16`; tests build the worst case (eight other names,
`entity_action_v1`, seven kind names) and reject a seventeenth entry. A passing handshake
is only an offered contract: it does not prove a callback source, identity, delivery or barrier.
Lua export (3.6) and native transaction multiplexing (3.8) stay open.

## Frozen next coding slice: combined negotiation groundwork

Append native_episode_steps: bool=False to ObserverConfig (preserve positional
compatibility). Require an actual bool. If true, reject safe_actions,
entity_observations or restart_after_death also being true; legacy exclusions
remain unchanged. Define NATIVE_EPISODE_CAPABILITY=entity_action_v1 in
observer_client.py, without importing native_protocol.py (it imports actions,
which imports observer_client). Required hello capabilities are the three base
capabilities plus only the new combined name for this mode; no silent fallback.

For this mode the base snapshot decoder uses EntitySnapshot and existing outer
ordering validation. It still rejects unsolicited oracle/step messages: bounded
multiplexing belongs to the later dedicated native client. Default and existing
modes retain exact shape/negotiation. No CLI flag, socket command sender, Lua
advertisement, approval bypass or deployment is introduced by this groundwork.
The installed 0.4.0 cannot negotiate the new capability and must fail closed.


## Frozen next coding slice: bounded native snapshot waiting

Create native_client.py with NativeStepClient(ObservationClient) as the future
native transaction transport, not a GameBackend or a second observation CLI.
Require config.native_episode_steps=True explicitly. No other mode is accepted.
This first transport slice sends no command and has no approval or authority
renewal path. Inherit the existing combined negotiation and listener behavior.

receive_active() returns EntitySnapshot, using one monotonic deadline computed
from config.message_timeout for the entire call. Read/decode/validate every
snapshot with the existing bounded _read_line and _validate_snapshot. Do not call
receive() repeatedly with a fresh timeout. Check the deadline explicitly on each
iteration and before returning even if buffered lines are immediately available.
Paused/unavailable snapshots may repeat engine frames and are skipped within
that same deadline. All sequence/update/session/base identity checks still apply.
An active snapshot must have a frame strictly greater than the last active
snapshot in this connection. The first active snapshot fixes epoch/room;
a subsequent active snapshot crossing either faults. First active state after
accept may be in any valid epoch. close_peer clears this state; reconnect has
new session/counters and never changes game authority. Keep only fixed-size
connection state, with no snapshot/event queue or unbounded history.

On read/decode/identity/deadline failure, close_peer and raise EpisodeFault
(wrap BridgeError/ValueError while retaining the cause). KeyboardInterrupt and
other BaseException still close and propagate. release() closes the peer
idempotently; no synthetic neutral acknowledgement is produced. Server-side
disconnect/deadline cleanup remains required and unverified for the new mode.

Until real step transport and start/reset authority exist, start_episode,
reset and step raise UnsupportedNativeOperation (EpisodeFault subclass) without
sending ANY command; close an existing peer before raising as conservative
cleanup. No no-op StepResult, inferred outcome, ignored action or GameBackend
success is permitted. No CLI, Lua change, deployment, training or runtime action.
Tests with bounded simulated sockets verify pause/resume, unavailable/resume,
absolute deadline under frequent paused traffic, stale active rejection, epoch/
room faults, malformed messages, disconnect, same-listener reconnect, release
idempotence, and unsupported operations producing EOF with zero command bytes.
Tests must surface peer-thread failures and join every thread in bounded cleanup.


## Frozen next coding slice: explicit event watermark model

The source audit is reports/2026-10-17-native-lua-plan.md; its primary review
qualifies recommendations and lists remaining runtime/order unknowns.
Append required last_event_id: Counter to StepCompletion (no default). This is
an undeployed native protocol refinement; old missing-field receipts fail closed.
It names the last contiguous oracle event at the completion barrier; zero means
none in the session, not a per-step reset. Keep all existing identity/status/frame
and byte-limit validation unchanged. No field is added to policy EntityFrame.

Add validate_event_barrier(result: StepCompletion, last_event_id: int) -> None.
Validate observed last_event_id as an actual int in 0..2**53-1, then require exact
equality to result.last_event_id; both missing tail and cursor ahead fault with
ProtocolError. This helper is independent of validate_completion and does not
claim a caller used the correct session cursor. Future transaction code must
first match command/result identity and consume interval events using its bound
NativeEventCursor, then pass cursor.last_id. Watermark alone proves no physical
input and cannot detect a malicious peer inventing a consistent history.

Model/helper tests cover zero, positive/MAX, round trip, missing field, invalid
strict counter values, matched barriers, missing tail, cursor ahead and malformed
observed counters. Update the shared simulated completion fixture to explicitly
provide zero. No client transaction, sockets, Lua, CLI or runtime work in this slice.

Future requirements: first interval starts at the policy frame delivered to the
caller; neutral elapsed updates count. Attach baseline must not silently lose
post-initial-frame events. Completion cannot ignore late same-interval events.
Explicit bounded event delivery/queue/ordering and death handling are still open.


## Frozen next coding slice: bounded receipt assembler (no transport sender)

Add native_receipts.py with immutable NativeStepReceipt(ack, completion, events),
where events is a tuple of deduplicated NativeOracleEvent envelopes, and
NativeReceiptAssembler(command, baseline, cursor). baseline is a game_api
EntityFrame matching the command session/epoch/room/frame exactly; cursor must
match session/epoch. Add read-only session_id and game_epoch properties to
NativeEventCursor to check this binding. Initial cursor.last_id is captured.

feed(raw: bytes) receives one delimiter-free wire record and returns None or the
completed receipt. It sends nothing and does not read sockets or implement a
GameBackend. Order is exactly one matching action CommandAck, then zero or more
NativeOracleEvent records, then one completed StepCompletion. Other records,
wrong identity/kind/sequence/freshness, a second ack, or input after failure or
completion raise ProtocolError. Noncompleted receipts fault explicitly; they
are never yielded as successful transitions. Use existing bounded decode/models
and validate_completion. A matching receipt is not proof of physical input.

Bounds: <=32 event records INCLUDING duplicates, <=34 records total, <=65536
encoded bytes total (including ack/events/completion), and existing <=16384 bytes
per record. Check budgets before storing, keep no unbounded history. Every fault
invalidates this assembler and clears pending event storage. No timer: the later
socket client must enforce its own single absolute transaction deadline.

Before mutating the supplied cursor, validate the whole receipt: command/ack/
completion matching, all event session/epoch/room context, new contiguous IDs
from the captured last_id, new-event frames in (baseline.frame_id, completion
frame_id], and exact final watermark. Previously consumed IDs are deduplicated
with existing cursor semantics (old frame may be outside interval, context still
must match). Require the supplied cursor.last_id still equals its captured value
before committing; concurrent cursor use faults. Then consume through cursor.take
and yield only deduplicated envelopes. All preceding validation must occur before
any cursor advancement, so rejected tails/late events leave the caller's cursor
unchanged. This component assumes a caller already established a valid attach
baseline; it does not invent one or silently discard post-baseline events.

Tests cover zero/multiple events, repeated events from earlier intervals, gaps,
wrong context, old/ahead frames, ack/order/sequence errors, watermark mismatch,
noncompleted result, caller cursor changed, missing/wrong baseline, strict byte/
record/event limits, invalid UTF-8/JSON, failure/finished reuse and no advancement
on failed receipt. No NativeStepClient, Lua, policy, recording or runtime change.
Task 3.8 remains incomplete after this standalone assembly component passes.


## Frozen next coding slice: receipt socket reader (no command sender)

Add NativeStepClient.receive_receipt(command, baseline, cursor), returning a
NativeStepReceipt. Require a negotiated peer and a previous receive_active or
receipt in this connection. command/baseline must match that latest active
session/epoch/room/frame. The assembler still validates full baseline/cursor
binding. Require command.sequence == previous successful receipt sequence+1
(initial zero, reset on close_peer). No command is sent by this reader.

Use one monotonic config.message_timeout deadline for all _read_line calls,
including buffered lines; check before every read and immediately before final
cursor commit. To support that final check without mutating caller state on a
late receipt, add optional keyword-only before_commit: Callable[[], None] | None
in NativeReceiptAssembler.__init__. Store it and invoke only after ALL receipt
validation and watermark checks, immediately before shared cursor.take calls.
A raised callback error follows existing failed/clear-pending behavior. Recheck
captured cursor.last_id after the callback to catch external mutation. The
assembler itself still has no clock or sockets; default None preserves behavior.

The reader supplies a deadline guard as before_commit. Any infrastructure,
protocol, validation or deadline error closes the peer and raises EpisodeFault
with cause; interruption closes and propagates. After success, update _active
and inherited _frame to the receipt frame, keep snapshot sequence/update counters
unchanged, advance local successful receipt sequence, and return the receipt.
This lets later receive_active reject state older than the completed frame.
No paused/snapshot records are silently swallowed within a receipt transaction;
they are unexpected assembler records and fault. release/close/reconnect clear
receipt sequence alongside active state. start/reset/step remain unsupported.

Tests use simulated bounded socket peers: initial native snapshot then split/
coalesced ack/events/completion, sequential receipts, finite silent timeout,
slow trickle total deadline, foreign/order/barrier errors, disconnect mid-record,
stale snapshot after receipt, old receipt replay and same-listener reconnect.
Assert no post-hello command bytes on the peer. Test the precommit guard rejects
late receipts before cursor advancement, is not called on malformed receipts,
and detects callback-induced external cursor mutation. No fake game outcome,
attach-baseline support, sender, local authority gate, CLI, Lua or deployment.
Task 3.8 remains unfinished: these are receiver components only.

### Receipt kind enforcement (offline subtask 3.13, 2026-10-19)

Python-only hardening of the two components above; no Lua advertisement, event emission,
producer coverage claim, recording change or runtime eligibility. `NativeReceiptAssembler`
gains a keyword-only `oracle_kinds` (default `()`): a tuple or frozenset of exact `OracleKind`
names, otherwise `ProtocolError` at construction. After the context check, a
`native_oracle_event` whose wrapped `kind` is not in the set raises `ProtocolError` ("not
requested"), so the assembler fails and clears pending events before the existing `_finish`
validation or any cursor commit. The check covers replayed event IDs too: a deduplicated ID
never bypasses it. Ordering, identity, interval and watermark checks are unchanged, and an
event-free receipt is valid with an empty set.

`NativeStepClient.receive_receipt` passes exactly `config.native_oracle_kinds` (nothing when
`None`) from its own `ObserverConfig`. `receive_receipt` already requires a negotiated peer, and
`accept()` required every requested name, so the set is the successfully negotiated request.
Extra names in `HelloAck.capabilities` are never consulted and never widen it. A rejected event
takes the existing path: close the peer, raise `EpisodeFault`, leave cursor, `_active` and the
receipt sequence unchanged. An absent kind remains unknown, never a negative outcome.

Tests drive the production assembler and client: requested kinds accepted in wire order, every
kind accepted when requested and faulted when only another is requested, a peer that advertises
all seven kinds while one is requested, no requested kinds rejecting every kind, a valid prefix
not committed when a later event is rejected, and constructor validation. Not done and separate
follow-ups: persist the negotiated set with a native recording (recording wire/file format is
unchanged here; persisting the requested kinds is subtask 3.14 below), carry kind coverage on `NativeStepReceipt`, and the Lua export (3.6) and native
transaction multiplexing (3.8) work, both still open and runtime-ineligible.

### Native recording requested kinds (offline subtask 3.14, 2026-10-19)

Recording-format and Python-only change in `recording.py`; no Lua, bridge negotiation, receipt,
event semantics, reward/training or recording payload change. `RecordingManifest` gains an
optional `native_oracle_kinds`: an ordered, duplicate-free list of exact `OracleKind` names that
is valid only on a `native_oracle_events` manifest. It records the kinds requested when the
recording was created. It is not producer coverage, delivery, a transaction barrier or runtime
eligibility.

Three states, never conflated: an explicit nonempty list; an explicit `[]` (nothing was
requested, so every event record is invalid); and an absent field, which marks a legacy native
manifest and decodes as `None` (unknown). A legacy recording replays exactly as before and its
missing events are never read as negative outcomes. An explicit `null`, a non-list, an unknown
or non-string name, a repeated name, or the field on a `policy_frames` or `oracle_events`
manifest is malformed and `open_replay` raises `ProtocolError` before any record is read.

`JsonlRecorder` takes a keyword-only `native_oracle_kinds`. A `native_oracle_events` recording
requires a `tuple` (an empty tuple is valid), a non-native stream accepts no value (not even
`()`), and any other value raises `ProtocolError`. The manifest is built and validated before the
file is opened, so a rejected request leaves no file. `record()` rejects an event whose kind is
outside the set before writing it, so a writer cannot produce a file that replay refuses. Replay
checks each decoded event after the provenance check and before yielding it, so earlier in-set
events are already yielded when a later out-of-set event faults.

Compatibility: non-native manifests omit the field and stay byte-identical, and legacy native
manifests stay readable. No new manifest version is needed: `observation_schema_version` is not
repurposed and stays 1. An older reader rejects a new native manifest through `extra="forbid"`,
which fails closed. No native recording producer exists yet, so nothing wires a session's
requested kinds into a recorder; that belongs with the unfinished tasks 3.6 and 3.8.

Tests use the public writer and replay APIs with simulated envelopes: nonempty and empty sets,
event order preserved in the manifest, an event outside the set at write and replay (first and
later position), hand-written legacy manifests without the field, malformed/duplicate/unknown
replay metadata, rejected writer requests leaving no file, and unchanged non-native manifest
bytes. No game or Lua peer is involved.


## Frozen next coding slice: bounded opt-in callback trace

Before native input completion is implemented, add diagnostic instrumentation
inside existing observer callbacks. Config.callback_trace=false by default;
only literal true opts in. No wire/capability/action behavior changes. Source and
metadata become 0.4.1-dev; installed 0.4.0 is untouched. This source is not deployed
by the task. Old modes and all action/restart/authorization limits stay unchanged.

Trace begins once, at the first existing authorized action acceptance (not hello,
heartbeat or release); invalid or observation-only traffic cannot start it. Keep
fixed-size per-mod-load state: started/done/count/deadline. Trace is nonrenewable
by reconnect/reapproval, at most 512 log attempts TOTAL and at most 10000 ms from
first acceptance. No queue, retained history, polling file or new background loop.
Reserve the final record for stop at the count limit; count includes that stop.
Next callback at/after deadline emits at most one stop and suppresses further
trace. Disconnect/game exit ends it; normal hold expiry need not end the window.
Trace state survives close_peer/reconnect only as exhausted/done authority.

Use separate [Isaac Future Trace] lines, <=300 characters each. Include bounded
record ID, event label, Isaac time, Game frame, update counter, session, epoch,
room and action sequence when available. Input records additionally name hook,
button and the value returned by this observer; do not claim engine consumption.
Record existing action acceptance, render/update callback entry/exit, native input
exposure just before returning recognized player/cardinal hook values, hold
release reason, and existing start/room/level/game-end/exit/disconnect callbacks.
No entity details, hidden state, oracle events, save paths or private approval data.
Wrap trace operations so logger/diagnostic failures disable trace without changing
input returns, transport, cleanup or action authority. Avoid recursive close/log.

This is a diagnostic trace, not an outcome event, completion receipt or policy
input. It introduces no entity_action_v1 advertisement, sender or neutral command.
A bounded test-only build_lua(callback_trace=False) helper option may replace the
Config flag in source, preserving existing default behavior. No runtime config
file or user-facing CLI flag is added. Runtime activation/deployment remains a
later reviewed action while the game is closed and the current instance/slot is
confirmed. Task 4.1/4.2/4.3 acceptance remains not_run after offline trace tests.

Tests: default produces zero trace lines; opt-in without valid action never
starts; authorized acceptance produces correlated callback/frame/input-return
records; record count and line length never exceed limits; time limit stops;
reconnect cannot restart; logger failure preserves input/cleanup; trace records
never enter wire snapshots. Existing action and restart limits/old tests pass.


## Frozen next coding slice: passive Lua timing ledger (unshipped)

Evidence and corrected plan: reports/2026-10-17-native-timing-followup.md. Add
mod/experimental/native_step_ledger.lua, loaded standalone only by offline tests.
Do not import it into observer/main.lua or deploy it. It calls no engine, clock,
socket, logger or filesystem API. It records caller-supplied facts, grants no
input authority and produces no completed/applied status, wire message or outcome.

API: Ledger.new(sequence, accepted_frame, requested_frames); observe_query(frame,
update_counter, hook, button, value); observe_post_update(frame, update_counter);
close(reason, frame, update_counter); snapshot(). Use finite integer-valued Lua
numbers in 0..2**53-1 for counters, sequence >=1, repeat 1..15; booleans/strings/
fractional/nonfinite values fail. Reject a constructor whose end frame exceeds
the counter bound. Hook is exactly GET_ACTION_VALUE, IS_ACTION_PRESSED or
IS_ACTION_TRIGGERED; button integer 0..7. Value is finite number 0..1 for
GET_ACTION_VALUE and boolean for the other hooks. Invalid arguments error before
state changes. No global state shared between ledger instances.

Query window is [accepted_frame, accepted_frame+requested_frames), <=15 slots.
Each slot retains only fixed hook/button cells (3*8) with count, first/last update
and first/last returned value, plus frame identity. Duplicate queries increase
counts, never an applied-update count. No per-query history or dynamic key space.
Out-of-window queries or queries after close increment fixed dropped counters
and return false. Valid in-window queries return true. Caller facts do not prove
consumption or full action application.

Post-update window includes the endpoint [accepted_frame, accepted+requested],
<=16 slots, each with count, first/last update and after-release count. Endpoint
post-update may be recorded AFTER close to represent expiry-before-post-update;
close is release recording, not sealing the bounded observation window. Out-of-
window updates increment a fixed dropped counter and return false. No growing
post-update list. close requires nonblank control-character-free reason <=64
bytes and bounded frame/update, retains the first supplied release cause/context
and returns true once, false thereafter. Do not infer wall/frame expiry from an
ambiguous reason. Recording never extends any runtime guard.

Cap valid query/post-update observation calls at 4096 total (including dropped
observations); the 4097th errors without mutation. This bounds scalar counts and
work per ledger. close and snapshots do not renew that budget. snapshot returns
a detached deep copy with facts/limits/windows/counts/release only; the caller may
mutate it without changing internal state. No immutable-table claim is made.

Tests use isolated lupa.lua53 and this module alone, without game globals. Model
the measured repeated-query ordering with synthetic numbers; distinguish query
counts from post-update observations. Cover invalid inputs/no mutation, 1/15
windows and endpoint, duplicate/neutral values, close-before-post-update, repeated
close, dropped frames, independent instances, 4096 boundary and detached copies.
Production integration, step classification, event baseline and real acceptance
are explicitly not part of this slice. Do not mark task 3.6/3.8 complete.

## Offline producer event outbox

NativeEventOutbox is a Python reference component, not an engine emitter or a
sender. Bind it to an explicit game_api EntityFrame baseline. Capture every later
event, including neutral time before command acceptance. Assign contiguous IDs
from one. Require the same session/epoch/room and nondecreasing event frames.
Never infer events or establish an engine baseline from this component alone.

Keep at most 32 pending events and 32768 encoded bytes, including events in an
unacknowledged batch and future events. Lower limits are allowed. Records retain
the 16384-byte bound; the remaining 32768 bytes reserve two bounded ack/completion
records within the existing 65536-byte receipt limit. No queue eviction.

seal(end_frame) stages one immutable interval (committed_frame, end_frame] and
its watermark, without removing events. Future-frame events remain queued; an
empty interval uses the previous committed watermark. Only acknowledge of that
exact staged object commits delivery and removes its prefix. The future sender
must call it after flushing completion, and close on any send failure.

An event at/before a sealed boundary, regressing frame, foreign identity, invalid
operation, or overflow permanently faults and clears the outbox. Reconnect needs
a new explicit baseline; close is idempotent. No clock/socket/action authority.
Sealing is a caller assertion, not proof all engine callbacks have finished.
Engine callback ordering and attach synchronization remain prerequisites for
production use. This component alone does not complete task 3.8.

## Passive oracle probe (negotiated diagnostic)

Use optional oracle_probe_v1 in the existing hello required_capabilities list,
independently of callback_trace. Start once after an explicitly requested valid
read-only hello; action/restart/native-step combinations are rejected. At most
120000 ms, 1024 log attempts (last reserved for stop), 400 bytes per line and 128
local entity labels per mod load. Disconnect/exit/unload ends it; reconnect never
renews it. Source version becomes 0.4.3-dev, installed once while closed. Remove
the old oracle_probe source flag and private patched-build procedure. Protocol
version and message shapes stay unchanged; this adds a capability, not outcome
records or action approval. Existing 0.4.2-dev evidence remains historical.

Advertise oracle_probe_v1 only when identifiers/reads exist and the mod-load
window has not started or ended. Old or exhausted peers fail explicit negotiation;
never silently fall back. Default attach does not consume the window and may
reconnect normally. Entity observation may combine with diagnostics. Diagnostic
callbacks are registered when supported but remain inert until requested.

Add strict ObserverConfig.oracle_probe=False and CLI observe --oracle-probe.
For this CLI mode require zero reconnects, message/handshake timeouts <=3 s and
accept timeout <=60 s; close after <=600 samples or 120 s from successful attach.
One bounded receive may finish at most 3 s after that deadline. Other CLI modes
are unchanged. No game launch, mode toggling on an existing connection, runtime
config files or poller is added. A normal source-matching installation always
passes launcher hash checks, whether diagnostics were requested or not.

Log raw damage_attempt amount/flags/countdown and current HP, NPC init/update HP,
entity kill/remove, NPC death, clean_award, game-end boolean, room/level/start,
and post-update player health/dead/paused/room-clear facts. Damage targets get one
pending NPC-update sample per label; repeated hits may coalesce, so no per-hit
attribution. Player sampling is at most every 200 ms plus the next update after
a callback. Entity labels are diagnostic only, never spawn generations or reward
IDs. Pointer hashes remain internal and room-local; do not log them or seeds.
NPC init may relabel a morph; label exhaustion ends the probe without eviction.

All diagnostic reads/logging are protected; a failure disables the probe without
closing observation or changing any callback return. Damage and clean-award
callbacks always return nil. Do not mutate entities or callback arguments. Do not
infer healing, applied damage, terminal transitions or clear from these logs.
Missing callback identifiers disable the diagnostic without breaking the observer.
Default attach performs no diagnostic reads or logs. Existing lifecycle callbacks record facts
without changing their control flow. Keep task 3.6/3.8 and runtime tasks open.

Terminal/short-step decision: retain the existing fail-closed receipt contract.
A death candidate, transition, or partial/zero elapsed step cannot become an
accepted policy transition without a separately specified terminal envelope and
verified event barrier. Do not weaken completed-step validation in this slice.

### Measured combat ordering, 2026-10-18

reports/2026-10-18-oracle-combat-runtime.md records a concrete attempt -> later
NPC-update with unchanged HP -> kill with negative HP sequence. The existing
diagnostic NPC-update sample is NOT an applied-damage barrier. Do not connect it
to enemy_damaged or treat a raw delta as attributed damage. All 33 matched local
kill groups had kill -> remove -> NPC-death order in that bounded window; this is
measured scope only, not a universal ordering guarantee. Seven award candidates
were followed by clear=true; death/revival/floor semantics remain unverified.
Specify and probe bounded end-of-update observations before choosing realization,
clamping and concurrent-effect semantics. No sender or event export is enabled.

## End-of-update HP diagnostic slice

Observer 0.4.4-dev extends the same explicitly negotiated probe; no new mode,
capability, timer or authority. Damage/init callbacks stage at most 16 target
entries until the next observer MC_POST_UPDATE callback. Each entry keeps a local
label/key, entity reference, first queued frame/update, coalesced attempt count
and init marker. Same-label callbacks coalesce without postponing the sample.
The 17th distinct pending label stops the diagnostic with reason=pending; no
eviction. All existing 120 s / 1024 records / 128 labels / 400-byte limits stand.

After the callback's update counter advances, flush the bounded entries once,
before periodic player sampling. Emit post_update_hp with queued context, counts
and status=sampled plus current raw HP, or status=removed/missing/identity_changed
without HP. Removed targets drop their reference immediately and keep only a
scalar tombstone. Check Exists() and the current diagnostic label/key before HP
reads. Negative raw HP remains diagnostic data, never a clamped outcome.

Flush detaches and clears the batch before reading/logging. Reentrant diagnostics
invalidate the window before further deferred reads; no completion is claimed. Stop/fault,
disconnect/exit/unload, game start/end and room/floor transitions discard pending
references. The older NPC-update sample uses its separate scalar pending marker
and cannot consume the new post-update sample. No game object is mutated.

This is an observation at this observer's MC_POST_UPDATE position, NOT proof all
engine/other-mod effects have finished or a valid completion/event barrier. No
per-hit amount/source, healing, kill/terminal inference or OracleEvent is emitted.
Offline tests replay a fabricated old-HP NPC-update followed by changed HP at
post-update, coalescing/cancellation, removed/missing/relabelled targets, bounds,
reentrancy, faults and all cleanup paths. The 0.4.4-dev manual-combat run verified
explicit activation and 106 raw deferred samples. A first post-update sample
still showed old HP in the attempt's game frame before a later kill showed
changed HP; see reports/2026-10-18-post-update-hp-runtime.md. This disproves using
the first observer post-update as a damage barrier. Later-frame settlement and
unavailable/transition semantics need a separate bounded design before event
integration; simply delaying a sample must not imply realized damage attribution.

## Later-frame HP diagnostic slice (offline subtask 4.4; reviewed, runtime pending)

Evidence: the 0.4.4-dev run showed first post-update samples equal to the attempt
HP in all 103 paired cases while 20 later kill records showed changed HP (room 13
label 1: records 7 and 8 both 0.53247833251953, later kill -3.3610258102417). The
slice below only samples raw HP at later distinct game frames to investigate timing.
It claims no applied damage, settlement, reward, completion or barrier. Source
becomes 0.4.5-dev; the installed 0.4.4-dev copy is untouched and not redeployed, so
installed and source hashes are expected to differ until a separate authorized install.

Subsequent closed-game deployment installed the reviewed source with matching
hashes and passed launcher preflight; see reports/2026-10-18-later-frame-hp-deployment.md.
The following design is unchanged. Subsequent bounded raw-sampling acceptance
passed in manual combat (593 snapshots; 99 first/197 later records; 87 changed
windows; 16 removed facts without HP). One room/floor callback slice was captured;
death/revival and native step/event barriers remain unverified. See
reports/2026-10-18-later-frame-hp-runtime.md. A fixed later-sample count still
cannot imply universal settled damage or source attribution.

### Entry lifecycle and exact bounds

The existing staging list is the only list and holds at most 16 entries TOTAL across
first and later stages; there is no detached or second list, so entries still being
processed always count. Each entry keeps its original label, key, reference, queued
frame/update, coalesced attempt count, init marker, a sample count (0..3), the game
frame of its last sample and an age. Age counts observer MC_POST_UPDATE callbacks
since staging, including callbacks that do not sample. Same-label damage/init
callbacks coalesce into the existing entry (attempt count and init may grow) and
never reset context, sample count or expiry. A seventeenth distinct entry stops
diagnostics with reason=pending; nothing is evicted. A finished entry leaves the
list, so a later attempt on the same label stages a fresh entry and window.

Per observer post-update callback, in this exact order for each entry:

1. age = age + 1; the game frame is read once for the callback.
2. Opportunity: sample 1 happens at the first callback and MAY share the attempt
   frame. Sample 2 or 3 happens only when the game frame is strictly greater than
   the frame of the previous sample. A callback in an unchanged frame reads nothing.
   A removed entry emits its scalar removed fact at its next callback regardless of
   frame (no read occurs). Observer update counters are never damage barriers.
3. An unavailable result (removed, missing, identity_changed) finishes the entry
   at once; HP is never fabricated. The third sample finishes the entry.
4. Expiry: an unfinished entry with age >= 4 emits one expiry fact and finishes.
   Opportunity precedes expiry, so a fourth callback may still take a sample, and
   a finished entry never emits expiry. At most 3 samples and 4 callbacks bound the
   lifetime, so unchanged frames can exhaust the window without any later sample.

Finishing, removal, expiry, transitions, stop and faults drop the entity reference
and key immediately; removal keeps only scalar context. Stop/fault, disconnect,
exit/unload, game start/end and room/floor transitions clear every entry and no
output crosses contexts. Reentrant or faulting Exists/pointer/frame/HP/logger
paths keep the fail-closed invalidation: no read or retention after invalidation,
and ordinary observation continues. The flush-frame getter is protected by the
same reentry guard as per-entry facts; reentrant room/diagnostic callbacks
invalidate the window before any old target is emitted in the new context.

### Records

The first record is unchanged: `post_update_hp`. New records share the same line
prefix, 120000 ms / 1024 attempts (including the final stop) / 128 labels budget,
400-byte limit and no renewal on reconnect:

- `post_update_hp_later`: label, queued_frame, queued_update, attempts, init,
  sample (2 or 3), prior_frame, then status=sampled with entity_type/variant/hp, or
  status=removed/missing/identity_changed with no HP.
- `post_update_hp_expired`: label, queued_frame, queued_update, attempts, init,
  samples (1 or 2), callbacks=4, status=expired.

HP values stay raw: unchanged, increased and negative values are facts; there is no
per-hit amount/source, healing or terminal inference, no OracleEvent, wire field,
reward, completion receipt or input authority. Default observation, explicit
oracle_probe_v1 negotiation, the independent NPC-update marker and every control
and reset restriction are unchanged. If the global budget is exhausted before an
expiry fact fits, the standard stop record is emitted and no fact is fabricated.

### Offline evidence required

Production-Lua tests replay old first-post HP followed by a changed value in a later
frame, same-frame callbacks, three-opportunity cap, four-callback expiry with
unchanged frames, coalescing without renewal, a fresh window after completion,
independent NPC-update sampling, healing/unchanged/negative HP, removal between
samples, Exists=false, identity change, combined 16-entry capacity and 17th-target
stop, shared budgets, line bound, reconnect without renewal, weak-reference release
on every finish path, reentry and faults at each read and logger, and absence of
entity/input mutation or callback-return interference. All game checks are not_run.

## Native step lifecycle reducer (offline subtask 3.9; unwired, unrun)

A pure reducer, `native_step_lifecycle.py`, decides whether the supplied facts about
ONE native step are logically consistent. It is not a sender, GameBackend, engine
adapter, timing ledger or wire receipt, and it is not imported by production code.
A READY decision is a LOCAL candidate: it is not a delivered transaction (the outbox
acknowledgement is a separate producer-side fact), not a StepCompletion, and not proof
that input was physically executed or that damage settled.

### Inputs

`NativeStepLifecycle(command, baseline_last_event_id, started_ms, deadline_ms)`
copies scalars from a validated StepCommand (no reference is kept). Integer
millisecond timestamps are caller-supplied and monotonic; `deadline_ms` must satisfy
`started_ms < deadline_ms <= started_ms + 250` and is never renewed. The reducer
reads no clock. One command per instance, no queue. `submit(fact)` consumes one
frozen fact and returns an immutable `StepDecision` snapshot. At most 64 submissions
are accepted as completion evidence (duplicates included); the 65th faults a
WAITING step. The internal counter saturates at 65. Further calls can only validate
constant-size cleanup/time facts or invalidate a provisional READY candidate,
never renew evidence capacity. Cleanup remains possible after overflow. Facts carry
bounded integer scalars only (strict `int`, 0..2**53-1, no bool).

Fact types (all carry `at_ms`):

- `AcceptanceFact`: ack identity and frame (from a CommandAck of kind action).
- `IntervalFact`: identity, accepted_frame, requested_updates, elapsed_updates,
  end_frame. A hypothetical adapter assertion of exact consumed updates; the reducer
  validates scalar consistency, not the assertion's provenance.
- `ReleaseFact`: identity and frame at which this bridge's held input override was
  cleared. It does not establish physical neutrality, final input seen by the engine,
  or absence of user/other-mod input. The reducer validates ordering only.
- `SealFact`: session/epoch/room, end_frame and last_event_id. An explicit statement
  that the event stream is complete through end_frame in this same context. This is
  also a caller-supplied assertion; the reducer does not establish callback quiescence.
- `InterruptFact`: identity, frame and one kind: pause, explicit_release, input_fault,
  death_candidate, disconnect, transport_fault, authority_lost.
- `ContextChangeFact`: the NEW session/epoch/room, frame and kind: room_change,
  floor_change, epoch_change, session_change. The new frame is never attached to the
  old command.
- `ClockFact`: time only. Elapsed time alone never produces readiness, only expiry.

### States and decisions

States: `waiting`, `ready`, `cancelled`, `expired`, `faulted`, `unsupported_terminal`.
Every non-waiting state is absorbing. A decision carries state, reason, `fresh` (true
only on the submission that caused the transition), `missing` (WAITING prerequisites),
`release_required`, a candidate (READY only), local identity scalars and
`conflict_after_ready`. `release_required` is true from construction until a valid
ReleaseFact; cancellation, expiry, fault and terminal outcomes keep it visible. A late
valid ReleaseFact clears only that flag and never changes the outcome. Bridge-control-
clear confirmation must cover the latest accepted/interval/interruption frame and
follow all observed timestamps, including terminal clocks. Later progress or a new
context invalidates old confirmation; frame counters from new sessions/epochs are not
compared to old frames. The flag records only that this bridge no longer holds its
override; it says nothing about physical neutralization or other input sources.

### Readiness and candidate

READY needs all four prerequisites at once, in any arrival order: matching
acceptance (frame inside command.frame_id..+15), a caller-supplied exact full interval
(`end - accepted == elapsed == requested == command.frames`), bridge-control-clear at a
frame >= end_frame, and a caller-supplied seal in the same session/epoch/room whose
end_frame equals the interval end and whose last_event_id >= the baseline watermark.
The reducer checks consistency, not provenance or engine behavior. Input-query counts,
callback returns, hold/post-update observations, snapshots, HP samples, requested
repeats and elapsed wall time are not facts and cannot substitute. The immutable
candidate holds identity, accepted_frame, end_frame, requested/elapsed updates and
last_event_id with provenance `local_reducer_unverified`; it satisfies the existing
full-interval invariants and rounds, clamps or completes nothing partially. It is not
live completion until a producer's exact consumed-update, bridge-control-clear and
event-seal evidence has been independently verified for the target game build.

### Precedence (first matching row wins, evaluated per submission)

1. Already non-waiting: state is kept; only a matching monotonic ReleaseFact
   covering observed progress clears `release_required`, even after overflow.
   After READY, contradictions, malformed/regressing facts, budget exhaustion or
   any interruption/context change set sticky `conflict_after_ready` and withhold
   candidates from future decisions, regardless of endpoint frame. Old immutable
   snapshots cannot be recalled; a future sender needs its own delivery/commit
   guard and must not treat a retained earlier candidate as final authority.
2. Counted submission 65: fault `overflow`.
3. Not a known fact type or non-monotonic `at_ms`: fault `malformed_fact` /
   `timestamp_regression`.
4. `at_ms >= deadline_ms`: expired `wall_deadline` (deadline wins every tie, including
   a completing fact at the same timestamp); the late fact is not applied except as
   a valid release.
5. Identical duplicate of an accepted fact: ignored, still counted.
6. Foreign session/epoch/room/sequence: fault `foreign_context`; frame below
   command.frame_id or accepted_frame: fault `stale_fact`; differing repeat of a
   one-shot fact, release before the interval end or seal/interval/ack mismatch:
   fault `contradictory_fact`; short, long or zero interval: fault `partial_interval`;
   watermark below baseline: fault `watermark_regression`.
7. Interrupts: pause, input_fault, explicit_release and room/floor change cancel
   (reasons pause, input_fault, explicit_release, transition); death_candidate and
   epoch_change are `unsupported_terminal`; authority_lost expires; disconnect and
   transport_fault, session_change fault. HP, disconnects and absent facts never
   imply death. Any interrupt while WAITING terminates, regardless of its frame.
8. Otherwise the fact is stored; if all prerequisites agree the step becomes READY.

### Mapping and engine-evidence gaps

Cancellation reasons reuse the wire reasons pause, input_fault, explicit_release and
transition; `wall_deadline` maps to expired. The reducer adds local-only reasons and
creates no wire message. Existing receipt, reader and client validation still reject
partial/terminal steps; NativeStepClient.step/start/reset stay unsupported.

The real adapter currently provides NONE of: a per-update counter establishing the
exact consumed updates for a command interval (input queries repeat around
post-update); transaction wiring from the existing bridge-clear observation to a
reducer `ReleaseFact`; a sealed endpoint with a complete watermark (the outbox has
no engine emitter); or ordering facts for pause/death/transition. Existing
`action_accepted`, `hold_update`, `release`, `release_update` and `release_input`
trace records are bridge observations only: they do not prove consumed updates,
neutral final game input, or event-stream quiescence. Runtime work must supply
independently verified evidence before any non-synthetic READY exists.

### Offline evidence required

Behavioral tests with fabricated facts: acceptance alone, independent-fact
reordering, query/HP substitution, repeat 1 and 15, interval and frame defects,
identity and scalar bounds, every interrupt before/at/after the endpoint, release
semantics after each terminal state, watermark/seal faults, ties, replay and duplicate
handling, absorbing outcomes, the 64/65 limit and detached immutable output, plus
unchanged receipt/client suites. All game checks are not_run.


## Bounded Lua step-evidence hooks (subtask 3.10)

Producer-side diagnostics only, inside the existing default-false `callback_trace` window
(10 s, 512 attempts including the reserved stop, 300 bytes per line, one window per mod
load). No new mode, wire field, capability or reducer input. Engine consumption of a held
input stays UNKNOWN; the records are raw bridge-side facts for a future probe.

### Records (all scalar; none emitted when the trace is off or finished)

- `action_accepted` (after canonical validation and hold assignment) adds `until` (hold end
  frame) and `deadline_ms` (wall deadline) to the existing move/shoot/frames, session,
  epoch, room, seq, frame and update fields. Acceptance is not wire-ack delivery.
- `hold_update`: from MC_POST_UPDATE after `action_guard`, at most once per game frame
  while the accepted hold is live: `hold_seq`, `left` (frames to `until`), `upd_since`
  (bridge update counter since acceptance). Repeated callbacks in a frame add nothing.
- `release` (existing record) adds `hold_seq` (identity from the cleared hold itself, not
  `actions.sequence`, which heartbeats move), `frame_due`/`wall_due` (observed expiry
  conditions at clearing time; both 1 means unattributable) and `left`. The reason is
  capped at 40 characters.
- One pending release observation (seq, session, epoch, room, update counter, two flags).
  The next post-update yields `release_update` (`hold=absent`); the next player movement or
  shoot input query that the bridge answers with nil yields `release_input`
  (`override=nil`). Nil override is not a neutral engine input: manual input and other mods
  still apply. Each fires at most once; both done clears it. An accepted action, any
  context change, game start/end, level, room, disconnect, exit, unload, stop or fault
  discards it. A new input never confirms an old release.
- A line over 300 bytes stops the trace with `reason=line_limit` instead of truncating
  identity fields. A failing read, logger or re-entered hook stops and clears diagnostics
  only; command validation, acks, input returns, release and watchdog are unchanged.

### Non-claims

Bridge-side clearing is not physical neutrality, post-update coverage is not a consumed
update, and no READY/seal/watermark exists. Source/metadata move to 0.4.6-dev; the installed
0.4.5-dev stays untouched and live acceptance needs a reviewed closed-game deploy and a
separate preflight. A future short probe (one action, release, cleanup) must not force
death, reset or restart to fit the trace budget.

## Terminal outcome coverage (offline subtask 3.15, 2026-10-19)

Finding F1 of `reports/2026-10-19-oracle-event-contract-review.md`: an absent
`player_died`/`room_cleared` event was treated as evidence for `timeout`, and the summary
defaulted both facts to false. Without delivery coverage that is a false negative.

### Contract

- `StepResult.terminal_coverage` is a `frozenset` of the terminal kinds `player_died` and
  `room_cleared` that the backend delivered exhaustively for that result's exact interval
  (previous frame, frame]. It is an explicit claim: never derived from requested or recorded
  kinds, provenance, or an empty `events` tuple. The default is empty (unknown for both kinds);
  anything outside the two kinds, or a non-`frozenset`, is a `ValueError` (an episode fault when
  raised from a backend call). `SyntheticRoomBackend` generates every event itself and declares
  both kinds on every result.
- The controller keeps two per-episode sets, reset by `start()`: `complete` (starts with both
  kinds; each accepted result, including the initial one, intersects it with its coverage) and
  `observed` (terminal kinds seen in any accepted result, including the initial one). A later
  complete interval therefore never repairs an earlier gap.

### Resolution (first matching row wins, per step)

The initial result must establish a playable episode baseline. If it contains a terminal
event, `start()` raises `EpisodeFault` through the existing release/fault path before any
action can be sent. Gymnasium reset cannot convey a terminal transition; silently ignoring
the initial event would permit an action after an already observed death or clear. The
following table applies only after a successful start.

| Condition | Outcome | Transition |
| --- | --- | --- |
| `player_died` in this interval | `death` | terminated |
| `room_cleared` in this interval and `player_died` in `complete` | `cleared` | terminated |
| `room_cleared` in this interval and death coverage incomplete | `unknown` | truncated |
| limit reached, both kinds in `complete`, `observed` empty | `timeout` | truncated |
| limit reached otherwise | `unknown` | truncated |
| none of the above | none, episode continues | neither |

A clear is never resolved as `cleared` while an unreported death could precede or accompany it,
so the unresolved clear maps to the explicit `unknown` outcome: truncated, not terminated,
control released, episode stopped. `unknown` is not a death, clear or timeout and carries no
reward of its own; rewards still come from the events actually delivered. Death needs no
coverage because a delivered death is positive evidence.

### Summary facts

`died` and `room_cleared` are `bool | None`. A kind observed in any result is `True`. A kind in
`complete` that was never observed is `False`. Otherwise it is `None`. Facts follow events, so a
same-interval death and clear gives `outcome == "death"` with both facts `True`; only the outcome
applies death-over-clear precedence. They are refreshed on every transition, so a running
episode reports `False` only for a kind covered so far.

### Consumers (reviewed; continuation 2026-10-19 after coordinator feedback 1)

`IsaacCombatEnv` forwards `outcome`, `terminated` and `truncated` and emits `info["episode"]`
for any non-null outcome, so `unknown` reaches Gymnasium consumers as a truncation.
`LiveBackend` is intentionally left without a coverage claim: its `EventDeriver` facts are
frame-delta-derived approximations, not an exhaustive event-delivery guarantee. Its derived
clears and 1800-update limits therefore resolve as `unknown` (truncated, released) while a
positive `player_died` stays `death`. Live-facing tests expect `unknown`, never `cleared`.
Rewards still come from the events actually delivered, so a derived clear event is rewarded as
before even though the episode label is `unknown`. The reward and training/checkpoint
implementations are not edited here; because the new outcome is truncated, the existing training
path bootstraps its final value.

`evaluation` carries `unknown` explicitly: `EpisodeRecord.outcome` allows it and `Metrics` has an
`unknown` count next to `faults`. Unknown never enters the death/clear/timeout totals. `valid`
is the known-outcome count (`cleared + deaths + timeouts`), so `clear_rate`, the Wilson interval
and curriculum/spectator sample-size reads use one consistent population, while the damage and
return means still cover every non-fault episode. Unknown episodes do not satisfy existing
minimum-valid sample gates and can delay advancement or regression decisions when coverage is
incomplete; threshold constants and gate implementations are unchanged.
`attempted == valid + unknown + faults`.
`REPORT_VERSION` is 2 for this shape. The combat gate tallies `unknown` under its own key.
`benchmark` passes outcomes through; its synthetic backend declares complete coverage, so
`unknown` cannot occur there today, and an uncovered backend would count `unknown` in its
`episodes` denominator (follow-up outside this subtask).

### Non-claims

No native producer, Lua export, `OracleEvent` delivery guarantee or runtime eligibility exists or
is implied. Task 3.15 is offline only; tasks 3.6 and 3.8 stay open.
