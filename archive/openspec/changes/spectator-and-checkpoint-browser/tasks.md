## 1. Implementation (offline)

- [x] 1.1 Add `spectator.py` (browser, runner, replay tap, CLI).
- [x] 1.2 Write tests/test_spectator.py (incompatible flagged, determinism, no oracle leakage, refusal).

## 2. Checks (run on Windows)

- [ ] 2.1 Run the new tests.
- [ ] 2.2 `./scripts/OpenSpec.ps1 validate spectator-and-checkpoint-browser --strict`.
- [ ] 2.3 `./scripts/Check.ps1` passes.

## 3. Real-game evidence (blocked)

- [ ] 3.1 Provide a real-bridge env factory and a model loader for saved checkpoints.
- [ ] 3.2 Replay a saved model at game speed on an authorized profile, stop and recover control; evidence report; archive.
