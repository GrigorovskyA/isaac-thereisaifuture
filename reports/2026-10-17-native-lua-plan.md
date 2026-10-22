# Evidence: episode-lifecycle / native-lua-plan-01

- Date/time and timezone: 2026-10-17, Europe (+02:00)
- Git revision and dirty status: 10db51c base, dirty (uncommitted working tree, shared SMB copy)
- Change scope and acceptance criteria: a source-backed plan before task 3.6. No code, spec,
  design, deployment or runtime action. Line numbers refer to `mod/observer/main.lua` (615 lines,
  mod 0.4.0) unless another file is named.
- Game/mod/bridge versions: observer 0.4.0 (installed, unchanged); Isaac API order not verified.
- Python/package versions and configuration hash: not applicable (reading only).
- Scenario, split, seeds, budget, and stop conditions: not applicable.

## Results

| Check/requirement | Command/scenario | Exit code | Status | Evidence |
|---|---|---|---|---|
| Source facts cited with lines | read of main.lua, actions/native_* modules, protocol doc | 0 | passed | section 1 |
| Callback-order assumptions separated | section 1 table, column "kind" | - | passed | assumptions listed A1-A7 |
| Lua/Python behavior tests | none run (plan only) | - | not_run | no code written |
| Runtime probes | none run | - | not_run | closed-game authorization required |

## 1. Source facts versus assumptions

| Topic | Source fact (line) | Kind |
|---|---|---|
| Frame cadence | Snapshot sampled from the MC_POST_RENDER pump (516-519, 436-441) every `sample_ms`=200 (line 5, 438); `update_id` = MC_POST_UPDATE counter (520-523, 310); `frame_id` = `Game():GetFrameCount()` (`capture`, 277-302) | fact |
| Single output slot | `queue` (131-139) closes with "Output limit exceeded" if a message is already pending; a 16384-byte cap per record | fact |
| Command freshness | `command` (321-370) requires `frame_id == state.snapshot_frame` (338) and current frame within 15 (354-356); `snapshot_frame` is set only after the snapshot is fully flushed (450-453) | fact |
| Acceptance | Hold is created with `frame` = frame at accept time, `until_frame = frame+frames`, `deadline = now+250` (362-365); ack carries the same frame (367-370) | fact |
| Input application | `MC_INPUT_ACTION` (576-600) calls `action_guard`, then returns the held value for the player's cardinal buttons; nothing counts applied frames | fact |
| Guard/release | `release` (38-42); `action_guard` (63-78) releases on pause, death, multi-player (70) and on expiry by wall time, frame limit, epoch or room change (74-77); heartbeat/lease expiry closes the connection (66-68) | fact |
| Lease | 120 s non-renewed lease set at first arm (455); heartbeat 500 ms refreshed per command (357) | fact |
| Transitions | `MC_POST_GAME_STARTED` (525: epoch+1, room 0, release), `MC_POST_NEW_ROOM` (556: visit+1, release, entity ids reset), `MC_POST_NEW_LEVEL` (572), `MC_POST_GAME_END` (544: release, disarm actions) | fact |
| Death | No native death event is emitted; `IsDead()` only releases (70); restart code uses MC_POST_GAME_END(game_over) (544-554) | fact |
| Negotiation | Capability list (18), advertisement (154-158), mode exclusions (173-176); `entity_action_v1` is not advertised, so 0.4.0 fails the native hello by design | fact |
| Bounded output | Entity caps 12/20/12/4 (line 29), scans <= 1024 entities and <= 2048 grid cells (207-210); command input limit 1024 bytes (415-421) | fact |
| Oracle events | main.lua has no event hooks; the only mention is a comment (28) | fact |

Assumptions that need a runtime probe (none are verified by installed-game evidence):

- A1. Order of MC_INPUT_ACTION, MC_POST_UPDATE and the frame increment within one update.
- A2. Whether `GetFrameCount()` at accept time (render callback) lies before or after the input
  consumption of that same frame, so the first controlled input is at `accepted_frame` or +1.
- A3. Whether MC_POST_UPDATE and MC_INPUT_ACTION are skipped while paused and how `update_id`
  behaves then.
- A4. Existence, arguments and order of damage/death/spawn callbacks relative to MC_POST_UPDATE.
- A5. Number of events of one kind in a single frame and across a room change.
- A6. Death sequence: `IsDead()`, MC_POST_GAME_END(game_over), MC_POST_GAME_STARTED ordering.
- A7. Render rate versus update rate on the target machine (design assumes 30 updates/s).

## 2. Smallest additive Lua increment (all in `mod/observer/main.lua`)

1. New constant `NATIVE_CAP = "entity_action_v1"`. In `hello` (141-193) advertise it only if
   `entity_capable()` and `action_authorized()` (existing functions, 22-61); when required it
   must not combine with any other mode (extend 173-176) and sets `actions.requested = true`
   plus `entities.requested = true`, reusing the existing arm/lease/heartbeat flow (450-465),
   so no renewed 120 s lease and no restart budget.
2. Command path: `command` (321-370) stays; a second branch recognizes `type="step_command"`.
   Factor out the shared integer/identity/staleness checks instead of copying them. Canonical
   string comparison and the 1024-byte limit stay. Acceptance still builds the same `hold`
   and ack (kind `action`), so the 15-frame/250-ms hold, replacement and release behavior is
   shared. Extra hold fields: `accepted_frame`, `applied` (set of distinct frames seen by
   MC_INPUT_ACTION, at most 15), `transaction=true`.
3. Completion hook: a new check in the MC_POST_UPDATE callback (520-523) after `action_guard`.
   It builds the existing entity frame (`capture_entities`, 205-275) once per transaction and
   queues the completion. Reuse of `capture` keeps one code path for entity data.
4. `release(reason)` (38-42) already has all cleanup call sites (guard, transitions, close).
   Route those reasons to a pending completion: `pause`, `transition`, `explicit_release`,
   `input_fault`, `wall_deadline`. Connection close drops it silently (a transport fault, not a
   completion).
5. Output: keep `queue` as is; add a bounded pending list (at most one completion plus at most
   N events per transaction, N in section 4) drained by `pump` before new snapshots. While
   the list is non-empty snapshots are skipped; sequence counters stay contiguous.
6. Nothing else changes: default mode stays read-only, death restart, lease loading,
   `mod_version` and deployment are untouched. Version string/packaging only when a deployment
   is separately authorized.

## 3. Acceptance versus completion versus applied input

- **Acceptance** (ack, line 367) is a validated command with a fresh snapshot; it proves only
  that a hold was created at the render-time frame.
- **Application** is evidence that MC_INPUT_ACTION returned the held values for a controlled
  frame. Proposal: completion is `completed` only if the number of distinct applied frames equals
  `requested_updates` and the final frame equals `accepted_frame + requested_updates`; fewer
  applied frames yield `cancelled/input_fault` (no new reason needed). A frame delta alone proves
  nothing about input; applied evidence proves the hook ran, not that the game obeyed it.
- **Completion** is emitted at the first MC_POST_UPDATE at or after `until_frame`, with the
  frame captured in that same callback so `elapsed = frame - accepted_frame` holds exactly.
- **Off-by-one risk (A1/A2):** if the render-time acceptance happens after the frame's input was
  already consumed, only `frames-1` frames can be applied. The probe must pick between
  `[accepted, accepted+n)` and `(accepted, accepted+n]`; until then the contract and completion
  must not claim exact application.
- **Wall deadline finding:** 250 ms at 30 updates/s is about 7 updates, so requests above ~7
  frames normally end as `expired/wall_deadline`. 6 frames (200 ms) fit. Do not raise the
  limits (rule); the training step size should be at most 6 frames unless a probe shows more.
- **Pause/death/transition:** pause releases the hold (70) -> `cancelled/pause`. Room or level
  change and game start -> `cancelled/transition`. **Gap:** there is no completion reason for
  death; `IsDead()` must not be mapped to another reason. Interim: close with an infrastructure
  fault and take death only from a later oracle `player_died`. A new reason needs a spec
  revision. Heartbeat (500 ms, refreshed by each step) still closes on silence.
- **Latency between steps:** the game does not pause between a completion and the next
  command; those frames are neutral input. The next command must reference a flushed frame within
  15 of the current frame, otherwise `command` raises and the connection closes (356). Allowing
  the completion's frame to become `snapshot_frame` after flush (like 450-453) avoids waiting
  for the next 200 ms snapshot; a stale command remains fatal and is a Python latency budget.

## 4. Event delivery, ordering and watermark

- Event hooks are absent from the source; candidate callbacks are assumptions (A4/A5) and each
  oracle kind is emitted only after its probe passes. Unproven kinds stay unavailable (never
  derived from zero HP, empty enemy list, disconnect or snapshot differences).
- Per session, `event_id` starts at 1 and is contiguous. Events before attach are not queued;
  recording begins at the first accepted step so a new cursor (last_id=0) is consistent after
  reconnect. Events in the neutral latency frames belong to the next step: the Python interval
  should start at the previous completion frame (episode start for the first), not at the new
  `accepted_frame`; this needs primary approval because `take` receives the interval.
- Ordering barrier: stream order ack -> events (frame <= completion frame) -> completion; the
  completion is only queued after all earlier events were queued, so the completion is a
  watermark in stream order. Late events (frame above the completion) belong to the next step.
- **Model revision needed:** `StepCompletion` has no event watermark, so tail loss cannot be
  detected and the order guarantee is implicit. Recommended: add `last_event_id` (strict
  non-negative integer, equal to the last emitted id, 0 if none) to the unshipped model and the
  spec; Python checks `cursor.last_id == last_event_id`. A new field must not be added silently.
- Gaps fault in the cursor (existing). Duplicates are suppressed by the cursor (existing).
- Overflow: per-transaction ring of N=32 events (fits several 16 KiB records per drain across
  renders); overflow -> close (transport fault), never a partial completion. At most one pending
  transaction; a second command while pending is a protocol fault. Disconnect clears all.
- Completion size: the largest EntityFrame must be measured offline to stay below 16384
  bytes (entity cap total 48).

## 5. Offline tests and minimal runtime probes

Offline Lua behavioral tests (extend `tests/test_lua_actions.py` harness, `build_lua`):

- native hello requires entity+action authority; mixed/legacy modes unchanged; 0.4.0-style
  default hello and legacy action tests still pass.
- ack differs from completion; completion exact for N applied frames; fewer applied frames
  give `input_fault`; expiry by wall clock; pause/transition/release/close mapped reasons.
- events: order before completion, ids contiguous, overflow closes, disconnect clears,
  reconnect starts at id 1 with no old pending events, death never inferred.
- size of the largest completion; backpressure (pending list drained, hold never extended).
- Python: stream-order test through a simulated peer with the watermark field.

Minimal runtime probes (each needs a closed-game, separately authorized deployment of a
log-only probe mod, never the observer): P1 frame/update/input order (A1-A3, A7); P2 pause
behavior (A3); P3 event callback existence/arguments/order (A4, A5); P4 death sequence (A6).
Probes print bounded lines, send nothing over the socket, never start/reset runs. Installed
observer stays 0.4.0; no training or reset.

## 6. Recommended next single task

**native-transaction-01 (Python only, offline):** `NativeStepClient.step(...)` transaction over
existing models, with frozen wire assumptions for approval:

1. One transaction at a time: send `StepCommand`, read ack, then zero or more
   `native_oracle_event`, then `step_completion`; any other record, wrong identity or sequence
   closes with `EpisodeFault`.
2. Events pass through `NativeEventCursor.take` with interval (previous completion frame or
   episode start, completion frame]; events later than the completion frame fault.
3. `validate_completion` and one absolute deadline (existing style); no inferred outcomes.
4. Include the small model revision `StepCompletion.last_event_id` (primary decision needed),
   otherwise the barrier stays implicit.
5. Still no Lua, deployment, CLI or GameBackend; death handling waits for the A6 probe.

Alternative if the primary prefers: write the probe mod design first. Neither counts as Isaac
acceptance.

## Real game

No real-game run took place; nothing was deployed or launched.

## Limitations and continuation

- Every callback-order statement is an assumption until probes P1-P4 run; simulated Lua
  tests (lupa) only prove the mod's own logic against stubs.
- Line numbers match the working tree at time of writing and shift with edits.
- Self-review (not independent): read-only work; only this report and agent-status.json written.
- Next action: orchestrator decides the watermark field, the interval-start rule, the death
  reason gap and the next task.

## Primary review and decisions (2026-10-17)

Source facts were checked against main.lua sections 22-78, 131-193, 321-370,
436-465 and 516-615. This accepts the source audit as planning evidence only;
recommendations are not an approved implementation contract in their entirety.
No tests were needed for this read-only report; the unchanged code previously
passed Check.ps1 with 606 tests and strict OpenSpec 24/24.

Decisions and corrections:
- Add required last_event_id to the unshipped StepCompletion model, with strict
  bounded counter semantics. No default: missing watermark fails closed. A helper
  must compare it to the contiguous cursor count; merely adding a field does not
  implement an event barrier. New model tests are the next bounded coding slice.
- The future interval begins at the last policy frame delivered to the caller,
  including neutral elapsed updates before command acceptance. Do not start
  event collection only at the first accepted command and silently drop events
  after the initial frame. Attach baseline and event-stream initialization need
  an explicit future barrier design before transaction coding.
- Closing on death cannot then deliver a later oracle event on that connection.
  Such a disconnect is strictly an infrastructure fault; there is no promised
  death transition or later recovery of it. Death reason/terminal short-step
  semantics remain unresolved; do not add a reason or infer death yet.
- Counting any one input-hook invocation per frame does not establish both
  movement and shooting application, nor engine consumption. Separate dimensions,
  neutral actions and duplicate hook calls need a callback-coverage contract and
  real probes. No applied-input claim is approved by this report.
- At 30 updates/s, 15 updates exceed 250 ms. Keep all existing limits; do not
  claim repeat <=6 guarantees completion under load. Actual behavior is measured.
- Event count N=32 alone does not bound encoded memory/bytes. The eventual queue
  needs explicit record/count/total-byte budgets, overflow close and a completion
  reserve. Single pending transaction and no unbounded history remain required.
- Do not retain a misleading 0.4.0 version in modified deployable source. Any
  eventual Lua behavior change must have accurate artifact versioning before
  deployment; installed 0.4.0 is unchanged until reviewed deployment is authorized.
- A separate log-only mod is an option, not a new mandatory approval prerequisite.
  Prefer minimal bounded instrumentation of reviewed artifacts where feasible.
  Standing ordinary-profile observation/action permissions remain; current-instance
  checks and reviewed closed-game deployment still apply. No game is touched here.

Next coding task: watermark models/helper only, no native sender or Lua changes.
Native transaction, event attach baseline and callback ordering stay unfinished.


Primary specification validation: the first strict run rejected the expanded
oracle requirement for length (>500 characters). The watermark behavior was
split into its own requirement and scenarios, preserving the original oracle
scenarios. A new strict all-items validation passed 24/24 after this repair.
