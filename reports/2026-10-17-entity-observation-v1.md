# Evidence: observation-and-event-contract-v1

- Date/time: 2026-10-17, approximately 21:48вЂ“21:55 Europe/Amsterdam (UTC+02:00).
- Git revision: based on d52fcb2 (offline batch) and 5eaafdb (item-03 archive),
  with the item-04 implementation/fixtures/docs then uncommitted.
- Scope: bounded read-only native entity export, schema/masks/overflow,
  recorder/replay, finite attach-only probe and real recorded fixtures.
- Game: Steam Repentance+ J460; installed manifest build 22878971 rechecked.
  Wire game metadata remains null/unavailable, not fabricated from the manifest.
- Adapter: 0.4.0; Lua 5.3; REPENTOGON false. Python 3.12.14; dependencies unchanged.
- Scenario: operator-confirmed file 2, solo existing run, manual gameplay.
  Ordinary-profile observation permission; no training isolation claimed.
- Budgets: first probe 50 samples / 45 seconds; second 200 / 60;
  final default regression 10 samples with bounded accept/message deadlines.
- Seeds/splits: no supplied game seed or train/validation/test split; no experiment
  or training. Surrogate IDs are not seed values.

## Deployment and provenance

The user closed the game and explicitly authorized updating the mod. No Isaac
process remained before copying. Both installed 0.3.1 artifacts were backed up
with matching hashes under ignored reports/local. Source 0.4.0 was copied and
hash-verified. Preflight-only exited 0 without launching a process. The user
manually launched Start-Isaac.cmd with --samples 1 --duration 180, chose file 2,
entered a room and confirmed the initial reader had finished.

Hashes of the exact source/deployed artifacts used by the live probes:

| Artifact | SHA256 |
|---|---|
| main.lua | d4d40604138fa3826970900c65033d2784c4ff61a25baeb7e42d5cf803440f4d |
| metadata.xml | 3a7749dffab0ddb43f496cd1688baa1c55eec5521f2ecd15a0e1e212858d9961 |

No installed file was changed while the game was running. A source-only draft
adding two extra property assertions was discarded before runtime acceptance;
source/deployed hashes were then compared exactly. Those assertions were never
deployed or counted as live-tested. The final mixed-capacity test remains.

The observed TCP connection belonged to isaac-ng PID 39624, loopback destination
9528, matching the manually started process. Native log recorded Observer 0.4.0
registration and peer disconnect. Private action approval was absent, action
capability was not advertised and no control/restart mode was requested.

## Results

| Check | Command/scenario | Exit code | Status | Evidence |
|---|---|---|---|---|
| Offline gates | `.\scripts\Check.ps1` with existing isolated Lua runtime | 0 | passed | 476 tests, no skips; Ruff; 66 formatted files; strict mypy 32 sources; pip; OpenSpec 24/24 before new main-spec sync |
| Strict change | `.\scripts\OpenSpec.ps1 validate observation-and-event-contract-v1 --strict` | 0 | passed | Expanded proposal/design/eight requirements/tasks valid |
| Closed-game preflight | `python -m isaac_threrisaifuture.launcher --preflight-only` | 0 | passed | Source/deployed hashes match; no process launched |
| Room probe | `python -m isaac_threrisaifuture.entity_probe --output reports/local/entity-runtime-20261017-214900/frames.jsonl --samples 50 --seconds 45` | 0 | passed | 50 frames, 0 unavailable; epoch 1, room visit 0; frames 235682вЂ“235978 |
| Manual-play probe | `python -m isaac_threrisaifuture.entity_probe --output reports/local/entity-gameplay-20261017-215008/frames.jsonl --samples 200 --seconds 60` | 0 | passed | 200 frames, 0 unavailable; epoch 1, room visits 1..8; frames 237700вЂ“238799 |
| Real schema/encoder/replay | open_replay and encode on all 250 recorded frames; selected fixtures in pytest | 0 | passed | Finite 649-value float32 vectors; all four kinds; deterministic fixture replay |
| Default regression | ObservationClient(ObserverConfig(accept_timeout=5)); 10 receive calls after manual-play probe | 0 | passed | Fresh session 7aa25d3a4d534455a9da153d3521e14b; frames 245557вЂ“245611; original snapshot shape; action capability absent |
| Cleanup | Client contexts exit, then bind 127.0.0.1:9528; process/native log check | 0 | passed | Listener released; native peer disconnect; game Responding=True and left running |
| Remote hardening | tests/test_recording_boundaries.py via full Windows check | 0 | passed | Five additional adversarial cases; remote syntax-only result was not counted as pytest |

Temporary pytest TEMP/TMP and Lua test runtime paths were process-local. No global
settings/dependencies were changed. The first intermediate format check failed
on the newly written fixture test; Ruff formatted that file and the full check
above then passed. Earlier batch-review temp-permission failure is separately
recorded in reports/2026-10-17-offline-batch-review.md.

## Real game

First session: 420b94d246d74bb289b5de25e1393487. Fifty snapshots contained 12
exported obstacles each (600 obstacle records); native source_overflow reported
30 additional obstacles per sample. Player position stayed (300.2424621582,280),
raw red health 8/8. This established room/grid reads, not enemy coverage.

The user then explicitly agreed to manual ordinary gameplay while reading.
Second session: 1ae6554bbd0c448ca7e7989cccebaed3. It contained 188 distinct
player positions, eight local room visits and the following coverage:

| Kind | Frames containing kind | Distinct exported surrogate IDs | Entity records across frames |
|---|---:|---:|---:|
| Enemy | 113 | 10 | 238 |
| Projectile | 6 | 2 | 6 |
| Obstacle | 200 | 248 | 2400 |
| Pickup | 95 | 13 | 147 |

These are repeated observations, not counts of defeated enemies, collected items
or achievements. Projectile kind identifies EntityType.ENTITY_PROJECTILE;
this first subset does not classify reflected/friendly projectile flags.
Initial/final raw red health stayed 8/8 during this recording. Movement and
shooting were manual; the probe sent only hello and read snapshots. No policy,
restart, reset or input injection ran. Ordinary game save writes are not isolation.

Actual APIs exercised include GetRoomEntities, entity existence/visibility/death/
active-enemy checks, Position/Velocity and internal lifetime keys; GetGridSize,
GetGridEntity, CollisionClass and GetType. API documentation was consulted before
implementation (links in the design); the observations above establish installed
build evidence for the encountered subset. Special weapons/types are not inferred.

## Committed fixtures

Selected original records, without coordinate/ID edits, are small reusable fixtures:

| File | Frames | SHA256 |
|---|---|---|
| tests/fixtures/entities/j460-obstacles-v1.jsonl | 235682,235827,235978 | 5c2c95fbe62ed5feb8658cb9725daf2cc1e530f4298725d630abe82a295e16f2 |
| tests/fixtures/entities/j460-gameplay-v1.jsonl | 237700,237760,238607,238799 | 10aa41fa6cf503bfb8238d2ca5af42c6c18461db0d1156551b03fc887c1a6bf0 |

Full recordings, deployment backups and operator transcripts remain ignored.
Raw recording SHA256: room d34859c99c9fe5707a1b08892bf446447e44deeeb3e279a905642ce48b32c171;
manual play 9c0c5ad314e8975dd00fcdb08bc9acdf49f7c064be1b20a1734693ec633f9476.
No private approval, save, backup or raw game log is committed.

## Separate self-review and OpenSpec verification

The primary agent performed a separate self-review using openspec-verify-change.
The user subsequently authorized a remote offline contributor through subagent.md;
that contributor supplied five boundary tests, reviewed and executed on Windows.
This is not a claim of an independent full implementation review.

| Requirement | Implementation/evidence |
|---|---|
| Fixed-shape masked policy observation | entities.py/encoding.py; missing-vs-origin/optional masks/source overflow tests; all 250 real frames encode |
| Stable ordering and determinism | Player-relative offsets, generation/ID ties; translation and shuffled-order tests; native nearest-first checks and actual frame analysis |
| Oracle separation | Distinct strict types/streams; unknown-field rejection; native HP null, no map/seed/pointer export |
| Versioned recording and replay | Manifest and integer schema checks; deterministic real fixture replay; incompatible-version tests |
| Real-game fixture validation | Two actual sessions, all four native kinds and committed recorded fixtures |
| Explicit native entity negotiation | Opt-in capability; unchanged default shape; incompatible-mode, old-peer and nested-identity/replay rejection tests; default real regression |
| Bounded visible export | Scan/object/message caps, source drops, unavailable-on-fault; Lua simulated bound tests and real obstacle overflow |
| Finite recording and bounded replay | Sample/wall deadline, close-on-fault and no-overwrite; size/blank/provenance/corruption tests; real finite exits and listener cleanup |

No removal or rename requirement exists. All eight added requirements map to
implementation, behavioral tests and the declared live slice. The earlier
origin-distance defect report was withdrawn: entity coordinates already are
player-relative; the added translation test prevents that misunderstanding.
No known critical issue remains within the declared acceptance scope. Special
weapons, complete room semantics and long-run behavior remain explicit limits.

## RL evaluation and continuation

No training, learned model, reward evaluation, Gymnasium game backend, automatic
save selection or full campaign was run. Next roadmap item is episode-lifecycle;
its 100-episode live criterion requires authorized verified training isolation
and lifecycle/reset design. Standing ordinary-profile permission covers bounded
action tests, not repeated training episodes or expanded reset budgets. Preserve
three restart attempts / ten minutes and the 120-second action lease.

The new source protocol is docs/ENTITY_OBSERVATION_PROTOCOL.md. Main-spec sync,
archive and final post-archive strict validation are recorded after they complete.

## Final lifecycle completion

All 14 tracked tasks completed. Eight new requirement blocks and the delta Purpose
were copied to the new main observation-encoding spec; structural/content checks
passed. Strict validation before archival passed 25/25. The archive command
`OpenSpec.ps1 archive observation-and-event-contract-v1 --skip-specs --yes`
exited 0; skip-specs avoided reapplying already synchronized content. Archived as
openspec/changes/archive/2026-10-17-observation-and-event-contract-v1.
Post-archive strict validation passed 24/24. Later offline changes remain open.
