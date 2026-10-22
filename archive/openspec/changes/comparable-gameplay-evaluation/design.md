# Design

## Contract

An offline manifest declares policies, cases and attempts before analysis. Cases
identify split, native seed, room shape/enemies, character/build, entry history and
common decision/wall budgets. An attempt references one normalized raw JSON trace
with SHA256, declared case/policy/repeat and assistance/control provenance. Strict
bounded parsing rejects malformed data, changed hashes and duplicate cells. Missing
cells remain in reports and block paired comparison. No trace discovery or latest
checkpoint lookup. Checkpoint identity includes model/normalizer/config hashes,
training seed and explicit directory ID; controls carry a versioned source hash.

## Raw accounting

Samples contain only raw observed HP/flags/identity, elapsed time, decisions and
phase. Adjacent monotone frames within declared maximum gap and one visit support
HP differences. Enemy identity includes spawn generation; only continuous active
entities count novel HP loss below their observed minimum. Healing, missing IDs,
phase changes, overflow and gaps cannot invent damage or kills. Player HP loss is
observed adjacent decreases in half-hearts, without assigning enemy/self causation.
A clear requires an observed false-to-true flag in an initially occupied encounter.
Death flags are separate. Empty starts, gaps, overflow or unknown phases censor
negative outcomes. Software stops are censored, never deaths or successful clears.
Time deltas belong to the preceding observed phase; no duration is extrapolated.

## Comparison

All attempts, including faults, are retained with exposure and raw provenance.
The report shows verified-clear counts / all attempts plus a separate known-outcome
clear denominator and Wilson interval. Damage is explicitly a sampled lower bound;
missing coverage remains visible. No aggregate winner or learning claim is emitted.
Paired per-cell differences (candidate minus declared reference) are descriptive
only and require the full expected matrix, native source, verified matching start,
unassisted single control, unchanged policy evidence, equal realized trace contracts
and zero infrastructure faults. Actual initial health, positions and enemy
type/HP/phase must match across policies, independently of matching metadata. A matched report is not native acceptance or a
multi-training-seed generalization claim. Synthetic fixtures always remain synthetic.

## Limits

No existing live log is silently upgraded to this contract. The normalized raw
trace exporter/matched native start still needs a separately requested pilot and
review of raw-log provenance. Hashes detect mutation, not fabricated metadata.
Wall stationary data unavailable in the normalized contract remains unavailable.
Existing offline training evaluator and live pilot are unchanged.
