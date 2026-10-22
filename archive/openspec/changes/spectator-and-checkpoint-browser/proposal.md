## Why

Roadmap item 10: the user wants to watch inference from random play to learned play and pick
a saved checkpoint, without any silent training and without monitor capture or desktop input.

## What Changes

- Add `spectator.py`: checkpoint browser, deterministic `spectate` runner, policy-frame replay
  writer, and a `main(argv)` CLI with `list` and `watch`.
- Modes are explicit labels: `random`, `scripted-baseline`, `checkpoint:<id>`.

## Scope and non-goals

- Offline contract only, on the toy simulator. Terminal text output only.
- Not in scope: real-game control (needs an explicitly injected env), model loading for
  checkpoints (a loader is injected), ordinary-game-speed pacing, training while watching.
- This change MUST NOT be archived until real-game evidence exists.

## Dependencies and risks

- Depends on checkpoints, baselines, env, episodes, recording and evaluation report format.
- Risk: toy simulator behaviour may not match real-game pacing and stop latency.

## Acceptance criteria

- Offline: listing flags incompatible checkpoints; identical seed gives identical output;
  output and recordings contain no oracle data; incompatible checkpoints are rejected.
- Pending real game: replay a saved model at game speed, stop and recover control.

## Impact

New module `spectator.py`; no change to wire protocol or checkpoint format.
