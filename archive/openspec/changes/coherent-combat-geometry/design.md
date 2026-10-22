## Decisions
Keep legacy v3 potential/ledger available for exact offline historical replay.
The active firing opt-in selects v4 and refuses v3 training resume. BFS visits at
most1024 nodes from positively witnessed goal cells. Interpolate graph distances
bilinearly over the enclosing grid centers, requiring every nonzero-weight corner
to be measured walkable/reachable. At edges use only nonzero weights. Unknown
support returns no potential; never fall back to a center-detour formula.
This is a continuous field over supported patches, not an exact continuous
shortest-path solver. Ordinary open-row/column approach must monotonically improve.

Maintain best potential per room/visible target identity, with total paid<=0.25
per physical room. Keep records across target switching, resets and reentry;
switches rebaseline unpaid. Bound4096 rooms/65536 targets and fail without eviction.
Compare both poses against fixed before geometry and shared positive candidates;
missing/changed support rebases unpaid. Motion<=0.5 and shots alone never pay.

Observation2 composes the unchanged649-vector with74 explicit features: two weapon
fields(known,range/4000), four cardinal40unit ground probes(known,blocked), sixteen
visible enemy slots(known line,clear line,in ordinary range,cardinal alignment).
Ground probes are not a controller or a flight path guarantee. Weapon support is
conservative ordinary tears only. CheckLine mode0 measures ground-blocking geometry;
mode3 measures projectile blockers. At most4+12 queries per capture; no query when
off. A separate negotiated top-level combat_geometry field carries only observable
own stats/local lines to already visible entities, not oracle navigation/HP/targets.
Feature known bits distinguish unavailable from clear. Validate enemy identities
against the same entity frame. Do not silently increase source obstacle cap12.

Opt-in live combat geometry wraps observation before the gate; diagnostics must
encode its declared schema. Checkpoints/training explicitly use observation1 or2;
old defaults stay1. Frozen loaders validate dimensions against manifest schema.
No automatic checkpoint conversion or new training lineage is added.

## Risks and validation
Conservative interpolation can withhold shaping near blocked cells; measure this
in replay, not as guaranteed improvement. Probe APIs require native qualification.
Test retreat/approach, subcell/edge behavior, blocked support, target switching,
cap/reset/oscillation, legacy isolation, unknown geometry, frame/identity mismatch,
oracle separation, shape compatibility and early checkpoint refusal. Full Windows
gate/synthetic smoke and saved-trace replay precede publication. Native and gameplay
acceptance remain pending without a separately bounded experiment.
