## 1. Contract

- [x] 1.1 Proposal, design (state machine, eligibility, handshake, budgets), delta spec
- [x] 1.2 Strict OpenSpec validation before implementation

## 2. Implementation

- [x] 2.1 `combat_gate.py`: classifier, request/ack models, `CombatGateEnv`, ack writer
- [x] 2.2 `LiveBackend.poll`/`latest` (read-only, command-free) in `live.py`
- [x] 2.3 Opt-in `LiveRunOptions.combat_gate`/`gate_wait_minutes`; random/train wiring;
      unsaved partial-rollout reporting
- [x] 2.4 CLI: `live --combat-gate --gate-wait-minutes`, `combat-ready --session-dir`

## 3. Verification (offline)

- [x] 3.1 Behavioral tests in `tests/test_combat_gate.py` (see report mapping)
- [x] 3.2 Real synthetic RecurrentPPO update and checkpoint across several handoffs
- [x] 3.3 Ruff, format, mypy, full pytest, strict OpenSpec (macOS precheck)
- [x] 3.4 Docs: `docs/COMBAT_EXPERIENCE_GATE.md`, optional section in `docs/LIVE_LOOP.md`
- [x] 3.5 Evidence report and self-review

## 4. Primary review feedback 1

- [x] 4.1 Maintain eligibility during combat: backend veto before each action on fresh
      queued state, post-step classification, truncation with gate exit, no fabrication
- [x] 4.2 Narrow the run deadline to the handoff cap through wait, reconnect and resume
      reset; recheck on return; restore afterwards
- [x] 4.3 Readiness freshness after disconnects and observation gaps
- [x] 4.4 Fake-clock/no-sleep tests, mutation check, docs, spec and report update

## 5. Primary-owned (pending)

- [x] 5.1 Windows `./scripts/Check.ps1` (primary re-review: 1362 passed, zero skips; strict 28/28)
- [x] 5.2 Bounded real-game gated run on file 2 with recorded handoffs and exposure (random policy; timeout, fresh readiness, enemy defeat, empty/clear handoff, no further actions, deadline cleanup)
