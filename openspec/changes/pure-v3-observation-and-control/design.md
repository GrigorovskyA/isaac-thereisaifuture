# Design

## Observation schema 4

New `entity_frame` fields (Lua -> Python, strict models):

- `stats`: `damage`, `tears_per_second` (30 / (MaxFireDelay + 1)), `range`
  (TearRange), `shot_speed`, `move_speed`, `luck`. Lua clamps to declared ranges
  with a comment; Python rejects out-of-range values.
- `tear_flags`: 16 booleans in this fixed order: spectral, piercing, homing, slow,
  poison, freeze, split, growing, boomerang, persistent, wiggle, explosive,
  charm, confusion, burn, bouncing.
- `weapons`: booleans for WeaponType TEARS, BRIMSTONE, LASER, KNIFE, BOMBS,
  ROCKETS, MONSTROS_LUNGS, LUDOVICO_TECHNIQUE, TECH_X, BONE, NOTCHED_AXE,
  URN_OF_SOULS, SPIRIT_SWORD, FETUS, UMBILICAL_WHIP (15).
- New entity kinds: `own_attack` (EntityTear/EntityLaser/EntityKnife spawned by
  the player or its familiars) and `bomb` (every EntityBomb, plus `age_frames`).
  Same slot fields as other kinds; bomb slots add an age feature.

Encoding (size computed in code and pinned by a test): existing blocks, then
stats (6, scaled), tear flags (16), weapons (15), own_attack slots (16 x 8),
bomb slots (4 x 9). Oracle data still never enters the vector.

`MAX_MESSAGE_BYTES` and the Lua outbound limit become 32768; a worst-case frame
test pins the margin.

## Control

`action_repeat_game_updates: 6`. The use head of `action_net` is initialised with
bias logits `log([0.85, 0.05, 0.05, 0.05])` (shifted to mean zero) and zero weights
for that head's rows, at model creation only; recorded in the contract as
`use_head_initial_none_probability: 0.85`.

## Reward v4

`configs/reward-v4.yaml` = reward v3 with `collectible_new: 2.0`.

## Lineage

`configs/training-pure-v3.yaml`: contract observation 4, action 2, reward 4,
action repeat 6, use-head prior 0.85. Run root `runs/pure-v3`; first session
`--initialize`. Launchers and dashboard default to it.
