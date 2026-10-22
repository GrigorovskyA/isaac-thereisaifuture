## 1. Implementation (offline)

- [x] 1.1 Add `progression.py` (Ledger, UnlockGraph, load_graph, select_next_goal).
- [x] 1.2 Write tests/test_progression.py (tamper, non-observed, determinism, missing dependency, cycle).

## 2. Checks (run on Windows)

- [ ] 2.1 Run the new tests.
- [ ] 2.2 `./scripts/OpenSpec.ps1 validate progression-ledger-and-goal-selection --strict`.
- [ ] 2.3 `./scripts/Check.ps1` passes.

## 3. Real-game evidence (blocked)

- [ ] 3.1 Research and supply real version-specific unlock dependency data with provenance.
- [ ] 3.2 Reconcile the ledger with actual file-2 state across a normal restart; evidence report; archive.
