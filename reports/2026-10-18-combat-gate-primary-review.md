# Evidence: combat experience gate primary Windows review

- Date: 2026-10-18, Europe/Amsterdam.
- Baseline: 548efbc plus matching executor changes; errors.txt preserved.
- Task: combat-experience-gate-20261018-01, ready_for_review.
- Scope: actual source/CLI integration, report/spec comparison and offline checks.
- Runtime: no game launch, connection, training, deployment or approval change.

## Results

| Check | Exit | Status | Evidence |
|---|---|---|---|
| Windows Check.ps1 | 0 | passed | 1344 tests, zero skips; Ruff, 97 formatted files, mypy 42 sources, pip and strict 28/28 |
| Empty state during active fight | 0 | failed | classify(latest)=empty, gate still combat_active, next step sends one extra action |
| Resume across handoff cap | 0 | failed | Cap .05 s; delayed inner reset .15 s; return combat_active at about .172 s |
| Real gate acceptance | — | not_run | No runtime attempt; code acceptance pending |

## Reproductions

Both use only the new test module's World, Operator and gated factory. First:
initialize one enemy, acknowledge initial combat, remove enemies with clear=false,
step once, then observe empty eligibility and call step again. The action count
increases despite the known ineligible snapshot. Second: acknowledge a fight
under a .05-second gate cap and wrap inner reset with a .15-second delay. The
gate activates after the cap instead of stopping. These demonstrate missing
behavioral coverage despite the passing suite.

The first reproduction command had a Python indentation typo and exited before
executing; the corrected command reproduced both findings. Private temporary
handoff files remain in reports/local/gate-review-* and are not uploaded.

## Review decision

Primary self-review, not independent review. Feedback 1 in subagent.md requires
ongoing fresh eligibility gating with preserved events/terminal accounting and
propagation of the smaller handoff/global deadline through resume/reconnect.
Readiness after disconnect gaps also needs fresh-state coverage. No requirement
or existing gate was weakened, no implementation commit/archive was made.
Next: corrected matching report and another Windows review before real control.

## Feedback 1 re-review: offline accepted

At the requested one-minute monitor check the executor status was freshly
ready_for_review, updated 2026-10-18T16:39:57Z, matching this task and the new
feedback-1 response. The temporary monitor was paused through the app automation
tool BEFORE source review/testing. No successor work or runtime work was started.

The actual backend veto, post-step classification, narrowed deadline holders,
readiness gap handling and new tests were inspected. Both original reproductions
were rerun against the new code with the synthetic World/Operator harness:

- Empty, clear=false now truncates; a subsequent step is refused and no extra
  action is sent.
- The delayed inner reset under a .05-second cap now raises CombatGateExpired;
  state is stopped and action count stays zero. Dedicated fake-clock regressions
  also check propagation through the blocking reconnect path, not only a
  post-return check.

Windows Check.ps1 exited 0: 1362 tests, zero skips, Ruff, 97 formatted files,
mypy 42 sources, pip consistency and strict OpenSpec 28/28. Existing modes and
synthetic short-fight RecurrentPPO update/checkpoint tests still pass.

This is primary self-review, not independent review. A queued action veto retains
one observed terminal/truncated transition sample even though the proposed action
was not executed; this is reported as withheld_actions and is NOT a wait sample.
Wait frames remain outside policy, rollout and normalization. If clear flags lag,
the conservative empty handoff can omit a clear bonus rather than fabricate it.
A queued pause/unavailable veto releases immediately but can wait for a newer
playable snapshot until the bounded backend/run deadline; no further action is
sent. These limitations remain documented; no exact engine-step claim is made.

Offline scope passes and executor authority is closed. Runtime task 5.2 remains
not_run, so the change is not archived. No game connection, new training, model
access, approval renewal, mod deployment or save/Cloud change occurred. Next:
separately authorized bounded game test with the operator present, covering
empty-room handoff, explicit readiness, battle end and release.
