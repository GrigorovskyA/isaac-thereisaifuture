## 1. Implementation (offline)

- [x] 1.1 Add `navigation.py` (FloorMap, KnownMap, MapTracker, BFS, door moves, encoder v1).
- [x] 1.2 Write tests/test_navigation.py (no leakage, paths, stale events, encoder size).

## 2. Checks (run on Windows)

- [ ] 2.1 Run the new tests.
- [ ] 2.2 `./scripts/OpenSpec.ps1 validate known-map-and-navigation --strict`.
- [ ] 2.3 `./scripts/Check.ps1` passes.

## 3. Real-game evidence (blocked)

- [ ] 3.1 Feed `MapTracker` from verified real room-change and minimap data.
- [ ] 3.2 Fix the success threshold, then evaluate at least 100 unseen scenarios against random;
  evidence report; archive.
