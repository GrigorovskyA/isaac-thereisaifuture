# Offline contracts (items 04вЂ“07)

Status: item 04 now has native read-only acceptance and real fixtures; later
modules remain offline contracts. Windows checks pass: 476 tests, no skips;
Ruff/format/mypy/pip; strict OpenSpec 24/24 after archival. See
reports/2026-10-17-entity-observation-v1.md for the real subset and limits.
Entity positions are player-relative offsets; player_position is room-local.
Ordering uses offset distance and is protected by a translation regression test.

- Observation contract: `entities.py`, `encoding.py` (capacities enemy 16, projectile 32, obstacle 24, pickup 8; overflow is reported, never silent).
- Recording: `recording.py` keeps `policy_frames` and `oracle_events` in separate streams.
- Episodes: `episodes.py`, toy backend `sim.py` (synthetic, not Isaac).
- Environment: `env.py` (Gymnasium, `MultiDiscrete([5, 5])`).
- Reward: `rewards.py`, coefficients from `configs/reward-v1.yaml`.

To verify on Windows: `ruff format`, ruff, mypy, pytest, `./scripts/OpenSpec.ps1 validate --all --strict`, `./scripts/Check.ps1`.
