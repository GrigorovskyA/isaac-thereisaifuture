## 1. Implementation

- [x] 1.1 Lua: `killed` ring (16) from `MC_POST_NPC_DEATH` for listed unfriendly enemies,
  reset per epoch, sent in the oracle; Lua tests (listed kill recorded, unlisted and
  friendly ignored, cap 16, reset on new game).
- [x] 1.2 Python: `LiveOracle.killed`; kill credit in the event deriver; tests (one-shot
  kill pays max HP once, partly damaged enemy pays the rest, repeated id pays nothing,
  unseen id pays nothing, still-listed id pays nothing, stall clock resets on a kill).
- [x] 1.3 Reward v6 config and contract `pure-v6`, training config, archive reward v5,
  docs; tests that reward v5 checkpoints are refused.

## 2. Verification

- [x] 2.1 Full offline gate and strict OpenSpec validation.
- [x] 2.2 Windows `scripts/Check.ps1` with Lua (1185 passed, no skips; strict OpenSpec
  16/16), RL smoke (3499 inputs), closed-game hash-verified redeploy.
- [x] 2.3 Native check: a one-shot kill gives `col_enemy_damage` > 0 in the episode row
  and `enemies_killed` > 0 with damage dealt > 0; no episode with kills and zero damage.

  Native qualification: epoch 6/frame 1897 credits an enemy at full 10 HP once;
  episode 6 has one kill, damage_dealt_fraction 1.35 and col_enemy_damage 6.75.
  All five completed episodes with kills have positive damage; no overpayment found.
  See reports/2026-10-23-pure-v6-native-acceptance.md.
