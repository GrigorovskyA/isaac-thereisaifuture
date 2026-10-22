## Decisions

Motion samples retain session,epoch,visit,accepted command frame,position and
requested direction. Compare consecutive samples only within one context and
1..15frames. Report Euclidean displacement and projection along the requested
direction. Less than0.5units is a near-stationary observation,not collision proof;
none-direction commands are idle and never counted as movement failures.
Inertia,knockback and timing can affect displacement;do not create rewards/actions.

Measured-grid routes use finite cardinal BFS over the existing management grid.
Map world positions to nearest grid centers;reject out-of-bounds,blocked endpoints
and disconnected cells rather than snapping them into a reachable area. Include
start/goal in returned cells. This is a coarse walking-grid diagnostic,not a
physics simulation,projectile blocker mask or live controller.

Replay source is the completed657-decision frozen pilot. Verify native action
sequence and direction agree with scheduled controls;retain source/accepted frame
offset explicitly. Future positions and oracle navigation stay in offline output,
never policy observations,normalizer inputs or inference logs reused as input.
Do not silently replace clipped player coordinates in old model inputs.

## Acceptance

Behavioral tests cover directional projection,idle/inertia,context/frame rejection,
grid detours,blocked/outside endpoints and disconnected routes. Full Windows gate
passes. Frozen capture replay reports all controllers,denominators and missing
matches,checks data/model hashes,and distinguishes old native evidence from a
new runtime test. Preserve t6912 and report range/line-of-sight unknowns honestly.
