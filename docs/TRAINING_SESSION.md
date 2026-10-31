# Training sessions (pure profile)

`python -m isaac_threrisaifuture.session_runner` supervises native Windows training.
The pre-refactor finite-session guide is in `archive/docs/TRAINING_SESSION.pre-pure.md`.

Reward v10 was stopped by the human October 30 at 13:26:04 CET, final
`3043a54c-s1-t63488`,290 completed episodes. Final learner exited 0, fault=null,
cleanup empty; game/worker/owner/listener closed and stop.forever retained.
The 15-minute graph-label check passed. The earlier Continue-only startup failure
and subsequent explicitly authorized file2 New Run are recorded separately.
[Final report](../reports/2026-10-31-reward-v10-training.md).
Reward v9 schema8 remains at `runs/pure-v4-reward-v9-schema8`, final t102400.
Reward v11 / observation schema9 was initialized once October30 at13:13UTC,
source3264207, then stopped early October31 at05:11:30UTC /06:11:30CET on a file2
Continue confirmation fault during automatic lease rollover. Final t253952 is46048
saved steps short of300000;1180 episodes/254782 observed steps/248 train rows.
Sessions1/2 exited0 normally; startup sessions3/4 exited1 and required termination,
so cooperative release remains unverified. The launcher's exit0 does not erase them.
No game/worker/finite owner/Start-Pure/listener9528/deployed authorization remains;
stop.forever is retained. Final model/normalizer/counts hashes and all32 archived
v10 files were verified. No manual retry, fallback New Run or deadline extension.

[Final report](../reports/2026-10-31-reward-v11-schema9-training.md),
[150k report](../reports/2026-10-30-reward-v11-schema9-150k.md),
[50k report](../reports/2026-10-30-reward-v11-schema9-50k.md),
[finite plan](../reports/2026-10-30-reward-v11-schema9-native-plan.md).
The initial18-minute passive check passed encountered item/count/statistics cases;
active/tagged/Blind coverage remains unverified. Offline Check1543 including Lua/no
skips, strict OpenSpec28/28. Native tasks remain open. The November1 deadline was
not reached; monitoring is finished and further training needs a human decision.
Sessions now start a New Run when the fresh log verifies that file2 has no game, as after the
death 3 s before the session 2 lease end (openspec change `session-start-new-run-fallback`).
Reward v12/schema9 launched once October31 at06:31:15UTC /07:31CET, source4c58937,
contract1a6d8146f5e89b7bdad14fe21d3afa9cc1f5c4192b8e5f24cefb6bbab0e0c8d8.
The v11 root is now archived with all77file hashes unchanged. No mod redeployment.
Check1569includingLua/no skips andstrictOpenSpec30/30 passed. Initial menu New Run
on verified file2 absence passed. The18-minute audit passed22/22 stalls at30.000..30.188s,
col_stall-4/col_stagnation-7.02,counts SHA valid,1035 frames and4 filled train rows.
First50k checkpoint1a6d8146-s1-t50176:296episodes/50127observedsteps/48trainrows.
At common(0,50000],exit64.4%,stalls73.9%,rooms1.692,kills4.102/1k,stage2zero;
v11 exit70.5%,stalls67.0%,rooms1.795,kills2.942/1k.
[50k comparison](../reports/2026-10-31-reward-v12-schema9-50k.md).
First150k checkpointt150528:882episodes/151375observedsteps/147trainrows.
Common(0,150000]:v12 exit79.8%,stalls71.7%,rooms1.876,kills6.264/1k;
v11 81.9%/61.9%/1.929/4.426,stage2zero. Goals remain unmet, not stop rules.
[150k comparison](../reports/2026-10-31-reward-v12-schema9-150k.md).
First8hrollover completed14:30:02UTC:exit0/faultnull/cleanup[]/writes_skipped0;
Continue verified,resumeTrue,parentt126976,samehash,newcheckpoint128000.
Conditional death/no-game -> resumed New Run unencountered, task still open.
[Audit report](../reports/2026-10-31-reward-v12-schema9-native-audit.md).
Stopped by the human October31 at17:22:56UTC /18:22:56CET, before the target/deadline.
Finalt173056:173056/300000 savedsteps (126944 short),1032episodes/173786observedsteps/
169trainrows. Both sessions exit0/faultnull/cleanup[]/status_writes_skipped0;
no game/worker/finite owner/launcher/listener9528/deployed authorization remains.
stop.forever retained; all77v11archive hashes matched. No retry/extension.
[Final report](../reports/2026-10-31-reward-v12-schema9-training.md).
Native tasks remain open; further training needs a human decision.
[Launch receipt](../reports/2026-10-31-reward-v12-schema9-launch.md),
[finite plan](../reports/2026-10-31-reward-v12-schema9-native-plan.md).


Full-batch structured learner launched once October31 at18:48:31UTC /19:48CET,
source2b475b9,contractee4f65999d3a8cf0c85dabd5d887e360fd0823a164814bd20753d6dca91ac703.
Check1583/Lua/no skips,Smoke passed,strict31/31;v12archive52files hashes unchanged.
Lua unchanged,dashboardclosed,Continue verified;native20minute audit pending19:08:31UTC.
Stop firstsaved>=150k or November1 18:48:31UTC,whicheverfirst;no retries/extensions.
Reports75k/150k compare3+roomshare/roomsper episode/post75kgrowth withv11 andv12.
[Launch receipt](../reports/2026-10-31-full-batch-structured-launch.md),
[finite plan](../reports/2026-10-31-full-batch-structured-native-plan.md).


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
- treats a stall as the end of the episode for learning (terminated; `episodes.csv` still says
  truncated / stall), and keeps the reward v11 novelty counts across runs in
  `novelty_counts.npz` inside every checkpoint directory (a v11 resume without it is refused;
  evaluation never writes counts);
- trains with `n_epochs` 10, `batch_size` 1024 (one minibatch of the whole rollout per epoch)
  and `target_kl` 0.03 (an update took about 19 s on the development Mac; native time is
  unmeasured), with the game paused;
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
unexplored rooms; `stall_goal_hops` (reward v10/v11: the best door term, rooms to cross plus the
in-room share, two digits; empty when unknown); half hearts; and `stall_seconds_in_room` (game updates since the last room
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

Steam launch and guarded file-2 Continue (or a New Run when the fresh log verifies that file2
has no game, e.g. after a death at the lease end; `menu_entry_resolved` in menu.jsonl),
loopback-only bridge, frozen source/
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
