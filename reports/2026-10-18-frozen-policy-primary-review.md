# Evidence: frozen-policy-evaluation primary Windows review

- Date: 2026-10-18, Europe/Amsterdam.
- Baseline: 4e11d78 plus uncommitted executor changes; errors.txt preserved.
- Matching task: frozen-policy-evaluation-20261018-01, ready_for_review.
- Scope: read executor report, actual new adapter/plan and training Monitor diff;
  run Windows gate and a targeted artifact-corruption reproduction.

## Results

| Check | Exit | Status | Evidence |
|---|---|---|---|
| Check.ps1 | 0 | passed | 1254 tests, zero skips; Ruff, formatting, mypy, pip, strict OpenSpec 26/26 |
| Existing real checkpoint through new adapter, offline only | 0 | passed | Valid action [2,0], verify_unchanged passed; original artifacts unchanged |
| Early rejection of corrupt normalizer | 0 | failed | Constructor accepted saved NaN mean in a private copied checkpoint |
| Runtime evaluation | — | not_run | No game attach/control, training or approval write |

The first attempt to reserialize a bare unpickled VecNormalize object failed
because class_attributes was absent. The successful reproduction used the
adapter's attached normalizer and VecNormalize.save on a private copied directory.
The original real checkpoint was never modified. Private copies stay in ignored
reports/local; no model/log data is committed.

## Review outcome

Implementation acceptance is pending. Feedback 1 in subagent.md requests early
validation of saved normalization statistics/scalars and behavioral regressions,
plus finite normalized-input checks before prediction. Existing passing checks
do not cover this corruption path. No specification or check was weakened.

The training Monitor fix is a small relevant correction with a regression, but
its inclusion does not close the larger combat-ppo-training acceptance tasks.
Executor report claims separate user authorization for those extra writes; this
review records the actual bounded diff rather than inferring runtime authority.

No implementation commit, archive or new performance claim was made. Next:
executor feedback correction and a fresh matching report, then primary review.

## Feedback 1 re-review: accepted offline

The fresh matching ready_for_review report was read. Actual validation helpers,
new behavioral tests and the unchanged Monitor correction were inspected.
Windows Check.ps1 exited 0: 1276 tests, zero skips, Ruff, 93 formatted files,
mypy 40 sources, pip consistency and pinned OpenSpec strict 26/26.

The original PRIVATE COPY used in the failing reproduction now raises
CheckpointError at construction: saved observation mean must be 649 finite
values. The real private smoke checkpoint still loads and produces [2,0] from
a fabricated zero vector offline; verify_unchanged passes. No private artifact
was uploaded or original checkpoint modified. No game connection was opened.

This is primary self-review, not independent review. Saved mean/variance shapes,
finite values, variance bounds, positive finite count/epsilon/clipping and finite
normalized input are now checked. Twenty-two added cases include zero-variance
compatibility and ensuring predict is not called on invalid normalized values.

Offline task acceptance passes; executor authority is closed. The model adapter,
plan and bounded Monitor fix are accepted. Real pilot/confirmatory tasks remain
blocked and unchecked; the OpenSpec change is left unarchived with those explicit
follow-ups. No combat-training milestone or policy improvement is accepted.
