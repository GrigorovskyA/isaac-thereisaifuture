# Tasks

## 1. Runner contracts
- [x] 1.1 Implement fixed deadline, lease mapping and strict parent preflight; test fractional clocks, delays and refusals; document CLI.
- [x] 1.2 Implement shared live cancellation/deadline and progress hooks; test no renewed time or fabricated checkpoint.
- [x] 1.3 Implement durable status and owned cleanup; test early stops, stale progress, cancellation and cleanup/metrics failures.

## 2. Verification
- [x] 2.1 Pass targeted regressions and Windows gate; self-review, OpenSpec verify and record evidence/status.
- [ ] 2.2 Under a separately declared five-minute native plan, verify Continue2 identity, resume update, stop/input/lease/game/sleep cleanup; retain interrupted and timer-stop evidence.
