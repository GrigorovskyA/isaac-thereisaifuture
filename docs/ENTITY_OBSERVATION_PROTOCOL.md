# Entity observation protocol v1

Observer 0.4.0 adds an explicitly negotiated read-only extension to protocol v1.
Default observation, bounded death restart and safe actions retain their existing
wire shapes. This extension cannot combine with action or restart negotiation.
It does not start, select, reset or control a run.

## Negotiation and envelope

Append `entity_observation_v1` to the existing required capabilities. A missing
capability fails before any snapshot; there is no silent fallback. Only a peer
that requests this capability receives the extra `entity_frame` key in each
snapshot. Default clients receive no extra fields and trigger no entity scans.
Both modes retain UTF-8 newline JSON, loopback TCP, 32768-byte wire records (49152 bytes since schema 5),
nonblocking bounded Lua I/O and the existing 200 ms sampling cadence.

Available snapshots carry an EntityFrame; unavailable snapshots carry null.
Python verifies matching session, game epoch, room visit, engine frame, player
position and health. Existing sequence/update/frame ordering rejects replay and
regression; reconnect establishes a fresh session. Paused frames may repeat.
A failure closes the Python peer; no stale state is returned as success.

## EntityFrame

- `type`: entity_frame; `observation_schema_version`: integer 1.
- `provenance`: game_api for native frames, synthetic for offline fixtures only.
- `session_id`, `game_epoch`, `room_visit`, `frame_id`: match snapshot identity.
- `player_position`: room-local game coordinates, X right and Y down.
- `player_velocity`: velocity in game units per engine update, or null if unknown.
- `health`: existing raw half-heart/container fields.
- `entities`: list of kind, opaque entity_id, spawn_generation, player-relative
  position, optional velocity and optional HP/max HP. Missing values are null.
- `source_overflow`: per-kind count of supported visible objects discarded at
  the native export capacity. Absence means zero, not a missing scan.

The native subset includes active visible enemies, projectile entities,
pickups and selected colliding grid obstacles (ordinary rock shapes, walls,
pits, spikes, poop and TNT). It omits player tears, beams, familiars, effects,
doors, grid subtypes, item contents and hidden entities. Enemy HP stays unknown;
being readable through an API does not make it permitted policy input. No hidden
room/map, engine seed, pointer or oracle/reward event enters a policy frame.
This is a documented initial subset, not full weapon or geometry coverage.

Opaque surrogate IDs are allocated only for observed objects and never reused
within a game epoch. spawn_generation is zero because IDs are not reused.
A current-room registry preserves live identities across samples/reconnects,
including an observed object temporarily hidden between samples. Room entry
clears that registry without resetting its counter; a new epoch resets both.
Objects recreated while a room is unloaded receive fresh IDs. Sampling cannot
prove events that happened entirely between samples.

## Bounds and encoding

Scan at most 1024 dynamic objects and 2048 grid cells. Exceeding a scan bound or
an API read failure produces unavailable state with null entity_frame, never a
successful partial scan. Native per-kind capacities are 12 enemies, 20
projectiles, 12 obstacles and 4 pickups (48 total); select nearest first with
opaque ID ties. Offsets/velocity round to 0.001 game units. Oversized encoded
messages close the peer under the 32768-byte limit (49152 since schema 5).

Schema 5 (current) adds to the frame: `obstacle_class` on every obstacle (rock, marked
rock, bomb rock, block, pit, spikes, poop, TNT, fire, wall, other; fireplaces are `fire`
obstacles, perimeter wall cells are not exported, observer cap 24), `room.shape` (1..12),
`map` (up to 64 minimap rooms: grid index, shape, visited, current, room type only when
visited or its icon is shown) and `map_current_off_grid`. The oracle block gains
cumulative `kills` and `player_hits` by source; they are metrics only. Messages may reach
49152 bytes. See `docs/RL_DESIGN.md` for the encoded vector (3499 floats).

The Python encoder retains schema-1 capacities 16/32/24/8 and outputs 649 float32
values. Presence and optional-field masks distinguish missing objects from
objects at relative (0,0), unknown HP from zero HP and unknown velocity from
stationary objects. Stable ordering uses player-relative distance, spawn
generation and ID. Source drops and encoder drops add together in diagnostics.
Position/velocity/health scale constants are versioned hypotheses; clipping is
reported. OracleEvent is a separate type and recording stream.

## Finite recording and replay

Run from the project root after manually launching/selecting a run. The output
parent directory must already exist; an existing output file is never overwritten.

```powershell
.\.venv\Scripts\python.exe -m isaac_threrisaifuture.entity_probe --output reports/local/entities.jsonl --samples 50 --seconds 60
```

This listener attaches only. Limits: 1..500 samples, >0..300 seconds; defaults
50/60. A snapshot budget includes unavailable samples. Only available, validated
and successfully encoded frames are recorded. Zero written frames is a failure.
No retries, gameplay inputs or restart are requested. Errors close resources,
return a failure code and retain completed lines as partial evidence; interruption
returns 130. A successful file is evidence of observations, not of learning.

Standalone recording/replay uses a separate 65536-byte line bound, checked with
bounded readline and before writing. The first line is RecordingManifest with
observation schema version, stream and provenance. Replay rejects incompatible
versions, changed provenance, mixed types, blank records and oversized lines.
Use open_replay(path, 'policy_frames') and encode(frame) for offline diagnostics;
oracle_events must use a different file. A native_oracle_events manifest also carries the
requested oracle kinds; see docs/NATIVE_EPISODE_PROTOCOL.md (oracle stream).

## Evidence and deployment

See reports/2026-10-17-entity-observation-v1.md and tests/fixtures/entities/README.md.
The installed 0.4.0 artifacts were backed up/deployed while the game was closed,
then hash-verified. Initial launch/save selection were manual. Actual probes
read 50 room frames and 200 manual-play frames, including all four native kinds.
Raw logs/backups remain ignored; selected policy records are test fixtures.
Training isolation, automatic slot attestation, reward events, reset/step
synchronization and special weapons remain outside this acceptance slice.
