## 1. Implementation

- [x] 1.1 `RunProgress` and live wiring; unit tests for revisits, counter peaks,
  collectibles, floors, damage and clears, and a live test where walking between two
  known rooms still stalls after 90 s (fails on the old behaviour).

## 2. Verification

- [x] 2.1 Full offline gate and strict OpenSpec validation (macOS).
- [x] 2.2 Windows `scripts/Check.ps1` (1123 passed with Lua, no skips;
  strict OpenSpec 14/14; `scripts/Smoke-RL.ps1` passed).
- [ ] 2.3 Native: in the next `pure-v3` session no stall-truncated episode runs far
  beyond 90 s without new rooms, damage or pickups.
