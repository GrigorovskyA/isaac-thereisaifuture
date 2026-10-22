# Evidence: native-timing-followup-02

- Date/time and timezone: 2026-10-17, Mac executor (report-only, offline)
- Git revision and dirty status: on top of bfffc70; this report is the only new file
- Change scope and acceptance criteria: separate measured facts, inferences and
  unknowns from the public timing evidence; propose ONE facts-only next slice, pending
  primary approval. No code, spec, design, task, STATUS, or installed-file edits.
- Game/mod/bridge versions: observer 0.4.1-dev installed default-off, hashes match source
  (`reports/2026-10-17-callback-trace-runtime.md`)
- Python/package versions and configuration hash: not applicable
- Scenario, split, seeds, budget, and stop conditions: not applicable (no run)

## Inputs inspected

Public evidence: `reports/2026-10-17-callback-trace-runtime.md` ("Observed callback
ordering"). Source: `mod/observer/main.lua` `release` 87-92, `action_guard` 106-127,
hold creation in `command` ~414-417, `MC_POST_RENDER`/`MC_POST_UPDATE` 571-583,
`MC_INPUT_ACTION` 643-668. Contracts: `native_protocol.py` `StepCompletion` 43-79;
`reports/2026-10-17-native-lua-plan.md` (assumptions A1/A2). No raw logs read.

## 1. Measured facts (accepted)

From the public trace of one pulse (IDs as in that report):
- Accepted at frame 397270 / update counter 1399 (IDs 1-2); hold `until_frame` 397272;
  released with reason `expiry` at frame 397272 / counter 1400 (ID 47); the next
  post-update 1401 was logged at frame 397272 (IDs 48-49).
- Three input-query groups of 12 records (8 `GET_ACTION_VALUE`, 4 `IS_ACTION_PRESSED`),
  36 total: IDs 3-14 (frame 397270, counter 1399), 17-28 (frame 397271, counter 1399),
  33-44 (frame 397271, counter 1400). They cover two frame IDs; no
  `IS_ACTION_TRIGGERED`. Left returned 1.0; the other values were zero/false.
- One `update_enter/exit` pair (IDs 29-30, counter 1400, frame 397271) lies between
  acceptance and release.
- Counter and frame advance together in the sample (1399/1400/1401/1405/1411 at frames
  397270/71/72/76/82).
- Position moved 312.89 to 300.45 by frame 397282, then 299.65 and stationary; health
  unchanged.

## 2. Inferences and unknowns

- Hook ordering is established: the first group follows post-update 1399, the second
  precedes post-update 1400, and the third follows it.
- **Unknown:** which code path queried or consumed any group, how many simulation updates
  consumed the left input (no numeric bound is claimed, neither one nor two), whether the
  accepted frame's own update had already run (A2), and behavior under pause, death,
  revival, transitions, and events. The trace proves hook ordering and values only.
- Displacement and the later stationary state do not identify consumed queries.
- Unique hook frame IDs, raw query counts, and post-update counts are not completed
  simulation actions.

## 3. Contract note

`StepCompletion` validates necessary consistency constraints for a claimed `completed`
receipt (identity match, game-API frame provenance, `elapsed_updates` equal to the frame
delta, status/reason coherence). It does not establish that the hold lived the whole
interval or that the game applied input, and a frame delta alone is not sufficient for
completion. Completed is not redefined more weakly here. No success classification,
receipt emission, or protocol advertisement is proposed, and nothing may be emitted on
legacy action streams. Whatever event-recording baseline attaches before command
acceptance stays unresolved; recording at the first accepted step was rejected because
it drops events between the initial policy baseline and acceptance.

## 4. Proposed next slice (pending primary approval)

A PASSIVE, bounded, facts-only Lua ledger in a separate unshipped module, for example
`mod/experimental/native_step_ledger.lua`. `main.lua`, installed hashes, and legacy
streams stay untouched. The module sends nothing, calls no engine API, grants no input
authority, labels nothing completed or applied, and is not a GameBackend.

Proposed API (plain Lua table, caller supplies all values):
- `Ledger.new(sequence, accepted_frame, requested_frames)` rejects `requested_frames`
  outside 1..15 and stores a fixed-size buffer of at most 15 frame slots.
- `ledger:observe_query(frame, update_counter, hook, button, value)` records
  per-frame, per-cardinal-button hook exposure counts and the returned value; frames
  outside the buffer window are counted as `dropped`, never grown.
- `ledger:observe_post_update(frame, update_counter)` records post-update observations
  in order.
- `ledger:close(reason, frame, update_counter)` stores the exact release cause once;
  later calls are ignored.
- `ledger:snapshot()` returns a detached copy: observations only (exposure per frame
  and button, post-update list, release cause, dropped count). Query coverage is
  reported as observation, never consumption.

Offline tests (`tests/test_lua_native_step_ledger.py`, lupa, loading the module alone):
duplicate queries before and after a post-update in the same frame; queries at several
frames; expiry before any post-update; no queries; neutral values recorded as
observations; frames beyond the 15-slot buffer counted as dropped; repeated `close`
keeps the first cause; invalid `requested_frames` rejected; the module has no
dependency on `Isaac`, `Game`, or sockets.

Production integration, classification, and protocol use need their own frozen
contract and probes; the existing hold expiry (<=15 frames / 250 ms), heartbeat 500 ms,
and nonrenewable 120 s lease must not be extended to produce a requested repeat.

## Results

| Check/requirement | Command/scenario | Exit code | Status | Evidence |
|---|---|---|---|---|
| Public evidence and source inspection | reading only | - | passed | cited above |
| Proposed ledger code/tests | - | - | not_run | pending primary approval; no code authorized |
| Runtime, Check.ps1 | - | - | not_run | report-only; baseline stays 746 passed |

## Real game

Not run; no raw logs or private data read.

## Limitations and continuation

Facts rest on one pulse and the public table; IDs not described there are unused.
Next action: primary review, then a separate approved coding task for the ledger.


## Primary review and coding decision

Revision 02 accepts the measured facts and withdraws the unsupported consumed-
update bound, one-query completion threshold and first-command event baseline.
The ledger proposal is approved only with the frozen refinement in active
 design.md: <=15 query-frame slots, <=16 post-update frame slots (including the
expiry endpoint), fixed hook/button cells and capped scalar counters; no growing
post-update list or value history. Snapshot is a detached deep copy, not a claim
of immutable Lua tables. Release is recorded once; bounded endpoint post-update
observations remain possible after release. Nothing classifies applied/completed.

The first query group's counter 1399 is a recorded source counter; do not infer
untraced engine consumption. Ordering around recorded IDs 29-30 is direct evidence.
No additional run or private log access occurred. Current code baseline remains
746 passed/no skips; this documentation-only batch passes strict OpenSpec 24/24.
The next standalone module is unshipped and cannot alter installed source hashes,
transport, authority, hold expiry or legacy modes. Tasks 3.6/3.8 remain incomplete.
