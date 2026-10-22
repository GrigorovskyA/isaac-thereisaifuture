## 1. Implementation (offline)

- [x] 1.1 Add `curriculum.py` (stages, advancement, regression gate, baseline comparison, results log, leakage check).
- [x] 1.2 Write tests/test_curriculum.py (gate logic, tolerance immutability, negative-result retention).

## 2. Checks (run on Windows)

- [ ] 2.1 Run the new tests.
- [ ] 2.2 `./scripts/OpenSpec.ps1 validate combat-curriculum-and-regression --strict`.
- [ ] 2.3 `./scripts/Check.ps1` passes.

## 3. Real-game evidence (blocked)

- [ ] 3.1 Fix tolerance and thresholds in an experiment plan before training.
- [ ] 3.2 Model beats random on held-out test scenarios in the real game with no regression; evidence report; archive.
