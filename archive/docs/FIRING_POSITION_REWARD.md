# Firing-position reward

`--firing-position-reward` enables the experimental `live-firing-v4` reward
contract. It is off by default and requires the combat gate and measured-grid
auto-navigation. The conservative session runner does not select it. Existing
`live-conservative-v2` and `live-firing-v3` checkpoints cannot be resumed for
training under this contract. There is no automatic migration or fresh-model
fallback. Keep the original model and normalizer intact.

## What earns credit

The negotiated `firing_geometry_v1` channel supplies reward-only evidence about
ordinary tears: measured TearRange, a visible vulnerable enemy and measured grid
cells with positive native projectile-line checks. Unsupported weapons, special
tear flags and missing APIs produce explicit unsupported/unavailable status.
There are at most32 line queries per sample. Native API correctness still requires
qualification; the Lua harness is not installed-game evidence.

Candidate positions must be walkable, within range minus20 units, at least80 units
from the enemy and within8 units of a cardinal firing axis. Python searches the
bounded walking grid for a route to a positively checked candidate. Walking
reachability alone never establishes projectile clearance. These margins are
versioned hypotheses, not an optimal strategy.

Actual movement greater than 0.5 units can earn a small bonus for a new record
for the same physical room and visible target. A multi-source bounded BFS measures
graph distance to positively checked firing cells; bilinear interpolation removes
the previous mandatory detour through the current cell center. All nonzero-weight
interpolation corners must be measured walkable and reachable. Missing support
withholds shaping. This is not an exact continuous shortest-path calculation.

Records are separate for each target, with one shared allowance of at most 0.25
per physical room within a collector. Target switches establish unpaid baselines;
standing, shooting, resets, room reentry, and returning to an old target do not
renew credit. Comparisons use the fixed before-frame target and candidate cells
positively checked in both samples. Histories are bounded to 4096 rooms and 65536
room/target records and fail explicitly rather than evicting records.

Historical v3 functions remain available only for faithful replay. The production
flag now selects v4; no old v3 checkpoint is silently reinterpreted. The saved trace
replays to its exact v3 total, while v4 produces a smaller total and withholds most
corner endpoints because interpolation support is incomplete. See the
[corrective implementation report](../reports/2026-10-21-coherent-combat-geometry.md).

The ledger is collector-local. An external process restart establishes a fresh
baseline and must be recorded as a trajectory discontinuity; exact reward-ledger
restoration is not implemented. This is capped novelty shaping, not a claim of
policy-invariant potential shaping.

## What stays measurable separately

The default 649-element policy encoder/schema1 remains unchanged. Optional
`--combat-geometry` selects a separate 723-element schema2 with explicit range,
ground blocking and projectile clearance; see [observable geometry](COMBAT_GEOMETRY.md).
No target-seeking controller replaces the learned actions. Management navigation
earns no shaping. Existing damage, clear, injury and death coefficients remain.
The no-progress guard uses registered combat progress, never this bonus. A kill
cannot be inferred merely from an enemy disappearing.

Before learning, qualify the native weapon/range/clearance telemetry in a finite
frozen-policy shadow-reward audit. Then declare a compatible lineage and compare
damage dealt, damage taken and verified clears under comparable scenarios, starting
with5 minutes, then15-30 minutes. A changed reward or updated weights do not prove
better play. Hour/four-hour stages remain later qualifications.

The ordinary-tear native shadow audit passed:range260,five positive candidates,
8 movement bonuses and zero bonus for549 stationary pairs. It used a frozen v2
policy and did not train. The progress guard stopped at about60s; no five-minute
duration or improved-play claim follows. See
[native audit](../reports/2026-10-21-native-firing-shadow-audit.md) and
[offline evidence and self-review](../reports/2026-10-21-firing-position-shaping.md).

The explicitly authorized five-minute inclusive-startup training trial created a
separate v3 warm start from preserved t21760. Latest7951bf19-s20-t24064 saved2304
new steps. The reward signal fired but corner stagnation remained;no observed
damage/clear gain was established. No longer stage is running. See
[pilot results](../reports/2026-10-21-firing-training-pilot-results.md) before any
new experiment. Ordinary direct v2->v3 resume remains refused; current v4 also refuses v3 resume.
