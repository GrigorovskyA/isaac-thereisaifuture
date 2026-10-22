# Native episode protocol groundwork

Status: offline Python components for the active episode-lifecycle change.
This document does not advertise installed-game support. Observer 0.4.0 does not
advertise entity_action_v1; negotiation with that installed version must fail.
Default observation, entity-only observation, legacy actions and bounded natural-
death restart retain their accepted protocols and mutually exclusive modes.

## Negotiation

ObserverConfig.native_episode_steps is an explicit boolean, default false, appended
to preserve positional compatibility. It cannot combine with safe_actions,
entity_observations or restart_after_death. Its hello requires the three base
capabilities plus entity_action_v1 only. There is no downgrade to an older mode.
The base ObservationClient decodes EntitySnapshot in this mode, validating nested
identity and provenance. Unsolicited oracle events, acknowledgements and completion
messages are rejected by this base snapshot path. A dedicated bounded native
transaction client is still required before combined actions can be sent.

There is no CLI switch, deployment or implicit action approval in this groundwork.
See OBSERVATION_PROTOCOL.md, ENTITY_OBSERVATION_PROTOCOL.md and SAFE_ACTIONS.md for
the existing framing, validation and runtime authority rules.

## Step command and receipt

The offline StepCommand has type step_command, protocol_version 1, session_id,
sequence, game_epoch, room_visit, frame_id, kind action, move, shoot and frames.
Directions are none/left/right/up/down; frames is a strict integer in 1..15.
Serialization uses the existing canonical field order and newline framing. It is
a distinct message type so an old peer cannot silently accept it as legacy input.

CommandAck records acceptance only. StepCompletion has type step_completion,
protocol_version 1, session_id, sequence, game_epoch, room_visit, accepted_frame,
requested_updates, elapsed_updates, status, reason, a policy-visible EntityFrame
and required last_event_id (strict bounded counter, no default).
Nested identity/provenance must agree. elapsed_updates equals frame.frame_id minus
accepted_frame. Completed requires interval_elapsed and elapsed exactly equal to
requested. Expired requires wall_deadline; cancelled requires pause, transition,
input_fault or explicit_release. A later arbitrary frame cannot prove completion.

validate_completion checks command/ack/result identities, request repeat, acceptance
frame agreement and the 15-frame acceptance freshness bound. These are receipt
consistency checks, not proof of physical movement, shooting or callback ordering.
validate_event_barrier(result, cursor.last_id) additionally requires exact equality
to the required last_event_id, rejecting missing tails, cursor-ahead values and
invalid observed counters. The helper does not bind a cursor to a session; future
transaction code must perform that binding and interval consumption first.
Native application and exact interval timing still need implementation and probes.

## Oracle stream

NativeOracleEvent has type native_oracle_event, protocol_version 1, session_id,
game_epoch, room_visit, frame_id, positive event_id and a separate OracleEvent.
The event body must have game_api provenance and matching identity. No oracle
labels are added to EntityFrame, policy input or policy recordings.

NativeEventCursor is fixed to one session/epoch and retains one last contiguous
ID. For take(envelope, start_frame, end_frame), bounds must always be strict
bounded integers with start_frame < end_frame, even for duplicates. After context
validation, IDs already consumed return None; their old frame can be outside the
new interval. A new ID must be last_id+1 and its frame in (start_frame,end_frame].
Faults leave cursor state unchanged. Reconnect requires a new cursor and never
renews game authority. This cursor does not infer outcomes or manufacture events.

The explicit native_oracle_events recording stream preserves the full envelope,
including event_id. Existing oracle_events and policy_frames streams remain
separate. Mixed, malformed, incompatible or synthetic native records fail closed.
Wire records are bounded at 32768 bytes (32 KiB since observation schema 4; the per-record 16384 limits below belong to archived components); recording lines retain their separate
65536-byte bound. No unbounded queue is introduced by these models.

A new native_oracle_events recording must be created with an explicit tuple of the requested
OracleEvent kinds, and its manifest persists them as an ordered duplicate-free native_oracle_kinds
list. An empty tuple persists as [] and means nothing was requested, so any event record is
rejected. The writer rejects an event outside the list before writing, and open_replay rejects
one before yielding it; this is integrity validation, not proof that the producer covered or
delivered every requested kind, and a requested kind with no event is unknown, not a negative
outcome. A legacy native manifest without the field decodes as native_oracle_kinds None
(unknown, not empty) and replays unchanged. An explicit null, unknown, non-string or repeated
name, or the field on a policy_frames or oracle_events manifest, is rejected when the file is
opened (writer: ProtocolError before any file is created). Those two streams keep their
manifest bytes, and observation_schema_version is unchanged. Only the requested set is stored:
no receipt, event semantics, payload, Lua or bridge negotiation change, and tasks 3.6 and 3.8
stay open and runtime-ineligible.

## Pending acceptance and limits

NativeStepClient now provides bounded receive_active snapshot waiting with one
absolute deadline, paused/unavailable filtering and strict active freshness and
epoch/room checks. Failures close the peer and raise EpisodeFault. release closes
idempotently; unsupported start_episode/reset/step close and explicitly fault
without writing commands. Reconnect resets connection state, never authority.

NativeReceiptAssembler now validates one delimiter-free record at a time:
matching ack, zero or more events, then a completed receipt. Baseline and cursor
session/epoch/room are checked. All events and the watermark validate before the
shared cursor advances. Faults invalidate the assembler and clear pending data.
Limits are 32 event records including duplicates, 34 total records and 65536 total
encoded bytes; each record remains <=16384 bytes. Limits are checked before JSON
parsing. LF/CRLF/CR records are rejected. This component has no clock or socket;
its caller must enforce the total deadline and a valid event attach baseline.

NativeStepClient.receive_receipt now reads ack/events/completion with one absolute
message_timeout, including fragmented or coalesced records, and never sends a
command. It requires the latest connection-bound active/receipt baseline and next
successful receipt sequence. A caller-owned before_commit guard checks the deadline
after all validation and before cursor updates. Failure closes the peer; successful
receipt frames advance active freshness without changing snapshot counters.

The command sender, event attach/delivery baseline, Lua input completion and
outcome emission remain unfinished. start_episode/reset/step stay unsupported. Do not substitute
periodic snapshots for exact step completion, infer death from zero health or
transport loss, or infer clear from an empty entity list.

General episode start/reset and the real GameBackend remain gated by verified
training isolation and explicit authority. File 2 and the ordinary-profile bounded
action-test exception are not training isolation. Manual launch/save selection,
500 ms heartbeat, at most 15 frames/250 ms per hold, the nonrenewable 120-second
per-mod-load action lease and three restarts per ten minutes remain unchanged.
One hundred real consecutive episodes remain required before item-05 archival.

Evidence: reports/2026-10-17-native-step-models.md,
reports/2026-10-17-native-events.md and
reports/2026-10-17-native-negotiation.md, reports/2026-10-17-native-wait.md
reports/2026-10-17-native-watermark.md, reports/2026-10-17-native-receipts.md
and reports/2026-10-17-native-receipt-reader.md.
Simulated peers establish only offline
behavior; see docs/STATUS.md for the latest accepted Windows gate results.


## Experimental observation ledger

mod/experimental/native_step_ledger.lua is an offline-only facts component, not
imported or installed by the observer. It records caller-supplied query exposure
in at most 15 frame slots and post-update observations in at most 16 slots,
including the endpoint after release. Fixed hook/button cells retain counts and
first/last values; 4096 valid observation calls, including drops, is the limit.
Invalid inputs and extra calls fail before mutation. Snapshots are detached copies.
It calls no engine API and creates no input authority, wire receipts or outcome.
See reports/2026-10-17-lua-evidence-ledger.md. Observed exposure remains separate
from engine consumption; exact step application and native event APIs are pending.

## Offline producer delivery reference

NativeEventOutbox binds to an explicit game_api frame and captures subsequent
events, including neutral time before the first command. It assigns contiguous
IDs and retains at most 32 pending records / 32768 encoded bytes; no eviction.
Each record stays within 16384 bytes. Two additional bounded records fit the
existing 65536-byte ack/events/completion receipt budget.

seal(end_frame) stages (committed_frame, end_frame] and its last_event_id; future
events remain pending and an empty interval retains the committed watermark.
acknowledge requires the exact staged batch object and removes only its prefix.
A future sender must acknowledge after flushing completion and close on failure.
Late/regressing/foreign events, overflow and invalid operations permanently close
and clear the outbox. Reconnect requires a new explicit baseline.

This is a Python reference with no sender, engine integration or input authority.
Sealing asserts completeness supplied by the caller; it cannot prove callback
quiescence. It does not complete attach synchronization or task 3.8. See
reports/2026-10-17-native-oracle-api-audit.md for unresolved outcome semantics.

## Passive oracle callback diagnostic

Observer 0.4.3-dev activates diagnostics only when the existing hello explicitly
requests oracle_probe_v1. Ordinary attach does not consume the window. The same
installed/source files serve both modes; no diagnostic flag is patched. One
read-only diagnostic attach may log raw callback facts for at most 120 seconds, 1024
attempts and 128 local labels per mod load; it cannot renew on reconnect. Damage
and award callbacks return nil; diagnostic failure never closes observation.
Exhausted or unsupported requests fail without fallback; action/restart/native-
step combinations are rejected. Oracle facts remain outside the wire and no
combined action capability is enabled. Python observe --oracle-probe caps the
read loop to 600 samples/120 seconds with zero reconnects and <=3-second reads.
See ORACLE_PROBE.md for one-time installation, manual launch, privacy and stop.
It does not enable terminal receipts:
partial steps and transition/death candidates still fault in the current reader.

## Local step lifecycle decision (offline, unwired)

`native_step_lifecycle.py` is a pure reducer, not a transport component. For one
StepCommand it combines four independent facts: matching acceptance, an exact full
interval (`end - accepted == elapsed == requested`), bridge-control-clear at a
frame >= the endpoint, and a sealed same-context endpoint with a complete event
watermark. These are caller-supplied assertions: the reducer validates their scalar
consistency and ordering but does not establish their provenance or engine truth.
Only then does it return a local READY candidate. That candidate is not a
StepCompletion, not a delivered transaction (outbox delivery acknowledgement is a
separate producer fact) and not proof of physical input. Pause, transition, death
candidates, release, disconnect, faults and deadline expiry end the step as
cancelled, expired, faulted or unsupported_terminal, keep release_required until a
valid bridge-control-clear fact and are absorbing; the deadline wins same-timestamp ties. At most
64 facts and a 250 ms authority window apply. The real adapter does not yet supply
per-update consumption, a transaction-bound bridge-control-clear receipt, a sealed endpoint or ordering facts, and
the receipt reader still rejects partial/terminal steps. Design: openspec change
episode-lifecycle, section "Native step lifecycle reducer".

The source 0.4.6-dev trace records `action_accepted`, `hold_update`, `release`,
`release_update` and `release_input` only as bridge-side observations. Clearing this
bridge's held override does not prove physical neutrality or exclude user/other-mod
input. Input-query returns, post-update callbacks and frame deltas likewise do not
prove that the requested input was consumed for the exact interval. A live step stays
unsupported until those producer claims and a complete event endpoint are independently
verified on the target game build.

Primary review hardened cleanup: release must cover the latest observed command
progress and follow all timestamps; context changes invalidate old confirmation.
New session/epoch frame counters are not compared with old counters. Evidence
processing stops at 64 submissions with a saturating counter, but constant-size
late cleanup validation remains possible after overflow. Any interruption or
conflict after READY withholds future candidates, including transport faults at
later frames. Old snapshots stay immutable; READY is provisional and a future
sender needs a final delivery guard. These rules do not enable partial receipts.

## Lua step evidence hooks (offline, diagnostic)

Source 0.4.6-dev extends the default-off `callback_trace` with bounded acceptance,
post-update and release/input records (see [NATIVE_STEP_EVIDENCE.md](NATIVE_STEP_EVIDENCE.md)).
They add no wire field or capability and feed no reducer; consumption, neutral release and
READY remain unavailable from the engine.
