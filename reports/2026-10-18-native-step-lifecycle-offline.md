# Evidence: native-step-lifecycle-20261018-01 (offline reducer, subtask 3.9)

Current disposition: accepted for the pure offline slice after primary Windows
review and corrections below. Executor results are historical and do not replace
the pinned Windows gate. No engine adapter, runtime acceptance or archive.

- Date/time and timezone: 2026-10-18, Europe/Berlin (executor on macOS via SMB share).
- Git revision and dirty status: HEAD d73792c; dirty (this task's files plus untracked errors.txt).
- Change scope: active change `episode-lifecycle`, offline subtask 3.9, unchecked pending primary acceptance (checklist 13/20 now, 13/21 once counted).
- Game/mod/bridge versions: not applicable. Observer 0.4.5-dev and every existing client/receipt/action behavior are unchanged. No game was launched, attached or controlled.
- Python/package versions: no changes. Ad hoc executor runs used Python 3.11.15, pydantic 2.11.3, pytest 7.1.3 (not the pinned Windows 3.12 environment).
- Scenario/seeds/budget: fabricated typed facts only; no randomness.

## Baseline and changed files

New: `src/isaac_threrisaifuture/native_step_lifecycle.py`, `tests/test_native_step_lifecycle.py`, this report.
Edited: `openspec/changes/episode-lifecycle/{proposal,design,tasks}.md`, `specs/episode-lifecycle/spec.md` (design, spec and task 3.9 were written BEFORE the code), `docs/NATIVE_EPISODE_PROTOCOL.md`, `docs/STATUS.md`, `ROADMAP.md`, `subagent_report.md`, `agent-status.json`.
No existing Python module, Lua file, metadata, script or dependency file was touched.

## Contract (summary; full text in design.md "Native step lifecycle reducer")

One `NativeStepLifecycle(command, baseline_last_event_id, started_ms, deadline_ms)` per StepCommand; `submit(fact)` returns an immutable `StepDecision`. Facts: Acceptance, Interval, Release, Seal, Interrupt, ContextChange, Clock; scalars are strict `int` 0..2**53-1 (no bool), session ids 32 lowercase hex, kinds from closed sets, all validated at construction.

States: waiting, ready, cancelled, expired, faulted, unsupported_terminal (all but waiting absorbing). READY needs acceptance (frame within command..+15), exact full interval (`end-accepted == elapsed == requested == command.frames`), release at a frame >= endpoint, and a same-context seal whose end equals the interval end and whose watermark >= the baseline, in any arrival order. The candidate is local, unserialized and labelled `local_reducer_unverified`.

Precedence per submission: (1) terminal state kept, only a valid late release clears `release_required`, a conflicting fact after READY sets `conflict_after_ready`; (2) 65th counted fact faults; (3) unknown type or time regression faults; (4) `at_ms >= deadline_ms` expires (deadline wins every tie; the fact is applied only as a valid release); (5) identical duplicate (ignoring `at_ms`) is ignored but counted; (6) foreign/stale/contradictory/partial-interval/watermark-regression faults; (7) interrupts and context changes map to cancelled (pause, input_fault, explicit_release, transition), unsupported_terminal (death_candidate, epoch_change), expired (authority_lost) or faulted (disconnect, transport_fault, session_changed); (8) otherwise store and test readiness. The deadline must satisfy `started < deadline <= started + 250` ms and is never renewed. At most 64 facts; no history beyond fixed scalars and one fact per kind.

Mapping to the wire: cancellation reasons reuse pause/input_fault/explicit_release/transition and expiry reuses wall_deadline; the reducer emits no wire message. READY is not a StepCompletion, not a delivered outbox transaction and not proof of physical input.

## Results

| Check/requirement | Command/scenario | Exit code | Status | Evidence |
|---|---|---|---|---|
| Reducer behavior | `PYTHONPATH=src:tests python3.11 -m pytest tests/test_native_step_lifecycle.py` on a /tmp copy (see note) | 0 | passed (ad hoc, Mac) | 128 passed |
| Existing native suites unchanged | same copy: test_native_protocol/receipts/receipt_reader/client/outbox plus reducer | 0 | passed (ad hoc, Mac) | 369 passed, 0 skipped |
| Pinned Windows pytest, `Check.ps1` | not run | n/a | not_run | no PowerShell/.venv on Mac |
| Ruff lint/format, strict mypy | not run | n/a | not_run | tools not installed on Mac; line length checked manually (<=100); the Windows gate must confirm formatting and strict typing |
| `OpenSpec.ps1 validate --all --strict` | `node` on a /tmp copy | 1 | blocked | `node_modules/@fission-ai/openspec` cannot be copied or opened from the SMB share (Operation not permitted); design/spec/task text is therefore NOT strict-validated before coding |
| Game checks | none | n/a | not_run | no game access |

Note: the ad hoc copy lived in /tmp and replaced one PEP 695 generic (`decode[T: WireModel]`) with a plain signature because the Mac interpreter is 3.11. This was never applied to the repository. These passes are not the pinned-environment acceptance.

## Tests (behavior)

128 cases with fabricated facts: acceptance/clock alone never complete; five arrival orders and every single missing prerequisite; repeat 1 and 15; zero/short/long/skipped/regressing intervals; wrong session/sequence/epoch/room, stale and over-window frames, watermark regression; strict scalar and enum bounds at construction; contradictory evidence in nine arrival orders; duplicates counted but ignored, no second READY; every interrupt kind at four progress points; context changes and implausible ones; release-required semantics, late valid/invalid release after every terminal kind; deadline tie for each completing fact, one millisecond before the deadline, expiry before/at/after the endpoint; no authority extension or renewal; READY then conflicting fact flagged not unpublished; 64/65 limit, overflow and fault absorbing against replay and foreign-session facts; frozen, detached output without event/reward/receipt/serialization surface. Existing receipt/client/outbox suites are unmodified and still pass.

## Requirement mapping

Spec requirements "Native step readiness is a bounded local decision" and "Native step outcomes fail closed and stay absorbing" are covered by the scenarios above (readiness, missing evidence, 64-fact limit, interrupts, late release, deadline tie).

## Real adapter: evidence still missing

The installed observer provides none of: a per-update counter proving consumed engine updates (input queries repeat around post-update), a neutral-release confirmation fact (only heartbeat/disconnect cleanup exists), a sealed endpoint with a complete watermark (the outbox has no engine emitter), or ordering facts for pause/death/transition. Live HP shows the first post-update can still hold old HP and later raw HP is not an event barrier. Until these exist, a non-synthetic READY is impossible.

## Self-review and limitations

- Ordering is submission order only; the reducer assumes no engine ordering. A fact conflicting with READY after emission cannot unpublish it and only sets `conflict_after_ready`; the future sender must check it before use.
- The 250 ms ceiling is conservative and also bounds the seal wait; real timing may need an explicit, reviewed value.
- Any interrupt while waiting terminates the step regardless of its frame; floor_change allows an unchanged room_visit because the room counter behavior on floor change is unverified.
- Process deviation: new/edited text files were written with small Python/heredoc scripts instead of the edit tool for docs and OpenSpec appends (content verified by diff; no line-ending churn). Unit tests were not mirrored from implementation internals but a few assert on reasons chosen here.
- Strict OpenSpec validation could not precede coding; Windows must run it, and also ruff format/lint and mypy, before acceptance. Nothing was committed, pushed or archived. No successor work was started.

## Next runtime prerequisites

Define engine-side facts for consumed interval, release confirmation, sealed endpoint with watermark and pause/death/transition ordering; verify them in an authorized bounded probe before wiring any sender, then reconsider partial/terminal receipts in a separate change.

## Primary Windows review and corrections

Primary review used task native-step-lifecycle-20261018-01 and baseline d73792c.
Initial pinned tests reproduced the executor's 128 reducer / 369 combined native
passes. Strict OpenSpec passed 24/24 and mypy accepted 38 sources; Ruff found one
import-order violation. That was fixed and the two new files were formatted.

Review then added twelve regression cases, all failing on the submitted code:

- A release at frame 101 incorrectly satisfied cleanup after an interruption at
  104; even a late release below the stop frame cleared cleanup. A release floor
  now tracks validated accepted/interval/interruption progress.
- Terminal clocks did not advance timestamp validation, allowing regressing
  cleanup. All typed terminal facts now maintain the monotonic time boundary.
- The evidence counter grew without bound, and overflow made later cleanup
  impossible. The internal counter now saturates at 65; after overflow, only
  constant-size cleanup/time validation or provisional-candidate invalidation
  remains available. No further completion evidence or authority is accepted.
- Transport/disconnect/authority failures after the interval endpoint left the
  READY candidate apparently usable before delivery. Malformed/regressing/foreign
  facts also escaped invalidation. Conflicts are now sticky and future snapshots
  withhold candidates; prior immutable snapshots cannot be recalled and remain
  explicitly provisional. No delivery authority is granted by this module.
- New epoch/session frame zero was misclassified as an old-context stale frame.
  Context identity is now checked before comparing frame counters; new epochs/
  sessions can reset their frame identity without attaching it to the old command.

Ten follow-up cases cover cleanup after further interruption, READY budget
exhaustion and all four context changes invalidating prior cleanup confirmation
both before and after READY.
Existing positive/replay/ordering cases remain covered; one original READY test
was strengthened to require withholding the candidate after any interruption.
Spec/design/protocol now state the reviewed behavior explicitly, including late
cleanup after evidence exhaustion. No existing receipt/client behavior changed.

| Final requirement/check | Command/scenario | Exit code | Status | Evidence |
|---|---|---|---|---|
| Reducer cases | .venv/Scripts/python.exe -m pytest tests/test_native_step_lifecycle.py -q | 0 | passed | 150 cases, fabricated typed facts only |
| Targeted native compatibility | .venv/Scripts/python.exe -m pytest tests/test_native_step_lifecycle.py tests/test_native_protocol.py tests/test_native_receipts.py tests/test_native_receipt_reader.py tests/test_native_client.py tests/test_native_outbox.py -q | 0 | passed | 391 cases, zero skips |
| Full Windows gate | ./scripts/Check.ps1 with environment below | 0 | passed | 1133 tests, zero skips; Ruff, 86 formatted files, strict mypy 38 sources, pip consistency, OpenSpec strict 24/24 |
| Final strict validation | ./scripts/OpenSpec.ps1 validate --all --strict | 0 | passed | 24/24 after final evidence/spec review |
| Diff review | git diff --check and actual file allowlist review | 0 | passed | No unrelated changes, existing Python modules/Lua untouched |
| Real native step | No game launch, attach, control, deployment or training | N/A | not_run | Adapter facts and runtime acceptance still missing |

```powershell
$env:PYTHONPATH='C:\Users\<user>\Documents\Codex\2026-10-17\work-on-isaac-threrisaifuture-in-the\work\lua-test-runtime'
$env:ISAAC_JSON_LUA='C:\Program Files (x86)\Steam\steamapps\common\The Binding of Isaac Rebirth\resources\scripts\json.lua'
$env:TMP=Join-Path (Get-Location) 'reports\local\check-native-protocol'
$env:TEMP=$env:TMP
.\scripts\Check.ps1
```

### Verification scope

| Dimension | Finding |
|---|---|
| Completeness | Offline 3.9 accepted; original tasks stay 12/19 plus offline 3.9/4.4, current checklist 14/21. Seven whole-change tasks remain unfinished. |
| Correctness | Two readiness/outcome requirements with nine scenarios map to reducer, ordering, capacity, interruption, cleanup, tie and new regression cases. All facts are fabricated; engine correctness is not verified. |
| Coherence | One copied command context, fixed-size typed state, 250 ms deadline ceiling, saturating evidence budget and immutable local-only outputs; existing wire/client/outbox contracts preserved. |

This is primary-agent review and testing, not independent review. The current
module cannot execute a step, prove neutral input or prove a sealed engine event
stream. No runtime task was checked off, no partial/terminal receipt acceptance
was enabled and no deadline/lease/restart limit was relaxed. Source observer and
installed 0.4.5-dev were not modified. errors.txt and private agent-status.json
remain excluded. The executor assignment is closed; no successor or heartbeat.

Next work remains engine-side consumption/release evidence and conservative
ordering/commit semantics, followed by separately prepared bounded runtime
checks. Repeated episodes and start/reset additionally require training isolation
and specific authority. No archive, learning or progression claim is justified.
