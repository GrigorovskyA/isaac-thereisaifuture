# Design

## Context
See proposal. v4 remains the historical supported bilinear field.

## Goals / Non-Goals
Fill initial wall/corner feedback gaps using measured ground-line evidence.
Do not add a controller, guess diagonal clearance, change weights or restart a run.

## Decisions
Negotiate `firing_boundary_support_v1` only with firing_geometry_v1. Capture one
nearest fully walkable 2x2 grid patch (row-major tie break), projecting the current
position onto its closed rectangle. Only projections at distance <=sqrt(2)*40
are eligible. Scan at most1024 cells and issue at most one extra CheckLine(mode0,
threshold0,false,false) query. Missing/failed API means unknown, blocked means no
usable link. This measures a ground line, not whole-body collision safety.
Transmit version1, patch index, source and projected positions and nullable clear
only in oracle.firing.boundary_support; no policy/normalizer input changes.
Source coordinates must retain the snapshot's raw player precision; rounded entity
delta coordinates are unsuitable for an exact pose-bound evidence check.

v5 keeps v4 at supported positions. Otherwise validate nearest patch, exact source,
projection, walkable corners and positive line. Add Euclidean link length to the
v4 interpolated graph distance at the projection, then apply the same bounded
potential transform. Never return to forced nearest-cell detours on open rows.
Compare endpoints on fixed before target/shared goal cells with each endpoint's
own line evidence. A boundary patch change rebases unpaid unless the other endpoint
is inside that same patch; no credit from selecting another patch. Preserve v4
high-water target records, physical room cap0.25, stationary/reset/reentry guards.

Native attempt03 exposed an additional feedback barrier: all12 scripted escape
steps improved local position without exceeding the earlier door-to-wall record,
so high-water novelty paid zero. Before any v5 child exists,extend its unpublished
ledger with bounded signed recovery. On validated moving transitions evaluate both
poses against the same before-target/shared-goal geometry and their own line proofs.
Charge0.25*(potential loss) as negative reward,with outstanding debt capped0.25 per
physical room across targets. Refund only previously charged debt for that same
target on measured potential gain. Keep debt across collector reset/reentry/target
switch; unknown geometry and stationary actions charge/refund nothing. Debt keys
are bounded by existing room/target histories. Novelty remains capped0.25 per room;
cumulative recovery is never positive,so cycling cannot mint new undiscounted
reward. Do not describe this bounded ledger as discounted potential-based invariance.
Report signed return,novelty and refunds separately in evidence. Old native field
qualification stays valid; its reward ledger is an earlier frozen iteration.

## Risks / Trade-offs
The approximate graph field is not an exact continuous shortest path. Boundary
patch changes can withhold real progress; native qualification and signed probes
are required. One positive line is not a universal route or body clearance proof.
Inherited corner bias and sparse hits may persist after correcting this signal.

## Migration Plan
Add an explicit v5 opt-in requiring existing firing mode. Refuse v4 resume under
v5 before environment creation. Retain default v4. Native qualification must
precede a separately recorded child-lineage migration/learning plan; preserve all
parents and their normalization/optimizer artifacts. No automatic conversion.
Transport/action failure cleanup remains release/disconnect/normal owned exit.
