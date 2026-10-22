# Evidence clarification: door1, corner2 and enemies X/Y

The user supplied an annotated screenshot on2026-10-21 to explain the trajectory:
spawn at the right door1, pass along the rock barrier near enemyX, then move into
the bottom-left corner2 and shoot upward toward enemyY. This is user-supplied
visual context, not a new live-game check. No screenshot was captured by the agent.
The private attachment is not copied into Git.

Readback of the existing paired native trace maps the landmarks consistently:

| Landmark | Existing game-world coordinates | Trace identity |
|---|---|---|
|Right entry1|Initial player(560,280)|First policy frame48205 |
|EnemyX|Enemy(560,360)|entity2, shaping target for first36 decisions |
|EnemyY|Enemy(80,200)|entity1, shaping target for remaining2470 decisions |
|Bottom-left corner2|Player approximately(70,410)|Observed stagnation cluster |

The first17 bonuses, ending at decision34/player approximately(302,349), occur
during the approach to a measured firing position around the X-side rock barrier.
They are not rewards for standing in corner2. A useful firing route may initially
move farther from the enemy's body while going around a blocker; straight enemy
distance is not the reward criterion. The separate open-corridor distance-sign
counterexample remains valid, but does not establish that these17 native bonuses
were all erroneous. This distinction is necessary when interpreting the screenshot.

In the final recorded state, the policy receives a visible obstacle point at
(80,240), between corner2 and enemyY at(80,200). That point is one of the12
obstacles actually exported by Lua. The encoder has24 slots, but source
`entity_caps.obstacle=12` limits the transmitted points first. Source overflow41
includes omitted room obstacles; do not infer which unseen rock subtype each is.
The earlier report's24-actual-obstacle claim is corrected to12.

The representative walkable lattice cell(80,400),index106, is within ordinary-tear
range of Y and cardinally aligned, but is absent from the positively clear firing
cells. Overflow is0, so eligible candidate queries were not truncated. Given the
collector's conditions, its projectile-clear query did not succeed. Native positive
cells for Y are instead(160,200),(200,200),(240,200),(280,200),(320,200):positions
on Y's right. This supports the user's blocked-upward-shot interpretation without
claiming that every actual tear impact was observed. The exact corner pose is
approximately(70,410), not the queried lattice center(80,400).

Conclusion: there is evidence of an ineffective geometric representation/learned
obstacle response, not total absence of the relevant stone from policy input.
The actor receives generic point coordinates, without obstacle collision class,
projectile-blocking flag, weapon range or explicit current-target shot clearance.
The reward-only geometry knows more than the actor. Coordinates alone have not
produced a learned rock detour and firing decision in this trial.

Priorities are refined accordingly: retain the distance-sign/target-record fixes,
and design explicit legitimately observable weapon/target/blocking geometry for
the policy rather than relying solely on more time or a larger bonus. Merely
increasing the obstacle count does not establish shot understanding. Any source
cap/feature change needs its own declared compatibility and normalization plan;
do not silently fill previously empty slots for the old model. No production
change, runtime, new training or model migration was performed in this clarification.

Verification: primary inspected the attached image, current Lua cap and encoder,
and first/final raw native endpoint records. No numerical clipping was implicated.
No source change;full tests/native checks not_run. Models t21760/t24064 preserved.
See [original diagnosis](2026-10-21-firing-policy-diagnosis.md).
