# Schema 8 qualification: startup blocked

Date: 2026-10-29 (Europe/Amsterdam). Outcome: **blocked before training**.
This is a bounded startup report and self-review, not native acceptance.

## Verified preparation

- Source revision `384b1cc` was committed and pushed to existing `origin/main`.
  It contains rich-room-observation-v8 and paused-updates-and-input-projection.
- Windows Check passed: 1422 tests including Lua, no skips; lint, format, mypy and
  dependency checks passed; strict OpenSpec 24/24. Synthetic CPU smoke passed with
  9762 inputs, 16 steps and [5,5,4] actions. Synthetic results do not prove native play.
- Contract: `b26db425729a40fa632b66a3967cf403f708bc10f89edb13500e09cd4e47b4de`;
  observation 8, action 2, reward pure-v9, features_dim 512, n_steps 1024,
  ent_coef 0.005, gamma 0.998, stall 40 seconds.
- With the game closed, the observer was deployed and source/deployed hashes matched:
  main.lua `41b78262d4e8a80634a6d9ce0a04e343195601b2dbcf061fdeca46aac4e58985`;
  metadata.xml `00f46cc452c2a4e7809c14501d94de2db1ac94b1dde12b3c25d163922f34b997`.
- Schema 7 was renamed to `runs/pure-v4-reward-v9-schema7`, retaining stop.forever.
  Final checkpoint `3cb9d928-s1-t204800` was preserved with verified hashes:
  manifest `ef36741f147997527ab5af81ce08cac96b08bd1f008b752a3d0846c1af809be5`,
  model `a475b42159e877c7bd12ddee89d409e90b718908f0da0fe49d1f5b184d574dd4`,
  normalizer `b553631169209374ce8887dae8709e72cd19459a916fcdbcbbdf1000f0378675`.

## Native result and cleanup

The one-hour owner was launched once at 10:25:04 UTC (11:25:04 CET), with
`--initialize` and an intended deadline of 11:25:04 UTC. The normal forever
supervisor automatically attempted two startup sessions before the stop marker
was set. Neither entered training:

| Session | Startup seconds | Learner exit | Checkpoint | Fault |
| --- | ---: | ---: | --- | --- |
| session-20261029-112504-0001 | 36.750 | 1 | none | Existing file2 game state not confirmed; no New Run fallback |
| session-20261029-112541-0002 | 35.922 | 1 | none | Existing file2 game state not confirmed; no New Run fallback |

The game log reports that Steam Cloud could not find or open `rep+gamestate2.dat`
and that no game state was detected. It also reports that the rerun state cannot
be continued with the current modding state. These are observed log messages;
the underlying save/Cloud condition was not changed or repaired.

Both sessions recorded `worker: RuntimeError: Owned worker required termination;
cooperative release unverified` in cleanup_errors. This is not a clean native exit.
The outer owner exited 0 at 10:26:18 UTC because its supervisor had stopped on the
stop file; that wrapper exit does not make qualification successful.

Subsequent live inspection confirmed no Isaac, training worker, session runner or
hour-owner process, no port 9528 listener and no active owned control approval.
The retained approval-identity receipts are historical session records.
`runs/pure-v4/supervisor/stop.forever` remains present. No continuation or recurring
monitor was started. The failed schema 8 startup root is preserved.

## Requested measurements

All native qualification measurements are **not_run**, with no usable training
sample: snapshot validation/maximum bytes, rejected-command share, steps/hour,
update_seconds median, pause_ok share, pause_seconds, pause/resume event rates,
door/minimap/enemy API values, trapdoors/interactables and per-kind maximum and
overflow shares. Missing measurements are not zero values or absent encounters.
No model checkpoint, optimizer update or completed training episode was produced.
There are no 30k-step windows or equal-step schema 7 comparisons to report.

Neither pause success nor pause failure was observed. Both changes' native task
2.2 remains unchecked; richer-observation task 2.3 also remains open. No frozen
evaluation or gameplay-improvement claim is made.

## Evidence and next prerequisite

Local evidence is retained under `reports/local/pure-v9-schema8-20261029/`:
`check.log`, `smoke.log`, `preflight.json`, `launch.json`, `result.json`,
`initialization.log` and `isaac-first-hour.log`. Native session results remain
under the two session paths in `runs/pure-v4/supervisor/` above. These raw artifacts
are deliberately excluded from Git.

The guarded entry path requires an existing file-2 Continue. `--initialize`
initializes the model; it does not select New Run. An explicit agreement on
starting a new file-2 game is required before another bounded qualification.
No source/configuration/save/Cloud repair or further initialization was attempted.
The October 31 continuation remains conditional and has not been launched.
