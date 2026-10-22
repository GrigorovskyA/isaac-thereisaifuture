# Real J460 entity fixtures

These are selected, unmodified policy-frame records from authorized read-only
gameplay on 2026-10-17. They are not synthetic peers. No saves, private approvals,
account data, raw game logs, oracle events, engine pointers or seeds are included.

- `j460-obstacles-v1.jsonl`: frames 235682, 235827, 235978 from a 50-frame room probe.
- `j460-gameplay-v1.jsonl`: frames 237700, 237760, 238607, 238799 from a
  200-frame manual-play probe through local room visits 1..8. Together these
  selected frames include enemy, projectile, obstacle and pickup kinds.

Each first line is a versioned recording manifest. Remaining lines are original
EntityFrame JSON records; coordinates and surrogate IDs were not edited.
Entity positions are relative to the player; player_position is room-local.
Enemy HP is deliberately unknown. source_overflow reports native capacity loss.

Observer 0.4.0, Lua 5.3, no REPENTOGON. Installed J460/build 22878971 was identified
separately; the hello game metadata remains explicitly unavailable. The operator
manually selected file 2 under the standing ordinary-profile observation exception;
this is not automated slot attestation or training isolation.

See reports/2026-10-17-entity-observation-v1.md for commands, source hashes,
coverage and limits. Large recordings and deployment backups remain ignored locally.
The offline tests validate schema/encoding/replay; they do not replay game actions
or establish Gymnasium integration, rewards or learning.

Schema note: the fixtures are observation schema 1 recordings and are kept unmodified.
Observation schema 4 adds pickup, inventory, stats, tear flag, weapon, collectible and room facts that these
frames never carried, so `tests/test_real_entity_fixtures.py` upgrades a temporary copy
with neutral placeholders before replay. Only positions, velocities and identities are
real; the later schema fields are not game evidence.
