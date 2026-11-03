# Recording human demos

A new lineage with contract `pretraining: demo_bc_v1` starts from a policy that first imitates
human play (behaviour cloning), then improves by RL. This page is for the human who plays.
OpenSpec change: `openspec/changes/demo-pretraining-v1`.

## Before the first recording

1. Stop training: `Train-Stop.cmd`. Recording and training share the game and port 9528.
2. Deploy the updated observer mod once (the `demo_record_v1` capability), the same way as for
   training.
3. The game keeps its Steam launch option `--luadebug` (already set for training).

## Record

1. Run `Record-Demo.cmd` in the project root. It waits for the game.
2. Start the game from Steam and play. The mod connects by itself within a second or two. The
   window prints a status line about every 30 seconds.
3. Each game session becomes one file in `runs/demos` (`<time>-<session>.jsonl.gz`). Quitting to
   the menu, dying and starting new runs are all fine.
4. Close the window or press Ctrl+C when done. The file is flushed every second, so a crash loses
   at most the last second.

During a loading screen or an alt-tab pause, a short receive timeout does not end the recording.
The recorder prints `waiting (game paused or loading)` once for a silent gap, keeps listening in
short intervals, and closes the session after 30 minutes without a snapshot. A real disconnect
still creates a new recording when the game reconnects.

New recordings include the run start seed as oracle metadata, not as a policy input. The dataset
can join adjacent files from the same apparent run using the player's alive state, timing, frame,
stage, stage type and character; it also checks the seed when both files have one. This allows
older seedless recordings to be grouped, but cannot prove identity. Cache keys change when the
replay rules or any grouped recording change; existing raw recordings are never rewritten.

Check what was recorded:
`.venv\Scripts\python.exe -m isaac_threrisaifuture.demo_dataset runs\demos`
(steps, minutes of play and the label mix per action head).

## How to play

The policy learns to do what you do, so play the way you want it to play:

- Character Isaac, normal mode, new runs (as in training). No mods that change the game.
- Clear rooms: shoot enemies, dodge projectiles, then leave through a door to a new room. Explore
  the floor, take items, go down when the floor is done.
- Keep moving with purpose. Long idle stretches teach the policy to stand still.
- Move mostly along one axis at a time. The policy has 5 move choices (none, left, right, up,
  down): a diagonal is recorded as the axis you move faster along.
- Use bombs, the active item and pills/cards when they help, not to test them.
- Dying is fine: it ends a sequence, the next run starts a new one.

## How much

Training refuses fewer than `demo.min_steps` (20000) decision steps, about 70 minutes of active
play at 5 decisions per second. 2-5 hours is the target; more hours on more varied floors help.
Recordings can be added later: the next session uses all files in `runs/demos` for the BC
regulariser without a new lineage (only pretraining needs them before `--initialize`).

## Start the new lineage

1. Rename the reward v13 run: `runs\pure-v4` to `runs\pure-v4-reward-v13`.
2. `Train-Start.cmd --initialize`. Pretraining runs first (minutes on the GPU) and writes
   `runs\pure-v4\seed-1\pretraining.json`: holdout accuracy per head before and after, against
   the majority-class baseline. Then RL starts from the checkpoint at step 0.

## Privacy

Recordings hold game state and button presses only: no screen, audio or other input.
