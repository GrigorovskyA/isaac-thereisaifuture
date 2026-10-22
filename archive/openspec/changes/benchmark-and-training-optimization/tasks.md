## 1. Implementation (offline)

- [x] 1.1 Add `benchmark.py` (timing harness, injectable clock, bounds, JSON report).
- [x] 1.2 Add synthetic action-repeat comparison and non-applying proposal function.
- [x] 1.3 Write tests/test_benchmark.py with a fake clock.

## 2. Checks (run on Windows)

- [ ] 2.1 Run the new tests.
- [ ] 2.2 `./scripts/OpenSpec.ps1 validate benchmark-and-training-optimization --strict`.
- [ ] 2.3 `./scripts/Check.ps1` passes.

## 3. Real-game evidence (blocked)

- [ ] 3.1 Measure real-bridge throughput on an authorized profile; evidence report.
- [ ] 3.2 Compare CPU/GPU and batch sizes on real training; record memory and failure rate.
- [ ] 3.3 Multiple game instances only with isolated profiles, ports and input; do not archive before this.
