# Training sessions (pure profile)

`python -m isaac_threrisaifuture.session_runner` supervises native Windows training.
The pre-refactor finite-session guide is in `archive/docs/TRAINING_SESSION.pre-pure.md`.

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

## Single session

Without `--forever` the runner keeps its explicit finite mode: `--config`,
`--run-root`, a new `--output`, `--parent-id`, `--seed`, `--seconds`,
`--disk-bytes`, and either `--time-budget-only` or explicit `--steps` and
`--max-restarts`. Use it for bounded acceptance checks.

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
