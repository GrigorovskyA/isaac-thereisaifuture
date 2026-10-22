## 1. Implementation (offline)

- [x] 1.1 Add `env.py` (IsaacCombatEnv, RewardAccountant protocol, oracle sink).
- [x] 1.2 Write tests/test_env.py (checker, seeds, invalid actions, oracle channel, faults, 10,000 steps).

## 2. Checks (run on Windows)

- [ ] 2.1 Run the new tests.
- [ ] 2.2 `./scripts/OpenSpec.ps1 validate gymnasium-environment-v1 --strict`.
- [ ] 2.3 `./scripts/Check.ps1` passes.

## 3. Real-game evidence (blocked)

- [ ] 3.1 Real-bridge backend and an authorized game-test CLI.
- [ ] 3.2 10,000 real steps; measure steps/sec, p50/p95 latency, reset time, fault rate, memory.
- [ ] 3.3 Evidence report; archive.
