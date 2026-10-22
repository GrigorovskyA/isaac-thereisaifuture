# Evidence: exposed-start-curriculum planning

- Date: 2026-10-22, Europe/Amsterdam; base 743a65523f072b75b5f123f87f78c073095b5159.
- Scope: proposal, design, two existing-capability delta specs and nine unchecked
  implementation/acceptance tasks. OpenSpec propose workflow; planning only.
- Game/Python execution and configuration changes: not applicable to this milestone.
- Planned budget: 300 seconds total, up to 180 seconds learning, protected t26368
  parent, separate child, zero restarts/New Run; all phase caps are in the design.

## Results

| Check | Command/scenario | Exit | Status | Evidence |
|---|---|---:|---|---|
| Project/spec context | OpenSpec context, capability inventory and relevant full specs | 0 | passed | Existing combat-experience-gate, live-training-loop and rl-evaluation contracts read |
| Proposal completeness | OpenSpec status and instructions apply | 0 | passed | Planning complete; apply ready; 0/9 implementation tasks |
| Strict validation | scripts/OpenSpec.ps1 validate --all --strict | 0 | passed | 56 items, zero failures |
| Code/full quality gate | Not invoked for planning-only artifacts | — | not_run | No source/config/dependency changes |
| Native curriculum/evaluation | Not invoked | — | not_run | No new game, approval, model or training writes |

## Real game and RL evaluation

No runtime occurred during planning. The prior scripted positive control remains
the only new damage qualification; it is not learned-policy improvement. The
proposal requires actual learner damage, a completed update and reloaded child,
plus per-phase native metrics. Continue-only comparison is explicitly observational;
unavailable frozen phases cannot be replaced with resets or fresh models.

## Limitations and continuation

Self-reviewed planning against current source: trainer closure ends the client,
so phase reconnect must be explicit; event derivation can baseline a wounded target
without crediting prior damage; setup must precede normalization/rollout/reward.
Implementation, offline integration checks and all native tasks are unfinished.
Next: apply [the design](../openspec/changes/exposed-start-curriculum/design.md),
then freeze the exact finite assignment. No archive or training authorization is
created merely by completing planning artifacts.
