## 1. Implementation

- [x] 1.1 Python schema 5: wire models (obstacle class, room shape, map, off-grid
  flag), encoder blocks, stall clock in env and live backend, 48 KiB messages; tests for
  validation, encoding layout and size, shapes, special rooms, stall fraction and
  worst-case message size.
- [x] 1.2 Lua observer schema 5: obstacle classes, border walls dropped, fireplaces,
  cap 24, room shape, minimap, 48 KiB, kill and hit counters in the oracle; Lua tests.
- [x] 1.3 Reward v5, oracle metrics (kills, hits by source) into episode rows, lineage
  `pure-v4` config, launchers, dashboard default, docs; tests that `pure-v3` configs and
  checkpoints are refused and that stall restart pays -10.

## 2. Verification

- [x] 2.1 Full offline gate and strict OpenSpec validation.
- [x] 2.2 Windows `scripts/Check.ps1` (1175 passed with Lua, no skips;
  OpenSpec 15/15), RL smoke (3499 inputs), and hash-verified mod redeploy while closed.
- [ ] 2.3 Short native check: obstacle classes match the room (rocks, pits, spikes,
  fire), no perimeter walls, minimap entries plausible (start room current, neighbours
  known), stall clock rises and resets, a kill and a self-bomb hit counted, death and
  stall restart, reloadable checkpoint.
