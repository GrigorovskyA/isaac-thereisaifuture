## 1. Implementation (offline)

- [x] 1.1 Add `resources.py` (state, events, ledger, chooser protocol, random baseline, evaluation helper).
- [x] 1.2 Write tests/test_resources.py (each exploit, cap, session check, chooser, counterfactual).

## 2. Checks (run on Windows)

- [ ] 2.1 Run the new tests.
- [ ] 2.2 `./scripts/OpenSpec.ps1 validate resource-and-build-policy --strict`.
- [ ] 2.3 `./scripts/Check.ps1` passes.

## 3. Real-game evidence (blocked)

- [ ] 3.1 Verify real pickup/drop/spend/use events and identities in the bridge.
- [ ] 3.2 Learned chooser beats random and item-tier baselines on predefined scenarios; evidence report; archive.
