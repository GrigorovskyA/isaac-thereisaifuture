# Wall-stagnation replay fixture

`policy.jsonl` and `oracle.jsonl` are records 30-38 (lines 30-38, unmodified)
of the paired learning traces in evidence bundle
`wall-stagnation-offline-20261022-01` (zip SHA256
`e66c0cc9f5482ef27487ef8b70382b24fb47b6a88b98913922a644b801a5390d`):

| Source trace | Full SHA256 |
| --- | --- |
| `traces/learning-policy.jsonl` | `62d846283027b239149ffcf4bbdd1c76d92eea83d425c591925fbb2d51e44ad6` |
| `traces/learning-oracle.jsonl` | `e511db640ebe6eaaaa3a0b279ffbbe567d0b535c944457cba9989d62b82cb195` |

The window covers the last target-1 hit (record 30), the switch to target 2
(record 33) and the first right-then-left deviation from the left wall
(records 35-38). The expected bonuses in `tests/test_wall_stagnation.py` are
the logged `firing_position_reward` values for frames 79472-79498 from
`run/live-events.jsonl`. They contain no paths, credentials or save data.
