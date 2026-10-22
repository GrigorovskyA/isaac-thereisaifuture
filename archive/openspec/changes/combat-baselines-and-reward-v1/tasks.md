## 1. Implementation (offline)

- [x] 1.1 Add `rewards.py` (coefficients loader, ledger, deduplication, HP cap).
- [x] 1.2 Write tests/test_rewards.py.
- [x] 1.3 Add `scenarios.py`, `baselines.py`, `evaluation.py` with tests/test_baselines.py and tests/test_evaluation.py (random and scripted baselines, fixed splits, evaluation report).

## 2. Checks (run on Windows)

- [ ] 2.1 Run the new tests.
- [ ] 2.2 `./scripts/OpenSpec.ps1 validate combat-baselines-and-reward-v1 --strict`.
- [ ] 2.3 `./scripts/Check.ps1` passes.

## 3. Real-game evidence (blocked)

- [ ] 3.1 Validate the ledger on real exported events.
