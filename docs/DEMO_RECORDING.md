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

- Character Isaac if you can, normal mode, new runs (as in training). No mods that change the
  game. Other characters are recorded too, but training only uses those that play like Isaac
  (see below).
- Clear rooms: shoot enemies, dodge projectiles, then leave through a door to a new room. Explore
  the floor, take items, go down when the floor is done.
- Keep moving with purpose. Long idle stretches teach the policy to stand still.
- Move mostly along one axis at a time. The policy has 5 move choices (none, left, right, up,
  down): a diagonal is recorded as the axis you move faster along.
- Use bombs, the active item and pills/cards when they help, not to test them.
- Dying is fine: it ends a sequence, the next run starts a new one.

## Characters

The agent plays Isaac and its observation has no character identity, only stats and health.
Training therefore uses only the steps of characters listed in `demo.characters` of
`configs/training-pure-v4.yaml`: by default Isaac (0), Magdalene (1), Cain (2), Judas (3), ???
(4), Eve (5), Samson (6), Lazarus (8), Lazarus risen (11), Dark Judas (12), Apollyon (15) and
Bethany (18) and Tainted Isaac (21). Azazel, Eden, The Lost, Lilith, Keeper, The Forgotten and
The Soul, Jacob and Esau and the other tainted characters are skipped: their attacks, health or
core mechanic (melee, dash, crafting bag, form switch) work differently, and copying them would
teach Isaac the wrong moves. Skipped recordings stay on disk for a later lineage that
knows the character. A step of a skipped character splits the sequence; a switch between two
kept characters (Lazarus rising) does not.

The summary command prints the kept steps per character (`characters`), every recorded
character (`recorded_characters`) and `dropped_steps`; `--characters all` or `--characters 0,7`
changes the list for the summary only.

Recordings of another player can go in a separate folder (for example `runs/demos-friend`)
listed next to `runs/demos` in `demo.recordings`, so each set can be compared or removed.

## How much

Training refuses fewer than `demo.min_steps` (30000) decision steps, about 100 minutes of active
play at 5 decisions per second. 2-5 hours is the target; more hours on more varied floors help.
Recordings can be added later: the next session uses all files in `runs/demos` for the BC
regulariser without a new lineage (only pretraining needs them before `--initialize`).

## Start the new lineage

1. Rename the current run, for example `runs\pure-v4` to `runs\pure-v4-demo-bc-v1` (done for the
   first demo lineage on 2026-11-04).
2. `Train-Start.cmd --initialize`. Pretraining runs first (minutes on the GPU) and writes
   `runs\pure-v4\seed-1\pretraining.json`: holdout accuracy per head before and after, against
   the majority-class baseline. Then RL starts from the checkpoint at step 0.

## Privacy

Recordings hold game state and button presses only: no screen, audio or other input.
