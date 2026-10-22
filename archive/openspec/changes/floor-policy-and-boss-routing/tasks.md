## 1. Implementation (offline)

- [x] 1.1 Add `floors.py` (policy protocol, options, executor, baselines, metrics).
- [x] 1.2 Write tests/test_floors.py with a synthetic floor (known-only targets, boss routing, truncation vs termination, determinism).

## 2. Checks (run on Windows)

- [ ] 2.1 Run the new tests.
- [ ] 2.2 `./scripts/OpenSpec.ps1 validate floor-policy-and-boss-routing --strict`.
- [ ] 2.3 `./scripts/Check.ps1` passes.

## 3. Real-game evidence (blocked)

- [ ] 3.1 Adapt the known map from navigation to `FloorView` and implement a real `FloorBackend`.
- [ ] 3.2 Autonomous exploration of a bounded floor set on unseen seeds; evidence report; archive.
