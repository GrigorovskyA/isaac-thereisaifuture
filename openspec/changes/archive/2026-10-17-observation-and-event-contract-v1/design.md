## Context

observation.py holds strict pydantic wire models (Hello, Snapshot). Policy observation,
oracle data and rewards do not exist yet. AGENTS.md requires oracle data to stay out of the
policy, normalizer, recurrent state and inference logs.

## Decisions

- **Modules**: `entities.py` (strict wire models `EntityFrame`, `Entity`, `OracleEvent`),
  `encoding.py` (pure `encode(frame) -> EncodedObservation`, numpy float32 vector plus masks),
  `recording.py` (JSONL recorder/replayer and manifest). No empty classes beyond these.
- **Entity model**: kind (enemy, projectile, obstacle, pickup), position relative to the
  player, optional velocity, optional observable HP, `entity_id` plus `spawn_generation`
  (both required for deduplication later), optional fields carry None, never 0.
- **Capacity**: fixed per kind (enemies 16, projectiles 32, obstacles 24, pickups 8).
  Selection: nearest first, ties by (spawn_generation, entity_id). Overflow count is exposed
  in diagnostics, not hidden.
- **Unknown vs zero**: every optional field has a paired validity mask bit; the value slot is 0.0
  when invalid and the mask distinguishes it.
- **Normalization**: constants are versioned in the schema (room-size scale, velocity cap);
  clipped values count in diagnostics. No learned normalizer here.
- **Oracle separation**: `OracleEvent` is a different type, in a different JSONL stream;
  `encode` accepts only `EntityFrame` and the recorder never writes both to one file.
- **Failures**: invalid frames raise `ProtocolError`; infrastructure faults stay separate
  from game outcomes.
- **Versioning**: `observation_schema_version = 1` embedded in the manifest and every recorded
  frame; replay rejects other versions.

## Risks / Trade-offs

- Capacities and constants are hypotheses; fixed by schema version, revised via new version.
- No real fixtures yet: wire fields may need adaptation after Lua export is verified.

## Migration

Additive; protocol v1 hello/snapshot messages are unchanged.

## Native export and transport

Observer source 0.4.0 advertises `entity_observation_v1` only when the top-level
entity API/enums are present. Only an explicitly requesting read-only client
receives `entity_frame` inside the existing snapshot envelope; ordinary clients
receive the original strict shape and never invoke entity/grid scans. Entity
mode cannot combine with action/restart negotiation. Unavailable snapshots carry
null entity_frame; Python checks nested session/epoch/frame/room/player/health
against the envelope before ordering validation. Live API availability still
requires an installed-build probe; an advertised name alone is not proof.

Scan limits: 1024 dynamic entities and 2048 grid cells per sample (200 ms cadence).
An exceeded scan bound/API failure produces unavailable state, never a partial
successful frame. Export nearest 12 enemies, 20 projectiles, 12 grid
obstacles and 4 pickups, at most 48 objects, under the existing 16384-byte wire
limit. `source_overflow` counts discarded visible objects per kind and the encoder
adds any further capacity loss. The standalone recording format retains its
65536-byte line bound, enforced before allocation of an entire input line.

Entity positions are player-relative, player_position is room-local. Velocity
uses the game axes in units per engine update; offsets/velocity are rounded to
0.001 units for bounded serialization. Dynamic visibility uses Exists/Visible/
IsDead; enemies use IsActiveEnemy(false), projectiles/pickups use EntityType.
Player tears, beams, familiars and effects are outside this first native subset.
Grid export includes colliding ordinary rocks, pits, spikes, poop, TNT and walls;
no doors, room-map queries, obstacle subtype or pickup contents are exported.
Enemy HP is always null: API access alone does not make it player-observable.
This conservative subset and all live coverage limits must be recorded.

A private pointer-plus-InitSeed key tracks dynamic lifetimes internally; neither
seed nor pointer crosses the policy boundary. Surrogate IDs never repeat within
a game epoch; spawn_generation is zero because IDs are not reused. Keep only
current-room live identities (including previously visible entities temporarily
hidden); clear on room entry, reset the counter only on a new game epoch. Reconnect
does not change a still-present identity. Grid keys combine cell and type but only
the opaque surrogate crosses the boundary. Identity is not guaranteed across
room unloading/recreation. No game API writes are used.

The finite entity_probe CLI attaches, negotiates, validates/encodes and records
at most 500 samples / 300 seconds; default 50 / 60. No retries, actions, launch,
reset or selection. Exceptions close sockets/files; a partial file remains
explicitly failed and existing paths are never overwritten.

API source evidence (accessed 2026-10-17; documentation, not J460 runtime proof):
- https://wofsauge.github.io/IsaacDocs/rep/Isaac.html
- https://wofsauge.github.io/IsaacDocs/rep/Entity.html
- https://wofsauge.github.io/IsaacDocs/rep/Room.html
- https://wofsauge.github.io/IsaacDocs/rep/GridEntity.html
- https://wofsauge.github.io/IsaacDocs/rep/enums/GridEntityType.html
