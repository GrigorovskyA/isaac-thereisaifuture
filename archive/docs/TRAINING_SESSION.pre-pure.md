# Finite training session runner

Readiness item 1 has an offline implementation in
`python -m isaac_threrisaifuture.session_runner`. It is not yet natively qualified.
The stopped overnight experiment and its old local launch assignments stay closed.
Do not launch training until a new finite native plan is requested and recorded.

The explicit CLI requires `--game`, `--game-log`, `--config`, `--run-root`, a new
`--output` directory, exact `--parent-id`, `--seed`, `--seconds` and `--disk-bytes`.
For a duration-governed run choose `--time-budget-only` and omit `--steps` and
`--max-restarts`. Diagnostic mode still requires both explicit count limits. `--navigation-scale` is optional
(1..5, default 1). Optional `--navigation-time-dominant` requires scale 1 and
uses the fixed session window for observed exploration; see COMBAT_NAVIGATION.md.
Use `--help` to inspect it without launching anything.
Supply the exact latest compatible checkpoint; there is no fresh-model fallback.
The runner always uses guarded Steam / Continue on file 2 and requires active
Isaac. It cannot select New Run or replace a saved run. Zero infrastructure faults,
one launch, no retry, existing action guards are retained. Diagnostic navigation
limits remain the default; the explicit time-dominant mode retains only local
safety guards and the global deadline, with observed no-progress stops.

One deadline is fixed before preflight. Startup, menu entry and model loading
consume that window. The deadline is aligned down to a whole Unix second (less
than one second of quantization) because Lua leases require integral expiry.
The original paired wall/monotonic sample maps the nonrenewed lease to the same
deadline. A long startup can refuse the lease; it cannot add time. Existing shorter
configuration limits also apply. Cleanup has a separate bounded grace: worker
15 seconds plus at most 5 seconds after termination, normal game close 12 seconds.
An uncooperative worker is a fault; the game is never force-killed.

`plan.json` records limits, fixed clocks, config hash, parent identity and frozen
source/parent hashes. `events.jsonl` is worker telemetry, `console.txt` preserves
worker errors, and `menu.jsonl` records guarded menu actions. `status.json` is an
atomic current snapshot; `result.json` is the terminal result. Optional
`metrics.json` cannot overwrite a final status if its export fails. These artifacts
are private local output and must not be committed.

Status phases are `startup`, `waiting`, `combat_learning`, `navigation` and
`checkpointing`. Combat collection is observed from actual gate decisions; saving
is separate. A live process alone yields no learning claim. Five seconds without
new activity changes an active phase to `waiting`. Phase durations measure the
last observed activity with that freshness bound, not continuous gameplay utility.
Check `updated_at` and `last_activity_monotonic`: if the supervisor itself dies,
the old snapshot remains historical and cannot establish current activity.

The snapshot retains cumulative combat decisions, the last independently readable
completed checkpoint and its update timestamp. A concurrent checkpoint read failure
retains the prior identity with `checkpoint_note`. The initial parent is not a new
update. These counts do not establish better damage, survival or room clears;
comparable evaluation remains readiness item 4.

Terminal states are `early_stop`, `completed`, `fault` and `user_cancelled`.
Completion requires cooperative wall-time stop evidence and the fixed deadline;
zero exit or elapsed uptime alone is insufficient. A clean navigation or timestep
stop before the deadline is `early_stop`, with the actual reason. Cleanup errors
make the result a fault even after cancellation.

Ctrl+C or creation of `<output>/stop.request` requests cancellation. The menu log
reader checks that signal before more menu input; the live backend checks it before
actions and during handoffs. Environment cleanup releases input. The parent then
normally closes only its verified new game window, removes only its unchanged
approval, and restores thread sleep behavior. A replaced approval is preserved and
reported as a cleanup fault. There is no automatic relaunch or lease renewal.

Remaining acceptance: separately declared five-minute native pilot with checkpoint
readback and manual/timer stop cleanup. Explicit finite-window navigation and
observed no-progress stops now have offline contracts; native travel remains
pending. Interrupted-save publication and strict continuation now have
[offline storage evidence](CHECKPOINT_STORAGE.md), including final readback if a
publication event is lost. Matched policy evaluation and longer stages remain
later readiness work. Do not treat offline checks as native acceptance.

## Duration-governed count limits

The native five-minute pilot on2026-10-21 exposed a too-small diagnostic restart
cap: three deaths exhausted two restarts and left the remainder waiting, although
one256-step update was saved. This did not constitute thirty minutes of learning.

The user requested removing practical death/step stops for long runs. Explicit
`--time-budget-only` supports60seconds through4hours, derives cumulative step
sentinel1billion and restart sentinel5000, and enables time-dominant navigation.
These are finite protocol fields, not literal infinity: at least4seconds between
native restarts permits fewer than3601 restarts in4hours; even30 decisions/second
cannot approach1billion steps from current lineage. Counts cannot practically bind
this window. A larger than4hour request is refused in this mode because the
existing5000 schema ceiling would no longer have that guarantee over all windows.

The configuration must already allow1billion total steps and at least the chosen
wall window. Smaller ceilings fail before approvals/game; no silent migration,
normalizer reset or fresh policy is permitted. Existing conservative-v2 overnight
config qualifies unchanged; this does not revive its cancelled experiment.
plan.json records nonbinding_schema_sentinels and all effective numeric limits.

The fixed deadline, zero infrastructure-fault tolerance, disk/focus/transport,
lineage and owned-cleanup guards remain. Exhausted/unreachable ordinary navigation
can still stop early, because waiting or circling is not learning. Death restarts
are ordinary game lifecycle, not permission to replace an existing saved run.
No new runtime or New Run is implied by adding the mode. Sustained native evidence
for this mode remains pending. Never renew a lease merely to remove an active cap.

## Windows status readers and current native limitation

Atomic JSON replacement retries Windows errors5/32/33 for at most1s with10ms
pacing,keeping prior complete status visible. Persistent/unrelated failures still
fault. This addresses the initial hour-attempt status failure;actual root-cause
handle attribution remains unknown. Offline held-reader regression and full2198
tests passed;corrective21min live continuation ended by user cancellation with
clean release and no repeat status fault. No one-hour timer completion claim.

Active combat collection is not a no-progress detector. The stopped capture showed
prolonged positional stagnation while policy updates continued. Repeated software
timeout/unknown episodes in one unchanged room do not establish diverse experience.
See the2026-10-21 one-hour stopped-analysis report;do not resume merely because
checkpoints continue to advance.
