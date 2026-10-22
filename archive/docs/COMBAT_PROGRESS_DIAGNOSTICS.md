# Combat endpoint diagnostics

Status: offline contract plus native endpoint/progress-stop evidence from the
2026-10-21 frozen Continue diagnostic.563 pairs/1800updates/60.190s combat validated
capture and cleanup;the guard stopped before the full five-minute duration.
Full duration qualification remains incomplete. No new native run or training is
authorized by this document. The stopped model t21760 and its parents are preserved.
See [native evidence](../reports/2026-10-21-native-combat-progress-diagnostic.md).

Both `live` and `session_runner` accept explicit opt-in settings:

| Option | Meaning | Default |
| --- | --- | --- |
| `--combat-trace-bytes N` | Combined policy/oracle JSONL cap, integer 1..268435456 | 0, disabled |
| `--combat-progress-updates N` | Observed combat game updates without endpoint-registered damage/clear, integer 1..108000 | Omitted, disabled |

`live` requires `--combat-gate` for either setting. The finite runner always uses
that gate and records settings in its session plan. A window of 1800 updates is
roughly 60 seconds at 30 game logic updates/second, not a wall-time lease. It counts
only captured same-visit combat action spans. Management waits, reset frame gaps
and navigation add no exposure. Software episode resets in the same native visit
do not renew the accumulated window. A new session/epoch/visit starts a new window.
Existing wall-time, disk, focus, fault, checkpoint and cleanup guards still apply.

## Evidence files

Per-session `combat_gate/diagnostics/policy.jsonl` contains version-1 records:
paired before/after encoder vectors, frame/session/epoch/visit identity, clipping,
overflow, selected move/shoot action, withheld-action/fault labels and transition
flags. The vectors are explicitly **before VecNormalize**. They are not the
network's normalized inputs, recurrent states, action probabilities or acceptance
acknowledgements. The backend can drain newer snapshots before sending an action.

The separate `oracle.jsonl` contains matching record IDs and full raw snapshots,
including enemy HP and geometry. Never feed this file to the policy/normalizer.
Weapon range is explicitly `null`/`not_exported`: policy v1 does not receive it.
These streams capture gated endpoints only; they do not claim complete damage,
kill or terminal coverage, nor the provenance/matched starts required by
[gameplay comparison](GAMEPLAY_COMPARISON.md). There is no automatic conversion
into accepted comparison evidence.

Files are exclusively created, never overwritten. Combined encoded bytes are
checked before writing a pair. If the next pair cannot fit, that transition is
explicitly uncaptured, input is released and a clean stop is armed before another
action/reset. Evidence is incomplete. An I/O failure stops the run; trailing
unpaired records must not be treated as valid evidence. Raw traces stay local.

## Registered-progress stop

The monitor reuses conservative HP-floor derivation at captured endpoints.
Continuous observed HP loss below the historical floor or an observed clear
resets its counter. Healing, disappearance/reappearance, software reset spawn
baselines, empty shooting and movement alone do not. Overflow/gaps can obscure
real damage. No enemy disappearance is promoted to a kill.

Expiry is a distinct `CombatDiagnosticStop` and an `early_stop` in the finite
runner, not a death, clear, infrastructure fault or completed-duration experiment.
The stop message says actual damage is unknown. The gate returns the last real
step, releases input and refuses the next action/reset. SB3's immediate auto-reset
can raise before storing that final sample: existing rollout accounting reports
all counted decisions versus checkpointed and unsaved steps. No fresh model,
New Run or automatic lease renewal follows the stop.

## Next learning change

1. Qualify this capture in a separately bounded five-minute native experiment,
   checking source/lineage, frame/vector binding, trace limits and owned cleanup.
2. Export verified weapon range/weapon type and version policy observations. Do
   not reinterpret t21760 or silently mix its normalizer with a changed schema.
3. Test a bounded progress-to-firing-position reward that accounts for reachable
   geometry and weapon behavior. Mere proximity is insufficient. Standing in
   range, empty shooting and approach/retreat loops must not accumulate reward.
   Retain damage penalties; they alone do not establish learned dodging.
4. Verify a native kill signal before enabling kill credit; current disappearance
   and `enemy_spawned.amount` (maximum HP) cannot establish a kill/current HP.
5. Compare actual HP removed, damage taken and verified clears over comparable
   starts/budgets, retaining unknown outcomes and failed attempts. Advance duration
   only after evidence: 5 minutes, 15-30 minutes, 1 hour, then a new 4-hour request.

Reward coefficients, optimizer updates and corner occupancy are diagnostics, not
proof of improved play. Management room traversal remains outside the combat
learner; a combat reward alone cannot teach that separate navigation layer.
