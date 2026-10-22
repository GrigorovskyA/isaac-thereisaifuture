## Context

See the2026-10-21 native combat diagnostic. No reward should pay merely because an
enemy is close. Walking geometry does not prove projectile clearance. Existing
native tear audit uses TearRange and Room:CheckLine(mode3), but current observer
does not export weapon model or candidate clearance. These APIs require native
qualification; documentation is not installed-game acceptance.

## Decisions

Negotiate firing_geometry_v1 only with live_loop and navigation_grid_v2. Keep data
inside the oracle/reward channel; encoder649 and policy schema1 remain unchanged.
The Lua collector feature-detects HasWeaponType; absent/unsupported APIs produce
explicit unavailable/unsupported status, not invented ordinary-tear semantics.
Only ordinary tears, visible vulnerable targets and measured grid cells qualify.
No more than32 CheckLine(mode3) calls per sample, no movement commands, no new scan
beyond existing bounds. Range is raw TearRange world units, not multiplied again;
require a20unit range margin,80unit minimum standoff and8unit axis tolerance.
These margins are versioned hypotheses, not optimal gameplay rules. Spectral and
nonordinary weapons are unsupported until separately modeled.

Python independently checks range/alignment/cell validity. BFS proves a measured
walking route; it does not invent shot clearance. The potential is
1/(1+path_distance/max(40,tear_range)). A step evaluates both player positions
against the same before-frame target/candidate geometry, restricted to candidates
positively witnessed in both frames; changed grids/target identities or missing
telemetry pay nothing. Target movement alone or shooting is not progress.

Each collector retains the highest potential and a total0.25 reward allowance per
physical(session,epoch,stage,stage_type,room_index), across software resets and room
reentry. A baseline raises the high-water mark without paying. Only actual player
movement>0.5units that improves this record can pay; idle/wall pressure and repeated
approach/retreat cannot. Room history is bounded4096; exhaustion fails explicitly,
never evicts records to renew credit. This is capped novelty shaping, not a claim
of policy-invariant potential shaping. State is collector-local; external process
resume establishes a fresh baseline, not exact reward-state continuation. Such a
resume is not an agent action and must be recorded as a trajectory discontinuity.

Wrap only the real combat environment inside the gate. Management navigation never
earns this reward. Add a named reward component; preserve damage/clear/injury/death
coefficients and conservative event coverage. The no-progress guard still uses
damage/clear, not shaping. live-firing-v3 is a distinct reward contract; train/resume
must reject old-contract artifacts before environment creation. No migration or
automatic fresh-model fallback is added. The finite conservative session runner
does not select this new contract; it remains unchanged until a lineage is planned.

## Validation

Behavioral counterfactuals cover blocked/clear lanes, out-of-range, no walking route,
unsupported weapons, exact standoff, target/grid changes, static shots, tiny motion,
oscillation, resets, reentry, replayed frames, bounded memory and total allowance.
Wire/negotiation and Lua harness tests cover explicit opt-in, query cap and absence
of APIs. Check unchanged policy encoding and early old-checkpoint refusal. Full
Windows gate and synthetic smoke precede publication. Native deployment, ordinary
weapon API confirmation, shot-clearance verification and comparable5min training
are separate pending tasks; no improvement claim follows offline acceptance.
