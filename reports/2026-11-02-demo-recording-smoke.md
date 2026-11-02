# Demo recording: five-minute native smoke

2026-11-02, Europe/Amsterdam. User played and stopped the recorder with Ctrl+C. Source `92d378d`; updated observer deployed while Isaac was closed, source and deployed `main.lua` SHA-256 `ea4303ae80b4d86c87aee81dbf54386b9adf31556e69e89b340f45a242cfcbf5`. Windows `Check.ps1`: 1774 passed, no skips, two warnings; strict OpenSpec 37/37. Training remained stopped.

`python -m isaac_threrisaifuture.demo_dataset runs/demos` read two recordings: 1,566 decision steps in 321.733 seconds of active game updates, about 4.87 steps per active second (target approximately five). Both manifests advertised `demo_record_v1`; gzip files were readable and reported zero dropped input masks. This demonstrates non-empty keyboard-derived move and shoot labels in this sample, not universal accuracy for all keys, controllers, game states, or later recordings.

| Head | Recorded labels |
|---|---|
| Move | none 313; left 402; right 439; up 209; down 203 |
| Shoot | none 660; left 251; right 345; up 148; down 162 |
| Use | none 1561; bomb 2; pill/card 3 |

The recordings contain 3,335 and 3,367 snapshots, respectively, with 3,157 and 3,083 active snapshots and 4,822 and 4,831 input updates. No claim is made that the use labels match every physical press without an independent record of what the user pressed. Two mod sessions were recorded; the reason for the session boundary was not independently established.

Current dataset: 1,566 / 20,000 decision steps; 18,434 remain. Further human-play sessions are required before the requested new-lineage initialization. This smoke does not validate behaviour cloning quality or gameplay improvement. Raw recordings stay under `runs/demos` and are not committed.

## Follow-up: bomb press discrepancy

The user recalled using more bombs than the two dataset labels. Readback of the two raw streams found five observed starts of the bomb-held bit (with a previous frame present), but only two bomb-triggered masks, which yielded the two dataset bomb labels. The other three held starts had no trigger in the following five recorded updates. The active-mask overflow counter was zero. A held input start does not independently prove that the game successfully placed a bomb; game trigger semantics, availability/cooldowns, polling and action-window behavior remain unverified. Treat bomb-label completeness as a blocker to claiming the recording is fully qualified; conduct a controlled count of deliberate presses and actual placements before relying on bomb labels. Existing recordings remain intact.

## Second human approach: three reported bombs

The user reported placing three bombs. The second approach produced two completed files (`20261102-140605-fcc35597.jsonl.gz` and `20261102-140916-223b16d7.jsonl.gz`): 1,480 decision steps, 303.433 seconds of active updates, 3 bomb labels, all four move and shoot directions, and zero reported dropped masks within the files. Raw masks contain three bomb-held starts and three bomb-triggered events, matching the user's reported count in this approach. This supports correct bomb labeling in this sample but does not resolve the earlier approach's five observed held starts versus two triggers or establish input completeness generally.

The user supplied the recorder output: the first session ended with `Message deadline expired`, then a second session connected and was stopped by Ctrl+C. The reader's configured message deadline is three seconds; the immediate cause and any actions missing during the disconnection are unknown. Zero dropped-mask counts do not measure the disconnected interval. The combined dataset has 3,046 steps (625.167 active seconds); 16,954 steps remain to the requested 20,000 minimum. No pretraining or RL was started.
