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
