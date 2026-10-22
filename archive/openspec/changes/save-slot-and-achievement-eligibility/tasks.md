## 1. Implementation (offline)

- [x] 1.1 Add `eligibility.py` (evidence, decision, guard, audit record).
- [x] 1.2 Write tests/test_eligibility.py (every denial reason, unknown denied, all-good allowed, audit).

## 2. Checks (run on Windows)

- [ ] 2.1 Run the new tests.
- [ ] 2.2 `./scripts/OpenSpec.ps1 validate save-slot-and-achievement-eligibility --strict`.
- [ ] 2.3 `./scripts/Check.ps1` passes.

## 3. Real-game evidence (blocked)

- [ ] 3.1 Bridge exposes slot id, achievements flag, debug/console, save-integrity and mod fields (blocked: absent).
- [ ] 3.2 Audit achievement eligibility of the installed build (mods, debug, seeds, challenges, daily, online).
- [ ] 3.3 Legitimate unlock retained after exit/restart on file 2; untouched files unchanged; archive.
