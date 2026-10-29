# Training sessions (pure profile)

`python -m isaac_threrisaifuture.session_runner` supervises native Windows training.
The pre-refactor finite-session guide is in `archive/docs/TRAINING_SESSION.pre-pure.md`.

The finite run from source `fc80cd5` resumed t31744 without initialization and
stopped early October 29 at 21:29:25 CET after a Windows status-file access fault,
final checkpoint t102400. All nine captured statistics were filled in 69/69 new rows;
pause_ok was 69/69 (first hour 15/15), so the live pause flag stayed enabled.
The first learner exited 0/cleanup empty. The supervisor automatically began a second
startup before the stop guard took effect; it made no progress and required worker
termination (exit 1; cooperative release unverified). All training/game/owner processes
and port 9528 are now absent; stop.forever remains. No manual retry or new run.
The planned October 30 09:00 CET deadline was not reached.
See the [final report](../reports/2026-10-30-schema8-train-statistics.md) and
[finite plan](../reports/2026-10-29-train-statistics-resume-plan.md).

## Forever mode

```powershell
.\Start-Pure.cmd "<Isaac install dir>" "<path to log.txt>" --initialize   # first ever
.\Start-Pure.cmd "<Isaac install dir>" "<path to log.txt>"                # later
```

`Start-Pure.cmd` runs `session_runner --forever --run-root runs\pure-v4`. It:

- reads `configs/training-pure-v4.yaml` before every session, so edited
  `hyperparameters` apply to the next session without a new lineage;
- runs bounded sessions back to back (`budget.wall_time_minutes`, at most the 8 h
  Lua lease), each resuming `latest`; the first session starts a fresh model only
  with `--initialize`;
- writes a fresh approval with unlimited restarts per session (New Run after death
  and after stall-watchdog restarts);
- stops on `runs\pure-v4\supervisor\stop.forever`, Ctrl+C, the disk cap
  (`budget.disk_limit_mb`), a refused lineage or config, or
  `budget.max_consecutive_faults` consecutive faulted sessions;
- keeps the 20 newest session log folders under `runs\pure-v4\supervisor`.

Results: `runs\pure-v4\supervisor\forever.json` (stop reason and sessions),
`runs\pure-v4\metrics\episodes.csv` (one row per episode),
`runs\pure-v4\metrics\train.csv` (one row per optimizer update: entropy, losses,
explained variance, KL, clip fraction and the action mix per head),
`runs\pure-v4\seed-<seed>\checkpoints` (5 newest plus every 200th rollout; ~52 MB each).

`episodes.csv` also has `last_room_clear` (0/1, clear flag of the room the episode ended in)
and the `stall_*` columns. They are filled only for episodes truncated by the stall watchdog,
from the last snapshot before the restart, and are empty for deaths. They show why an agent
stalled: room clear flag, type and shape; alive enemies (observed and oracle counts);
invulnerable, flying and boss enemies; the `type.variant` kinds present (`stall_enemy_kinds`,
sorted, `;` separated); the distance in px to the nearest enemy; open doors and open doors into
unexplored rooms; half hearts; and `stall_seconds_in_room` (game updates since the last room
change or the episode start, divided by 30). Metrics only, never policy inputs.
An older `episodes.csv` header is rewritten once with the full header; old rows get empty cells.

Timing columns in `train.csv`: `rollout_seconds` is the wall time of the rollout and
`update_seconds` the pause before it (optimizer, checkpoint, idle). For live runs
`game_wait_seconds` is the time spent waiting for game snapshots and `command_seconds`
the time spent sending commands and waiting for their acks, both summed over the rollout;
`snapshots_per_step` is the snapshots taken per env step. Python time (policy, encoding,
reward, wrappers) is `rollout_seconds - game_wait_seconds - command_seconds`. The cells are
empty for sim backends. A `train.csv` written before these columns is rewritten once with
the new header at the next start; its old rows keep empty timing cells.
The dashboard shows the three shares of the rollout time.

**Paused updates.** With `live.pause_during_updates: true` (not hashed) the worker releases
input, presses Esc through the guarded game keyboard and waits up to 3 s for a `paused`
snapshot at each rollout end. At the next rollout start it presses Esc again and waits for
`active`. The game therefore stands still during the optimizer update and checkpoint. The game
window should stay in the foreground; if another window holds the focus, the keyboard taps Alt
and asks Windows again (up to three tries), and a refusal names the window that kept it. A working pause writes an `update_paused` event with its
seconds; failures never stop the session: `update_pause_skipped` and `update_resume_failed`
events in `events.jsonl` give the reason, and the `train.csv` columns `pause_seconds` and
`pause_ok` (1 or 0) show each update. `Observer perf` windows also show a pause: game updates
per 10 s drop from about 300 while the game is paused. Many `pause_ok` 0 rows mean
the keyboard path is not working; check focus first.

The game side is measured by the observer: while streaming it writes an `Observer perf`
line to Isaac's log.txt about every 10 s (updates, renders, snapshots, and milliseconds
inside the update and render callbacks, snapshot capture and JSON encoding). Summarize it
with `python scripts/lua_perf.py "<path to log.txt>"` (`--since TEXT` keeps the windows after
the last line containing TEXT).

## Single session

Without `--forever` the runner keeps its explicit finite mode: `--config`,
`--run-root`, a new `--output`, `--parent-id`, `--seed`, `--seconds`,
`--disk-bytes`, and either `--time-budget-only` or explicit `--steps` and
`--max-restarts`. Use it for bounded acceptance checks.

## Frozen evaluation

Compare checkpoints (or a random baseline) under exactly the training protocol: same action
repeat, reward v9, stall watchdog and restarts, but no learning and no checkpoint
writes. Stop forever training first; one game runs at a time. One session per
policy, one folder per session (a root that already has episodes is refused):

```powershell
.\Start-Eval.cmd "<Isaac install dir>" "<path to log.txt>" t102400 3600 "runs\pure-v4\seed-1\checkpoints\<checkpoint id>"
.\Start-Eval.cmd "<Isaac install dir>" "<path to log.txt>" random 3600
.\Start-Eval.cmd "<Isaac install dir>" "<path to log.txt>" random-prior 3600
```

`random` is uniform over every action head, so its use head presses a bomb, active item
or pill/card 75% of the time. `random-prior` draws move and shoot uniformly and uses
the head like a fresh model: none with the config's
`contract.use_head_initial_none_probability` (0.85), the rest split evenly. Prefer it as
the baseline for checkpoints. It is seeded like `random`, takes no `--checkpoint` and is
selected by `--evaluate random-prior`.

The same without the wrapper (`--seconds` 60..14400; seed, disk cap and restarts are
derived):

```powershell
.venv\Scripts\python.exe -m isaac_threrisaifuture.session_runner --game "<Isaac install dir>" --game-log "<path to log.txt>" --config configs\training-pure-v4.yaml --run-root runs\pure-v4-eval\t102400 --output runs\pure-v4-eval\_sessions\t102400 --seconds 3600 --evaluate checkpoint --checkpoint "runs\pure-v4\seed-1\checkpoints\<checkpoint id>"
```

- `--checkpoint` names one exact checkpoint directory (never `latest`); it must match
  the config contract hash, seed and reward contract. Actions are sampled, with the
  config seed, like in training; the saved observation statistics are applied and not
  updated. The checkpoint files are hash-frozen and re-checked at the end.
- `--run-root` is the new evaluation output root. It must not be, contain or lie
  inside the training run root, and must hold no `checkpoints` folder.
- A normal stop at the time limit ends `completed` in `<output>\result.json`.
  Stop early with `<output>\stop.request`.
- Results: `<run-root>\metrics\episodes.csv`; events in
  `<output>\events.jsonl` (`evaluation`, `evaluation_result`).
- The session needs the full time limit for enough episodes: compare only runs with
  similar `--seconds`, and read the stall interval before the means.

Compare finished roots (offline, read-only):

```powershell
.venv\Scripts\python.exe scripts\compare_eval.py runs\pure-v4-eval\t102400 runs\pure-v4-eval\t204800 runs\pure-v4-eval\t237568 runs\pure-v4-eval\random runs\pure-v4-eval\random-prior
```

One row per root: episodes, death/stall/left-start-room/any-clear shares, mean damage
fraction with its standard error, kills, rooms cleared, half hearts lost, return, max
stage and the 95% Wilson interval of the stall share. The result is descriptive; the
game seed is not controlled, so differences within the intervals are not evidence.
`damage_1k`, `kills_1k` and `clears_1k` are totals per 1000 steps. They do not depend
on how episodes end, so they compare policies that die at different rates; the stall
share does not. `--baseline random-prior` adds a table of each run's rate difference to
that root with a 95% bootstrap interval over episodes. One 3600 s session gives
intervals about В±3 wide on `damage_1k`; use two sessions per policy for acceptance.
`live_evaluation.py` / `evaluate-live` is superseded for pure lineages.

## Guards kept

Steam launch and guarded file-2 Continue, loopback-only bridge, frozen source/
config/mod hashes per session, input release on stop and fault, closing only the
owned game, and removing only the exact owned approval.

## Dashboard

`.\Start-Dashboard.cmd` serves a live, read-only view of `runs\pure-v4` at
http://127.0.0.1:8765 (loopback only, standard library, works offline). It polls
every 5 seconds: episode counts, rolling learning curves, death/stall mix, reward
breakdown, latest checkpoint and supervisor state. It reads `metrics\episodes.csv`
(including its `wall_time` column), `supervisor\session-*\status.json`,
`supervisor\forever.json` and each `seed-*\checkpoints` manifest, and writes nothing.
It can run before, during or after training; stopping it never affects training.
For a look without real data: `python scripts/make_dashboard_sample.py`, then
`python -m isaac_threrisaifuture.dashboard --run-root reports/local/dashboard-sample`.
