## 1. Implementation (offline)

- [x] 1.1 Add `fullrun.py` (backend protocol, controller, budgets, taxonomy, report).
- [x] 1.2 Write tests/test_fullrun.py with a synthetic backend (gate, taxonomy, release, report).

## 2. Checks (run on Windows)

- [ ] 2.1 Run the new tests (passed on macOS: 7 tests; ruff/mypy not run here).
- [ ] 2.2 `./scripts/OpenSpec.ps1 validate full-run-integration --strict`.
- [ ] 2.3 `./scripts/Check.ps1` passes.

## 3. Real-game evidence (blocked)

- [ ] 3.1 Implement a real `RunBackend`; choose character, difficulty, route, final boss and the
  success threshold before test evaluation.
- [ ] 3.2 Series of complete autonomous runs; evidence report; archive.
