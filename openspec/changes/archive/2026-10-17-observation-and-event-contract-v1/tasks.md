## 1. Contract (offline)

- [x] 1.1 Add `entities.py` strict models (EntityFrame, Entity, OracleEvent) with bounds and size limits.
- [x] 1.2 Add `encoding.py`: capacities, ordering, masks, normalization, overflow diagnostics.
- [x] 1.3 Add `recording.py`: JSONL recorder/replayer, manifest, version rejection.
- [x] 1.4 Add the synthetic frame factory `tests/synthetic.py` (no recorded JSON fixtures yet).

- [x] 1.5 Implement opt-in read-only Lua entity export, nested envelope validation, source overflow and bounded scans.
- [x] 1.6 Implement finite attach-only entity_probe and bounded recording/replay.

## 2. Offline checks

- [x] 2.1 Write behavioral tests (tests/test_observation_encoding.py): shape stability, origin vs missing, unknown vs zero, shuffle determinism, oracle rejection, round trip, version rejection.
- [x] 2.2 Run the new tests on Windows; 467 offline tests passed including Lua stubs, no skips.
- [x] 2.3 `./scripts/OpenSpec.ps1 validate observation-and-event-contract-v1 --strict` passes.
- [x] 2.4 `./scripts/Check.ps1` passes including Ruff/format/mypy/pip and strict OpenSpec.

## 3. Documentation

- [x] 3.1 Document the implemented schema, capacities and offline-only status in docs/OFFLINE_CONTRACTS.md.

## 4. Real-game evidence (pending closed-game deployment and manual launch)

- [x] 4.1 Verify Lua APIs for entities on the installed build.
- [x] 4.2 Record real fixtures (provenance `game_api`) and validate schema/encoder/replay; record actual coverage of enemy, projectile, obstacle and pickup kinds.
- [x] 4.3 Evidence report, verify skill, archive only after 4.1-4.2.
