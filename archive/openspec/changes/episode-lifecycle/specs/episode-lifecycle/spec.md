## ADDED Requirements

### Requirement: Distinct episode outcomes
The episode controller SHALL report character death and room clear as terminated, a game-update
timeout as truncated, and MUST NOT report any infrastructure fault as a transition.

#### Scenario: Time limit reached
- **WHEN** the elapsed game updates reach the scenario limit without a terminal event and both terminal kinds were explicitly covered over the whole episode
- **THEN** the transition is truncated with outcome timeout and is not terminated

#### Scenario: Death and clear in one interval
- **WHEN** one step contains both a death and a room-clear event
- **THEN** the outcome is death

#### Scenario: Transport fails during a step
- **WHEN** the backend raises a bridge error while stepping
- **THEN** an episode fault is raised and recorded, control is released and no death or timeout is reported

### Requirement: Terminal event coverage is an explicit claim
A backend result MAY carry an explicit `terminal_coverage` claim naming the terminal `OracleEvent` kinds (`player_died`, `room_cleared`) it delivered exhaustively for that result's exact frame interval. The default is empty, meaning unknown for both kinds. Coverage MUST NOT be inferred from requested or recorded kinds, provenance or the absence of event records, and MUST NOT change identity checks, rewards, checkpoints, models or native wire formats.

#### Scenario: Default is unknown
- **WHEN** a backend result carries no coverage claim, even with an empty event list
- **THEN** both terminal kinds are unknown for that interval

#### Scenario: Coverage is not eligibility
- **WHEN** the synthetic backend declares complete coverage, or a backend declares none
- **THEN** only the offline contract changes: no native producer coverage, Lua export, runtime eligibility or event delivery is established, and tasks 3.6 and 3.8 stay open

### Requirement: Coverage aggregates conservatively into tri-state facts
The controller MUST treat a kind as complete only if every result from the initial result onward covered it; a later complete interval MUST NOT repair an earlier gap. A summary fact (`died`, `room_cleared`) MUST be true after a positive event of that kind, false only when the kind is complete over the whole episode and no such event occurred, and otherwise null (unknown).

#### Scenario: Coverage lost in a later interval
- **WHEN** a kind is covered by some results but one interval, including the initial result, omits it, even if later intervals cover it again
- **THEN** that kind is incomplete for the rest of the episode and its fact is never false

#### Scenario: Partial coverage and per-kind facts
- **WHEN** only one terminal kind is covered over the whole episode and the scenario limit is reached without a terminal event
- **THEN** the covered kind's fact is false and the other kind's fact is null

#### Scenario: Death and clear facts in one interval
- **WHEN** one step contains both a death and a clear event
- **THEN** the outcome is death while both facts record their observed events as true

### Requirement: Death and clear resolve only on covered evidence
A death event MUST resolve as death and keeps precedence over a clear in one interval. A clear event MUST resolve as cleared only when death coverage is complete over the episode so far; otherwise the outcome MUST be the explicit unknown and control MUST be released.

#### Scenario: Terminal initial result cannot start control
- **WHEN** the initial backend result contains a death or clear event, with any coverage claim
- **THEN** start raises an episode fault and releases control before allowing any action; no playable reset state or game outcome is fabricated

#### Scenario: Known death
- **WHEN** a death event arrives, with or without coverage
- **THEN** the outcome is death, the transition is terminated and the death fact is true; the clear fact is true if a clear event occurred, false if clear coverage was complete and none occurred, otherwise null

#### Scenario: Known clear
- **WHEN** a clear event arrives and death coverage is complete over the episode so far with no death event
- **THEN** the outcome is cleared, the transition is terminated, the clear fact is true and the death fact is false

#### Scenario: Clear with incomplete death coverage
- **WHEN** a clear event arrives and death coverage is incomplete for any interval of the episode so far
- **THEN** the clear is not resolved as cleared: the outcome is the explicit unknown with a truncated, not terminated, transition, control is released and the episode stops; the clear fact is true and the death fact is null

### Requirement: Time limit and unknown outcomes are explicit
At the scenario limit the outcome MUST be timeout only when both kinds are complete over the episode and neither terminal event occurred, and otherwise unknown. An unknown outcome MUST be truncated and not terminated, MUST release control, and MUST NOT be counted as death, clear or timeout.

#### Scenario: Complete coverage without events
- **WHEN** every result from the initial result onward covers both terminal kinds, no terminal event occurs and the scenario limit is reached
- **THEN** the outcome is timeout, the transition is truncated and both facts are false

#### Scenario: Missing or partial coverage at the limit
- **WHEN** the scenario limit is reached without a terminal event and either kind is incomplete
- **THEN** the outcome is unknown with a truncated, not terminated, transition and control is released

#### Scenario: Unknown is not a game outcome
- **WHEN** an episode ends as unknown
- **THEN** it is not counted as death, clear or timeout, and a following step without a new start is rejected

### Requirement: Evaluation metrics keep unknown outcomes separate
Evaluation records and metrics SHALL carry an explicit unknown outcome and count, distinct from faults. Unknown episodes MUST NOT enter the death, clear or timeout totals or the clear-rate and Wilson denominator, which is the known-outcome count; damage and return means keep covering every non-fault episode. The serialized report version MUST identify this metrics shape.

#### Scenario: Unknown and fault episodes in one evaluation
- **WHEN** an evaluation contains cleared, death, unknown and fault episodes
- **THEN** unknown and faults are counted separately, the clear rate and its interval use only the cleared and death episodes, and the damage and return means cover every non-fault episode

#### Scenario: Only unknown episodes
- **WHEN** every non-fault episode ended as unknown
- **THEN** the known-outcome count is zero, the clear rate is 0.0 with the uninformative interval (0.0, 1.0) and the unknown count is reported

#### Scenario: Uncovered backend through the evaluation loop
- **WHEN** a backend declares no terminal coverage and episodes are evaluated end to end
- **THEN** unresolved clears and limits are recorded as unknown, never as cleared or timeout, no ended episode is stepped again and the serialized report carries the new version

### Requirement: Identity and freshness checks
The controller MUST reject frames or events whose identity or ordering is inconsistent with the
running episode.

#### Scenario: Stale frame
- **WHEN** a step returns a frame whose frame ID does not exceed the previous one
- **THEN** the episode faults

#### Scenario: Session, epoch or room changes
- **WHEN** the session or game epoch differs from the first frame, or the room visit changes in a
  scenario that does not allow room changes
- **THEN** the episode faults

#### Scenario: Event outside the step interval
- **WHEN** an event carries a frame ID outside the interval of the step
- **THEN** the episode faults

### Requirement: Control release
The controller SHALL release backend control when an episode ends, faults or is stopped, and
stopping MUST be idempotent.

#### Scenario: Interrupted episode
- **WHEN** stop is called twice during a running episode
- **THEN** the episode is no longer running and release was requested each time

### Requirement: Consecutive episode reliability
Starting a new episode SHALL give it a new monotonically increasing episode ID and must not depend
on manual recovery after a normal end.

#### Scenario: One hundred short episodes
- **WHEN** one hundred short episodes run back to back on the offline backend
- **THEN** all end with their own episode ID and no fault is recorded

### Requirement: Offline backend labeling
The toy simulator MUST label all its data as synthetic and MUST NOT be presented as evidence of
game behavior.

#### Scenario: Synthetic provenance
- **WHEN** the simulator emits a frame or event
- **THEN** its provenance is synthetic

### Requirement: Explicit combined entity and action negotiation
A native backend SHALL obtain entity observations and bounded actions on one session only through an
explicitly negotiated capability. Default observation MUST remain read-only and receive no extra
fields, an unsupported peer MUST fail the handshake without fallback, and all existing action
authority, approval, heartbeat and expiry checks MUST still apply. Action and death-restart modes
MUST remain mutually exclusive.

#### Scenario: Peer lacks the combined capability
- **WHEN** the client requires the combined capability and the peer does not advertise it
- **THEN** negotiation fails before any snapshot or command and no entity-only or action-only mode is used silently

#### Scenario: Default client
- **WHEN** a client requests only the existing observation capabilities
- **THEN** it receives no entity frame, no command channel and no oracle event

#### Scenario: Restart and actions together
- **WHEN** a client requests the combined capability together with death restart
- **THEN** negotiation fails

### Requirement: Per-kind oracle capability negotiation is explicit and fail-closed
A native-episode client MAY require an explicit, nonempty, duplicate-free subset of the seven existing
`OracleEvent` kinds by exact name `oracle_<kind>_v1`, always with `entity_action_v1` and with no fallback.
A peer missing any required name MUST fail the handshake before a snapshot or command. Existing modes
MUST request what they did before and the 16-entry `hello_ack` limit MUST NOT change. A handshake MUST NOT
be read as producer coverage, delivery or runtime eligibility.

#### Scenario: Explicit kind subset
- **WHEN** a native-episode client requires one or more valid kinds and the peer advertises each exact name and `entity_action_v1`
- **THEN** the hello requires only the requested names after the native transport name and negotiation succeeds without enabling unrequested kinds

#### Scenario: Invalid or incompatible kind request
- **WHEN** the request is empty, not a tuple, contains an unknown or non-string kind or a duplicate, is made without native-episode mode, or combines with default, live-loop, probe, action, restart or entity-observation mode
- **THEN** configuration is rejected locally before a listener opens or a hello is sent

#### Scenario: Old or partial peer
- **WHEN** the peer lacks the native transport name or any requested per-kind name, or advertises only another version, a prefix or a different kind
- **THEN** negotiation fails before any snapshot or command and no event is inferred, downgraded or replaced by another source

#### Scenario: Existing modes
- **WHEN** a client uses default, action, restart, entity, probe, native-step or live-loop mode, even if the peer advertises per-kind names
- **THEN** the required-capability list is unchanged and requests no per-kind name

#### Scenario: Full request at the acknowledgement limit
- **WHEN** a client requests all seven kinds and the peer lists the eight other names, `entity_action_v1` and seven per-kind names
- **THEN** the sixteen-entry acknowledgement is accepted, while a seventeenth entry is rejected even if every required name is present

#### Scenario: Negotiation is not eligibility
- **WHEN** a peer advertises a per-kind name
- **THEN** the client treats it only as an offered contract; producer coverage, delivery and runtime eligibility still need the separate export gate and evidence

### Requirement: Native receipts accept only requested oracle kinds
A native receipt consumer MUST accept a `native_oracle_event` only when its kind is in the set the consumer itself requested for this connection; the set MUST be empty when none was requested and MUST NOT be widened by extra `hello_ack` names. Any other kind, including a replayed event ID, MUST fault the receipt before the cursor or receipt is committed, and existing identity, ordering, interval and watermark checks MUST stay unchanged.

#### Scenario: Requested kind
- **WHEN** a receipt carries events whose kinds were all requested
- **THEN** the events are accepted in order under the unchanged identity, interval and watermark checks

#### Scenario: Advertised but unrequested kind
- **WHEN** the peer advertises a kind that the client did not request and sends an event of that kind
- **THEN** the receipt faults, the cursor, active state and receipt sequence stay uncommitted (a valid earlier event in the same receipt is not committed) and the connection closes as an infrastructure fault

#### Scenario: No requested kinds
- **WHEN** the client requested no per-kind name
- **THEN** every `native_oracle_event` faults the receipt, while an event-free receipt remains valid

#### Scenario: Enforcement is not eligibility
- **WHEN** a receipt passes the kind check
- **THEN** no Lua export, producer coverage, recording-format change or runtime eligibility follows, an absent kind is never inferred as a negative outcome, and tasks 3.6 and 3.8 stay open

### Requirement: Native oracle recordings persist requested kinds
A new `native_oracle_events` recording MUST be created with an explicit tuple of unique, supported `OracleEvent` kinds and MUST persist it as `native_oracle_kinds` in its manifest (`[]` when none were requested). The writer and replay MUST reject a native event outside an explicit list before writing or yielding it. A legacy native manifest without the field MUST decode as unknown, not empty, and replay unchanged; other streams MUST keep their manifest shape and MUST NOT accept the field.

#### Scenario: Explicit requested kinds
- **WHEN** a native recording is created with a nonempty kind tuple
- **THEN** the manifest lists those kinds in order, events of those kinds record and replay, and no event is required for every listed kind

#### Scenario: Empty request
- **WHEN** a native recording is created with an empty tuple
- **THEN** the manifest holds `[]`, the writer rejects every event, and replay of a file with an event under that manifest faults on the first event

#### Scenario: Event outside the manifest set
- **WHEN** replay reads a native event whose kind is not in an explicit manifest list
- **THEN** replay faults before yielding that event, while earlier in-set events were already yielded

#### Scenario: Legacy native manifest
- **WHEN** a native manifest has no `native_oracle_kinds` field
- **THEN** the replayed manifest reports the kinds as unknown (`None`), not empty, every kind replays as before, and no absent event is inferred as a negative outcome

#### Scenario: Malformed metadata
- **WHEN** the field is null, not a list, holds an unknown or non-string name, or repeats a name, or a new recording is created without a tuple of valid unique kinds
- **THEN** replay fails when the recording is opened, and creation fails without creating a file

#### Scenario: Other streams unchanged
- **WHEN** a `policy_frames` or `oracle_events` recording is written, or its manifest carries the field
- **THEN** the written manifest keeps its previous shape and bytes, and creation or replay with the field is rejected

#### Scenario: Persistence is not coverage
- **WHEN** a manifest lists requested kinds
- **THEN** that is integrity metadata only; it proves no producer coverage, delivery or runtime eligibility, changes no event, receipt or recording payload semantics, and tasks 3.6 and 3.8 stay open

### Requirement: Step synchronization contract
A native step SHALL report the requested repeat, the actual elapsed game updates computed from frame
identity, and the accepted versus completed status of the action as separate facts. The step MUST
complete or fault within a bounded wait; it MUST NOT silently be satisfied by a later snapshot that
omits the requested interval, and rendering rate MUST NOT be assumed equal to game update rate.

#### Scenario: Action expires early
- **WHEN** the action hold ends before the requested repeat elapses because of its deadline, a room transition or an input fault
- **THEN** the step result states the actual elapsed updates and that the action did not complete, or the episode faults

#### Scenario: Acknowledgement is not completion
- **WHEN** a command is acknowledged
- **THEN** the acknowledgement records acceptance only; a later frame delta records elapsed game frames but does not prove that the requested input was consumed by the game

#### Scenario: Callback exposure is not consumption
- **WHEN** input-query counts, an input callback return, a hold update, or an observer post-update is the only evidence for a step
- **THEN** the step remains unsupported or waiting; none of those observations alone proves the exact requested interval was consumed

#### Scenario: No snapshot within the wait
- **WHEN** no fresh active snapshot arrives within the bounded wait
- **THEN** an episode fault is raised and control is released

### Requirement: Separated native outcome events
Native outcome and oracle events SHALL be delivered as typed bounded messages with session, epoch,
frame and event identity, validated into oracle types that are kept apart from policy frames,
normalizer input and policy recordings. Events MUST be deduplicated by identity within a session
and MUST lie in the step interval. Death, clear or timeout MUST NOT be inferred from a disconnect,
zero health alone or missing enemies.

#### Scenario: Duplicate event
- **WHEN** an event identity already delivered in this session is received again
- **THEN** it is not counted twice

#### Scenario: Oracle data in a policy path
- **WHEN** a native oracle event reaches the policy encoder or policy recording
- **THEN** the integration is invalid and a test fails

#### Scenario: Disconnect while health is zero
- **WHEN** the peer disconnects with no death event received
- **THEN** the episode faults and is not reported as terminated

### Requirement: Explicit native event completion barrier
A native step completion MUST carry the last contiguous event ID for its interval barrier.
The receiver MUST match it to the bound event cursor before accepting the transaction;
a missing tail or a cursor ahead of the barrier is a fault.

#### Scenario: Event barrier mismatch
- **WHEN** a completion declares a last event ID different from the receiver's contiguous event cursor
- **THEN** the transaction faults and no successful transition is yielded

#### Scenario: Missing event barrier
- **WHEN** a native completion omits the required last event ID
- **THEN** the message is rejected

### Requirement: Paused and transitional snapshots
The native adapter SHALL ignore paused or unavailable snapshots within a bounded deadline before
yielding a fresh result, and MUST keep rejecting stale active frames. The controller freshness check
MUST NOT be weakened.

#### Scenario: Pause then resume
- **WHEN** paused snapshots repeat a frame and an active snapshot with a greater frame follows within the deadline
- **THEN** the step uses the active snapshot

#### Scenario: Pause outlasts the deadline
- **WHEN** no active snapshot arrives before the deadline
- **THEN** an episode fault is raised

#### Scenario: Stale active frame
- **WHEN** an active snapshot does not exceed the previous frame
- **THEN** the episode faults

### Requirement: General start and reset remain gated
General episode start/reset SHALL remain unsupported until verified isolation and
explicit authority exist. Unsupported operations MUST fail explicitly. Preserve
operator-directed launch, manual slot selection, three restarts per ten minutes
and the nonrenewable 120-second action lease. Ordinary-profile action permission
MUST NOT be treated as training isolation.

#### Scenario: Operator-directed process launch
- **WHEN** the user requests an agreed check and preflight passes
- **THEN** the agent may launch the process once, with manual save selection and no unattended startup, recovery or forced reset

#### Scenario: Reset requested without authority
- **WHEN** a native backend is asked to start or reset an episode without verified isolation and authority
- **THEN** it raises an explicit unsupported error and no action is sent

#### Scenario: Lease expiry
- **WHEN** the 120-second action lease expires
- **THEN** no new approval or handshake renews it within the same mod load and the episode faults


### Requirement: Bounded callback diagnostics
Optional callback tracing SHALL be disabled by default, start only after an authorized
action, and remain bounded to 512 log attempts and a ten-second window per mod load.
It MUST NOT renew through reconnects, enter policy/wire data, change input semantics
or weaken runtime limits. Diagnostic failures MUST leave control cleanup intact.

#### Scenario: Trace disabled
- **WHEN** the operator uses default observation or action configuration
- **THEN** no callback trace is produced

#### Scenario: Trace budget exhausted
- **WHEN** the record or time budget is exhausted and the peer reconnects
- **THEN** tracing stays ended and no budget is renewed

#### Scenario: Diagnostic logger fails
- **WHEN** a trace logger raises an error
- **THEN** tracing stops while existing input and cleanup behavior is preserved


### Requirement: Passive timing evidence stays bounded and factual
An offline timing ledger SHALL keep fixed-size query and post-update observations,
validate caller-supplied values and return detached snapshots. It MUST NOT equate
query coverage with applied simulation updates or produce gameplay outcomes,
completion receipts or input authority.

#### Scenario: Duplicate input queries
- **WHEN** the same hook and frame are observed before and after a post-update
- **THEN** the ledger retains bounded exposure counts without declaring applied steps

#### Scenario: Release before endpoint update
- **WHEN** release is recorded before the endpoint post-update observation
- **THEN** the bounded later observation may be retained without changing release

#### Scenario: Observation budget exceeded
- **WHEN** more than 4096 valid query or post-update observations are submitted
- **THEN** the extra observation fails without changing the ledger

### Requirement: Producer event delivery is bounded and explicit
An offline outbox SHALL retain post-baseline native events until acknowledgement,
with contiguous IDs, identity/frame checks and no eviction. It SHALL bound pending
data to 32 records / 32768 bytes and commit watermarked intervals only through
their exact staged object. Faults SHALL close and clear it permanently. It MUST
NOT claim engine synchronization or input application.

#### Scenario: Event precedes first command
- **WHEN** an event follows the explicit baseline but precedes command acceptance
- **THEN** the first matching sealed interval includes it

#### Scenario: Future event and empty interval
- **WHEN** only an event beyond the sealed endpoint is pending
- **THEN** the empty batch retains the committed watermark and the future event stays queued

#### Scenario: Late event or overflow
- **WHEN** an event arrives at a sealed boundary or exceeds a pending queue limit
- **THEN** the outbox faults, clears retained data and cannot be reused

#### Scenario: Delivery acknowledgement
- **WHEN** the exact staged batch is acknowledged after delivery
- **THEN** only its prefix is removed and the committed interval advances

### Requirement: Passive outcome diagnostics preserve gameplay
A default-off passive probe SHALL start only on explicitly negotiated read-only
attach using oracle_probe_v1 and record raw
callback facts outside policy/wire data. It SHALL stop within 120 seconds, 1024
log attempts or 128 entity labels per mod load, without reconnect renewal.
Diagnostic failures MUST NOT alter gameplay, observation or callback returns.

#### Scenario: Damage and award callback
- **WHEN** a diagnostic damage or clean-award callback runs or its logger fails
- **THEN** it returns nil and does not cancel damage, rewards or other callbacks

#### Scenario: Default or control mode
- **WHEN** the client omits the probe capability, including ordinary action or restart mode
- **THEN** no passive probe starts and existing wire behavior remains unchanged

#### Scenario: Incompatible diagnostic request
- **WHEN** the client combines the probe capability with action, restart or native-step mode
- **THEN** negotiation fails before diagnostics or control starts

#### Scenario: Unsupported or exhausted diagnostic request
- **WHEN** the peer lacks the capability or its one-shot diagnostic window is exhausted
- **THEN** the explicit request fails without fallback while ordinary observation remains available

#### Scenario: Permanent installation
- **WHEN** an operator requests bounded diagnostics from Python on a compatible installation
- **THEN** the same source-matching mod files are used without editing a diagnostic flag

#### Scenario: Diagnostic budget exhausted
- **WHEN** a record/time/entity limit is reached or the peer disconnects
- **THEN** the probe stops, clears diagnostic maps and cannot restart on reconnect

#### Scenario: Partial step after death candidate
- **WHEN** a death or transition candidate accompanies a non-completed step
- **THEN** existing receipt validation faults without accepting a policy transition

### Requirement: Deferred HP diagnostics stay bounded and factual
The negotiated probe SHALL retain at most 16 target entries across its bounded
sampling window, coalescing repeats without postponement. Removed, missing
or relabelled targets SHALL yield an explicit unavailable status, not zero HP.
Overflow SHALL stop diagnostics; transitions and faults SHALL clear references.
These samples MUST NOT be treated as applied damage or a completion barrier.

#### Scenario: Old intermediate HP
- **WHEN** NPC-update shows old HP and the later post-update sees a different value
- **THEN** both raw facts are preserved without emitting a damage outcome

#### Scenario: Removed target
- **WHEN** a staged target is removed before the next post-update
- **THEN** its reference is released and a scalar removed status is logged without reading HP

#### Scenario: Pending target overflow
- **WHEN** a seventeenth distinct target is staged before flushing
- **THEN** diagnostics stop and clear targets without eviction or gameplay changes

#### Scenario: Repeated target and cleanup
- **WHEN** repeated callbacks stage the same target and a transition or disconnect follows
- **THEN** at most one pending entry exists and no retained reference survives cleanup

### Requirement: Later-frame HP diagnostics stay bounded and factual
The probe SHALL take at most three raw HP samples per entry: one at its first
post-update callback and two only in strictly later game frames. The first MAY
share the attempt frame. Entries SHALL expire after four post-update callbacks,
including unchanged frames, releasing references and logging expiry when budget
permits. Samples MUST NOT imply applied damage, settlement or completion.

#### Scenario: Old first sample then changed later HP
- **WHEN** the first post-update in the attempt frame shows old HP and a callback in a later frame shows a different value
- **THEN** both raw samples are logged with the original staging context and sample index, without a damage outcome

#### Scenario: Same-frame callbacks
- **WHEN** further observer post-update callbacks occur without the game frame advancing
- **THEN** no later sample is taken, yet each callback still counts toward the four-callback lifetime

#### Scenario: Window expires
- **WHEN** four callbacks pass after staging and fewer than three samples were taken
- **THEN** the reference is released and an expiry fact is logged without fabricated HP

#### Scenario: Third sample completes
- **WHEN** the third sample is taken
- **THEN** the entry is released without an expiry fact and a new attempt may stage a fresh window

### Requirement: Later-frame diagnostics share capacity and cleanup
First and later stages SHALL share a 16-entry capacity, stopping on a seventeenth
target without eviction, and the existing nonrenewable 120000 ms, 1024-attempt,
128-label and 400-byte limits. Unavailable targets SHALL yield facts without HP.
Transitions, faults and reentrant reads SHALL clear references and suppress old-
context samples. Diagnostics MUST NOT add wire data, events, rewards or input authority.

#### Scenario: Unavailable target between samples
- **WHEN** a staged target is removed, missing or relabelled before a later sample
- **THEN** a scalar unavailable fact is logged, the reference is released and HP is never read as zero

#### Scenario: Combined capacity
- **WHEN** a seventeenth distinct target is staged while sixteen first or later entries exist
- **THEN** diagnostics stop with reason=pending, all references are released and gameplay is unchanged

#### Scenario: Transition, stop or fault
- **WHEN** a room, floor, game start/end, disconnect, exit, unload, budget stop or read/logger fault occurs
- **THEN** all entry references are released and no later sample from the old context is logged

#### Scenario: Frame read reenters a transition
- **WHEN** reading the flush frame reenters a room transition before per-target sampling
- **THEN** the diagnostic window is invalidated without reading or logging old targets in the new room

### Requirement: Native step readiness is a bounded local decision
An offline reducer SHALL combine matching acceptance, an exact full interval, bridge-control-clear and a sealed same-context watermark into a local, undelivered candidate. It SHALL accept at most 64 evidence submissions without renewing authority; excess calls permit only bounded cleanup validation. The reducer MUST NOT send, serialize, emit events or rewards.

#### Scenario: All evidence agrees
- **WHEN** the four facts arrive in any order and agree on identity, interval, release frame and endpoint
- **THEN** one fresh READY candidate is returned, labelled as local and not delivered

#### Scenario: Evidence is missing or partial
- **WHEN** acceptance, a short or long interval, bridge-control-clear or the sealed watermark is missing or inconsistent
- **THEN** the step stays waiting or faults and is never completed

#### Scenario: Producer evidence is not verified
- **WHEN** the only available producer observations are action acceptance, input callback returns, hold updates, release callbacks, nil input overrides or post-update callbacks
- **THEN** they do not establish consumed updates, neutral final game input or a sealed event endpoint, and no live step completion is accepted

### Requirement: Native step evidence provenance
Reducer facts SHALL be treated as caller assertions; the reducer MUST NOT claim their provenance or engine truth. A local candidate MUST NOT be used as live completion until producer evidence is independently verified for the target game build.

#### Scenario: Candidate has unverified inputs
- **WHEN** the reducer returns READY from internally consistent supplied facts
- **THEN** the result remains a local candidate and cannot authorize a live transition

#### Scenario: Fact limit
- **WHEN** a sixty-fifth fact is submitted to a waiting step
- **THEN** the step faults without evicting earlier facts

### Requirement: Native step outcomes fail closed and stay absorbing
Interruptions, expiry, context changes and faults SHALL end in absorbing non-success outcomes. Conflicts after READY SHALL withhold future candidates; deadlines win ties; replay and new contexts MUST NOT renew or reuse evidence.

#### Scenario: Interrupted step
- **WHEN** a pause, transition, death candidate, disconnect or transport fault arrives while waiting
- **THEN** the outcome is terminal, release_required stays true and no new-room frame is attached

#### Scenario: Late release
- **WHEN** a valid release fact follows any terminal outcome
- **THEN** only the bridge-control-clear bookkeeping flag is cleared and the outcome is unchanged; no claim is made about final input seen by the engine

### Requirement: Native bridge-control cleanup
Cleanup SHALL retain `release_required` until a matching monotonic bridge-control-clear fact covers observed progress. This fact records removal of this bridge's hold only; it MUST NOT imply physical neutrality or absence of user/other-mod input.

#### Scenario: Bridge override cleared
- **WHEN** the matching bridge-control-clear fact follows the latest observed progress
- **THEN** bridge cleanup is complete while final game input remains unknown

#### Scenario: Deadline tie
- **WHEN** the completing fact carries the deadline timestamp
- **THEN** the step is expired and no candidate is produced

#### Scenario: Stale cleanup or exhausted evidence budget
- **WHEN** a release predates known progress or cleanup arrives after evidence overflow
- **THEN** stale release cannot clear cleanup and a valid late release can clear only cleanup without accepting more completion evidence

#### Scenario: Failure before delivery
- **WHEN** contradictory, malformed or regressing facts or an interruption arrive after READY
- **THEN** future decisions withhold the candidate and preserve the immutable prior snapshot without implying delivery

#### Scenario: New context resets frame identity
- **WHEN** a new session or epoch resets its frame counter
- **THEN** its context change ends the old step without comparing foreign frame counters or reusing old cleanup confirmation


### Requirement: Bounded Lua step evidence
With `callback_trace` enabled, the observer SHALL log bounded scalar producer-side facts for acceptance, post-update and release/input of an accepted action inside the existing trace limits. It SHALL NOT claim engine consumption, completion or readiness, and SHALL NOT change validation, acks, input returns, release or watchdog behavior.

#### Scenario: Accepted action
- **WHEN** an authorized action passes validation
- **THEN** one acceptance record carries hold end frame and wall deadline, post-update records appear at most once per frame, and the release record carries the original hold sequence and observed frame/wall expiry conditions

#### Scenario: Pending release
- **WHEN** a hold is cleared
- **THEN** at most one next post-update and one next nil-override input query are recorded, a new accepted action or context change discards it, and nil override is not reported as neutral input

#### Scenario: Off or failed diagnostics
- **WHEN** the trace is off, exhausted, over-long, re-entered or its read/logger fails
- **THEN** no further reads or records occur and command handling is unchanged
