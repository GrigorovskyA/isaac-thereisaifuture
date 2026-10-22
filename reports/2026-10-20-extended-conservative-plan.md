# Experiment plan: extended conservative-v2 continuation

Declared before execution on 2026-10-20, Europe/Amsterdam, following the user's
explicit request for a longer experiment. This is a continuation of the tested
conservative-v2 model, not new random initialization or a reward migration.

## Controlled budget extension

Source: runs/live-conservative-v2-development-20261020/seed-20/checkpoints/
92969b7f-s20-t1536. Preserve its entire root/latest pointer and legacy t8960.
The source config has a4096-step ceiling. Create the separate extended config
by changing only budget.total_timesteps to12288 and wall_time_minutes to12.
Every non-budget field, seed20, reward live-conservative-v2, algorithm,
observation/action schema, weights, optimizer, normalizer and RNG state must match.
No change to strict training compatibility checks is allowed.

Primary performs an explicit local artifact migration before dispatch: copy the
two binary state files byte-for-byte into a new checkpoint at the same t1536,
write the new config hash and new ID, retain the source ID as parent, preserve
all other manifest values, then record hashes, source/new config snapshots and
the exact changed fields in budget-extension.json. Read back with the ordinary
strict loader and independently load model/statistics. No learning occurs here.
Missing or mismatched source stops; an existing destination is not overwritten.
The new root is runs/live-conservative-v2-extended-20261020. Each native invocation
uses --resume, including the first; absence or incompatibility stops the experiment.

## Global finite budget

Three enumerated sessions at most (session1,session2,session3), one worker,
no concurrent game control, retries or recovery sessions. Global wall cap45min
from wrapper start plus an absolute latest finish recorded before dispatch;
offline gates have an additional bounded preparation allowance. No renewal.
Global cumulative target12288 saved steps (10752 additional from1536), aligned
to rollout256. Global new output cap512MiB, including all three session logs and
checkpoints; separate offline temp growth cap512MiB. Stop on any cap or fault.

Each session: one Steam launch, explicit guarded New Run on file2 after the
previous terminal death, initial active Isaac verification before learner creation,
12min learner cap,15min outer cap,10 natural deaths and9 structured restarts,
13.5min approval lease/max_restarts9. Native input stays on the structured bridge;
menus only use the accepted local foreground/ownership guards,8keys/60s/2MiB.
Gate wait90s,navigation scale5 (1280 commands/450 pulse seconds/20 transitions),
max infrastructure faults0. Existing Continue must not be discarded.

Session2 is allowed only after session1 ends normally on its tenth death,
with all cleanup successful, no faults and at least one newly saved checkpoint.
Session3 has the same requirements relative to session2. Each starts from the
exact latest compatible checkpoint produced by the previous session; the worker
cannot choose a different model or reset statistics. Fresh approval per enumerated
game session is authorized; it does not extend any previous lease/global deadline.
At most30 deaths/27 restarts across the experiment. Reaching12288, wall/disk/gate/
navigation limits, a refusal, missing progress, unknown stop, cleanup failure or
any infrastructure fault ends the entire experiment without another session.

Prepared learner arguments (through the same read-only startup guard as baseline):

```text
live --mode train --config configs/training-live-conservative-v2-extended.yaml --resume --seed 20 --steps 12288 --minutes 12 --max-faults 0 --combat-gate --auto-navigate --gate-wait-minutes 1.5 --navigation-budget-scale 5 --max-deaths 10 --confirmed-save-slot 2 --connection-timeout 90 --out-dir runs/live-conservative-v2-extended-20261020
```

## Acceptance and scientific limits

Run full Windows gates and synthetic RL smoke before runtime; these do not prove
gameplay. Freeze source/config/helpers, exact commands, migrated checkpoint
lineage, absolute deadlines and allowed outputs before delegation. The worker
executes only the primary's prepared finite wrapper and reports actual exits.
Close each owned game normally, release the listener/actions and remove only its
unchanged exact approval before another enumerated session. No save/Cloud/Steam
launch-option edits, forced deaths, console unlocks, third-party mods or screenshots.

Primary independently verifies logs, native run/death/epoch evidence, source hashes,
all checkpoint parent/step/config/reward/seed values, PPO updates, normalizer
counts, saved/unsaved decisions, every outcome and cleanup. Old roots remain
byte-identical; only the new extended root advances. Partial rollouts are reported,
not counted as saved learning. No wins/clear-rate or improved play claim follows
from training return. This remains one development seed with test held out.
Actual revival/champion phase coverage remains pending; no mechanic fix is claimed.
