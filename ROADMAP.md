# isaac-threrisaifuture roadmap

Milestones and acceptance for the pure self-learning direction (since 2026-10-22,
`docs/UPDATE_DECISION.md`). Current state lives in [STATUS](docs/STATUS.md);
requirements in `openspec/specs` and `openspec/changes`. The hinted roadmap is
preserved in `archive/docs/ROADMAP.pre-pure.md`.

## P0. Foundation (done, kept)

Steam launch, guarded file-2 menu entry, typed loopback bridge, bounded native
actions, entity observation, death restart, live training loop and transactional
checkpoints have recorded acceptance at their declared scopes.

## P1. Pure refactor (`pure-self-learning-v1`, offline done, native pending)

Acceptance:

- Offline: archive and trim; observation schema 3; action v2 with use head;
  reward v2 with exploit tests; restart command and stall watchdog; contract/
  hyperparameter lineage split, retention, metrics; forever supervisor. Full gate
  green on Windows (`scripts/Check.ps1`).
- Native (task 4.3): one bounded session shows schema 3 frames with plausible
  inventory/room/collectible values, an accepted use-item press with a visible game
  effect, a stall restart, a death restart and a reloadable `pure-v1` checkpoint.

## P2. Long continuous training

Start the forever supervisor on the fresh `pure-v1` lineage. Acceptance is
measured, not assumed:

- Stable operation: sessions chain for at least 24 h with fault rate and stall
  restarts reported; no unexplained stops.
- Learning signal: compared with a random policy over the same number of
  episodes, higher mean damage dealt and rooms cleared per episode in
  `metrics/episodes.csv` and in frozen evaluation (watchdog off).

## P3. Room and floor competence

Frozen evaluation shows the agent clears most Basement rooms it enters, reaches
the first boss and beats it in a reported fraction of runs, with denominators,
seeds and faults.

## P4. Items and progression

Evidence that pickups, item use and held collectibles change outcomes: e.g. runs
with more items reach deeper floors; use-head actions correlate with damage or
survival. Any new observation fact or reward term needs its own OpenSpec change
and exploit tests.

## P5. Dead God

Long-term goal through gameplay on file 2. Requires sustained full-run success;
achievement eligibility stays a separate evidence issue.
