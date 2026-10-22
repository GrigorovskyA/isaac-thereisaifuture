## Why

Roadmap item 05: the environment needs one place that owns episode identity,
terminal outcomes, timeouts and fault handling, so a transport failure can never be
mistaken for a character death. Defining it over a `GameBackend` protocol makes it
testable offline now and reusable with the real bridge later.

## What Changes

- Add `episodes.py`: `Scenario`, `Action`, `GameBackend` protocol, `EpisodeController`,
  `Transition`, `EpisodeSummary`, `EpisodeFault`.
- Add `sim.py`: an offline toy room backend that is explicitly not Isaac.
- Identity checks per step (session, epoch, frame monotonicity, room visit, event interval).
- Release of control on every episode end, fault and interruption.

## Scope and non-goals

- In scope: lifecycle state machine, outcomes, fault records, toy backend, offline tests.
- In the native increment: bounded combined step transport, strict result/event models,
  fail-closed negotiation and offline peer/callback tests.
- The producer reference retains post-baseline events through explicit delivery
  acknowledgement with bounded memory; it does not establish callback ordering.
- A default-off passive callback probe prepares raw outcome-ordering evidence;
  it neither emits outcome events nor accepts terminal/partial step receipts.
- Diagnostic activation moves to explicit oracle_probe_v1 negotiation from Python,
  preserving per-mod-load limits without replacing installed Lua files per run.
- Bounded post-update HP samples prepare a later ordering experiment; raw values
  and unavailable statuses remain separate from realized damage/outcomes.
- Later-frame raw HP samples (at most three per entry, four callbacks, 16 entries) in
  observer 0.4.5-dev source investigate timing only; no damage, settlement or completion claim.
- Out of scope until prerequisites: general game reset/start commands and save handling;
  a complete automatic real bridge backend remains gated. Also out of scope:
  Gymnasium API (item 06), rewards (item 07).
- Episode management here never touches saves; the real-game reset path stays blocked
  until training isolation is verified.

## Dependencies and risks

- Depends on observation-and-event-contract-v1 for frames and oracle events.
- Unknown: how the real game starts/ends a scenario room on J460; the protocol only requires
  that a backend produce a first frame and bounded steps.
- Risk: the toy backend may hide timing issues of the real bridge.

## Acceptance criteria

- Offline: 100 consecutive short toy episodes end without manual recovery, with consistent
  episode and frame IDs.
- Offline: injected transport timeout raises `EpisodeFault`, is recorded, releases control and
  is not reported as death or timeout.
- Offline: stale frames, epoch/session/room changes and out-of-interval events are faults.
- Pending real game: 100 consecutive short episodes on an authorized profile.

## Native integration increment (added in revision 2)

Beyond the offline controller, this change prepares the native integration contract: combined
entity+action negotiation, step synchronization, separated oracle events, pause handling and the
explicit gate on general start/reset. Implementation follows primary-agent review of these artifacts.
Non-goals remain: no GameBackend that ignores actions, no reset/start commands, no lease renewal,
no relaxed restart limit, no save or Steam Cloud handling. The 100 real short episodes stay
unfinished and blocked. Observation-only attach recording (item 04) does not satisfy item 05.

Offline subtask 3.9 adds a pure, unwired native step lifecycle reducer that freezes how
acceptance, interval, release and a sealed event endpoint combine into a local READY
candidate or an absorbing cancelled/expired/faulted outcome. It changes no wire format,
client, receipt validation or observer, and proves no engine behavior.

Offline subtask 3.10 adds bounded producer-side step-evidence records (acceptance, post-update,
release/input) to the default-off `callback_trace` in source 0.4.6-dev. It feeds no reducer,
claims no engine consumption or readiness, and changes no wire format or authority.

## Impact

Existing offline modules remain. Native integration adds explicitly negotiated
step/event message types while retaining protocol version 1 and all default
0.4.0 message shapes. No existing mode silently upgrades.
