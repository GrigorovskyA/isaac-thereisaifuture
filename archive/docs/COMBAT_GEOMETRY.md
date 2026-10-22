# Observable combat geometry

`live --combat-geometry --combat-gate` selects observation schema 2. This is an
explicit opt-in; the default remains schema 1. It does not select a reward contract
or authorize a game session. The active firing reward flag separately selects v4.

## Inputs and provenance

The first 649 values are the unchanged entity encoder. The following 74 values
come from the negotiated `combat_geometry_v2` channel, outside `oracle`:

| Offset | Values | Meaning |
| --- | --- | --- |
| 649 | 2 | Ordinary weapon range known, TearRange / 4000 |
| 651 | 8 | Left, right, up, down ground probes: known, blocked |
| 659 | 64 | Sixteen enemy slots: line known, line clear, in range, cardinal alignment |

Enemy slots use the existing distance/spawn/identity ordering. Absent slots are
zero. The line-known bit distinguishes a blocked line from an unknown result.
Unknown weapon range zeros range/alignment indicators; legacy entity-presence
features still identify occupied enemy slots. Inputs must have the same frame ID
and contain only enemy identities present in the visible entity frame.

Ground probes ask about a 40-unit cardinal segment with CheckLine mode 0. Flight
or unavailable capability yields unknown. Enemy probes use mode 3 for ordinary
tears only. They measure geometric line clearance, not a predicted hit, target
vulnerability, dodging, or shot timing. Range is radial distance; alignment is a
separate bit with an 8-unit axis tolerance. Clearance alone does not promise that
an action will hit an enemy.

The source still exports at most 12 nearest enemies/obstacles per kind; the larger
encoder capacity does not increase that source cap. Geometry adds at most four
movement and twelve enemy line queries per capture, and zero when disabled.
Unsupported weapons or failed APIs remain unknown. No oracle HP, navigation grid,
hidden entity, or reward goal is available to this encoder.

## Checkpoints and qualification

Schema 2 requires 723 model inputs and matching normalizer statistics. Live resume
rejects schema-1 checkpoints before creating an environment. Frozen inference can
load either supported schema and validates its exact size. There is no automatic
weight expansion, normalizer migration, or fresh-model fallback for resume.
Original v2 t21760 and v3 t24064 remain preserved. A new compatible lineage needs
its own explicit plan before training.

Offline tests cover serialization, unknown/blocked distinctions, oracle separation,
shape compatibility, synthetic save/load/resume, and legacy behavior. They do not
qualify installed-game collision semantics. Native qualification must first check
frame freshness, range, ground and projectile blockers, query bounds, and release
under a separately bounded session. Optimization-associated observation delay is
still a separate unresolved item. Do not automatically escalate to learning or a
longer duration from an offline pass.

## Native ordinary-tear follow-up

The short native check passed for ordinary tears:558 same-frame endpoints
reconstructed the723-vector and unchanged649 prefix;blocked in-range and clear
out-of-range enemy lines were distinguished. Frozen policy actions used only the
old prefix. This does not show schema2 learning or qualify optimizer stalls,
special weapons, or every room. See the
[native receipt](../reports/2026-10-21-native-coherent-combat-geometry.md).
