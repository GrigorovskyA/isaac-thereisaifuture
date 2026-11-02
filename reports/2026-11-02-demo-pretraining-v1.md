# Demo pretraining v1: recording, dataset, behaviour cloning

Date: 2026-11-02. Author: Mac work copy `~/work/isaac`, base `4a6560d`, merged onto `b61f590` (STATUS). Not committed.
OpenSpec change: `openspec/changes/demo-pretraining-v1` (strict validation 37/37).

## Why

Reward v13 at 23-39k steps still moves almost at random (1.3-1.6 rooms per episode); the E3B
lineage needed 273k steps for about 2 rooms. The observation already holds the minimap, the doors
and every entity. The policy has to discover what they mean from scratch. Human demos give it a
starting behaviour, and RL improves from there.

## What changed

- Mod `mod/observer/main.lua`: capability `demo_record_v1`, always advertised, only with
  `entity_observation_v1`; refused with actions, restarts, the live loop, seeded restarts and
  native oracle kinds. In this mode the mod sends the oracle block at the live sample rate (50 ms)
  and `human_input`: one 14-bit mask per game update (held move, shoot, bomb, active, pill/card;
  triggered bomb, active, pill/card), at most 16 per snapshot, older ones counted in `dropped`.
  It injects nothing.
- `live_wire.py`: `HumanInput`, `DemoSnapshot`, `HUMAN_INPUT_BITS`. `observer_client.py`:
  `ObserverConfig.demo_record`.
- `demo_recorder.py`, `Record-Demo.cmd`, `scripts/Train.ps1 -Action Record`: refuses while a
  training supervisor runs; one `runs/demos/<UTC time>-<session>.jsonl.gz` per mod session
  (manifest line, then `{t, snapshot}`), flushed every second; menu-only sessions are deleted;
  a truncated tail is readable.
- `demo_dataset.py`: decision points every 6 game updates, observations exactly as the live env
  (event deriver, run progress and stall watchdog replayed on the receipt clock, visited cells at
  decision points), labels from the masks of the step's updates (most held move/shoot direction,
  a diagonal becomes the faster axis; a triggered use press). float16, cache
  `<recording>.bc-<key>.npz`. CLI `python -m isaac_threrisaifuture.demo_dataset runs\demos`.
- `demo_learning.py` and `learner.py`: `DemoLearner` (normalizer fit, masked NLL over 64-step
  windows, normalization on the policy device, holdout of 10% of the sequences, best holdout
  weights kept, early stop after 6 checks of 250 steps without improvement), and a BC phase after
  each PPO update (32 steps at `bc_coef` x lr, decaying to 0 at 1M steps; logs `demo_bc_loss`,
  `demo_bc_coef`, `demo_approx_kl` to the SB3 logger, not `train.csv`).
- `training.py`: contract `pretraining: none | demo_bc_v1` (`none` is not hashed: older hashes
  unchanged), `demo` config section (not hashed, recorded in manifests). A fresh `demo_bc_v1`
  lineage loads the demos before the game is used (fewer than `min_steps` 20000 refuses), fits
  the normalizer, pretrains, writes `seed-1/pretraining.json` and publishes a step-0 checkpoint.
  On resume, demos are only used for the regulariser (skipped once it decays to 0).
- `configs/training-pure-v4.yaml`: `pretraining: demo_bc_v1` and `demo:` with
  `recordings: [runs/demos]`. New contract hash
  `c8a7486b9806f2cd76e3aab5324163659dfb4b3ae41a619ed61a362be8936121` (reward v13 `54be12af...`
  stays pinned in `test_e3b_count_intrinsic` as `V13_HASH`).
- Docs: `docs/DEMO_RECORDING.md` (new, for the player), STATUS, TRAINING_SESSION (CRLF kept),
  RUNTIME_AUTHORITY, RL_DESIGN, README.

## Checks (macOS)

| Check | Result |
|---|---|
| `scripts/check.sh` (ruff, format, mypy win32, pytest incl. Lua) | 1771 passed, 1 skipped, 2 failed (the known macOS-only `test_menu_entry` struct layout and `test_session_runner` worker module) |
| OpenSpec `validate --all --strict` | 37/37 |
| `scripts/smoke_rl.py` | passed |
| Dataset fidelity: same snapshot stream through `LiveBackend`+env and through `load_demos` | identical vectors (float16) at repeat 3 and 6 |
| Native game | not run |

New tests: `test_lua_demo_record.py` (21), `test_demo_recorder.py` (20), `test_demo_dataset.py`
(19), `test_demo_learning.py` (14).

## Known limits

- Only the real game verifies `Input.IsActionPressed/IsActionTriggered(button,
  player.ControllerIndex)` from `MC_POST_UPDATE` for keyboard and controller.
- BC speed on CPU is about 1.1 s per step (1024 rows); on the GPU it is not measured. The
  pretraining log reports it (`on_progress("pretraining", ...)`).
- The 5-way move head cannot express diagonals; the raw masks allow a later re-label.
- The BC Adam state is not checkpointed (fresh each session).
- The demo uses exactly 6 updates per step; live steps are a little longer because of latency.

## Reward v13 at the stop (read on the Mac, `runs/pure-v4/metrics`)

Stopped at `54be12af-s1-t80896`, 926 episodes (703 stall truncations, 223 deaths), max stage 1.
Per 10k steps, rooms per episode rose 1.25 -> 1.7 by 20k and stayed 1.6-1.8 to 80k; kills 0.4 ->
1.1-1.3 by 30k, then flat; room clears 0.07 -> 0.15-0.19; stall share 0.69-0.80 throughout.
At the last update: `move_down` 0.45, `use_none` 0.58 (`use_pillcard` 0.21, `use_active` 0.16),
explained variance 0.69. Plateau after 30k steps, as before: the reason for this change.

## Windows agent task

1. Wait until the user stops training with `Train-Stop.cmd` (check `Train-Status.cmd`: not
   running, stop file present). Never edit files while it runs.
2. Commit the 34 files of this change (list: `~/work/sync-demo-pretraining.txt` on the Mac; they
   are already on SMB once synced) with the message
   "Demo pretraining v1: human demo recording, BC dataset, BC pretraining and regulariser".
3. Run `scripts\Check.ps1` and record the counts.
4. Deploy the observer mod the usual way and verify the deployed hash equals
   `mod/observer/main.lua`.
5. Smoke recording (5 minutes, with the user playing): `Record-Demo.cmd`, play, Ctrl+C. Then run
   `.venv\Scripts\python.exe -m isaac_threrisaifuture.demo_dataset runs\demos` and check that the
   steps are about 5 per second of play, move labels are not all `none`, shoot labels appear in
   fights, use presses match what was pressed. Write
   `reports/2026-11-0X-demo-recording-smoke.md`.
6. After 2-5 hours of recordings (at least 20000 steps): rename `runs\pure-v4` to
   `runs\pure-v4-reward-v13`, verify the archived file hashes, then run
   `Train-Start.cmd --initialize`. Report `runs\pure-v4\seed-1\pretraining.json`: holdout
   accuracy per head before and after against `majority_accuracy`, `best_step`, seconds.
7. 20-minute audit, then 75k-step comparison against `runs\pure-v4-e3b` and
   `runs\pure-v4-reward-v13` at equal steps (rooms per episode, kills, clears, deaths, stall share,
   `move_*`/`shoot_*`/`use_none` shares).

## Rollback

Before commit: restore the 18 modified files from `b61f590` (`git checkout b61f590 -- <file>`) and
delete the 16 new files of the list. After commit: `git revert <commit>`. Recordings in
`runs/demos` are untracked and can stay. The reward v13 lineage resumes only with the old config
(contract without `pretraining`).
