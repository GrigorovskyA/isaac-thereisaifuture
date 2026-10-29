# Schema 8: authorized New Run and repeated qualification

Date: 2026-10-29, Europe/Amsterdam. State: running, qualification pending.

The user explicitly approved starting New Run on file 2 and repeating the hour
after the [missing-Continue startup blocker](2026-10-29-schema8-startup-blocked.md).
The two failed startup sessions are preserved, with stop.forever, in
`runs/pure-v4-schema8-startup-failed-20261029`. They had no model checkpoint.
The schema 7 archive at `runs/pure-v4-reward-v9-schema7` remains unchanged.

## Preparation and launch

- All frozen runtime inputs and source/deployed observer hashes were rechecked.
  Software revision remains `384b1cc`; documentation revision before launch was `2cf33d7`.
  The already-passed Windows gate (1422 tests, Lua, no skips), strict OpenSpec 24/24
  and synthetic CPU smoke were not rerun on unchanged software.
- Existing guarded `new_run_file2` verified fresh selected-slot metadata for file 2
  and native `New` run evidence. Normal owned-game close created Continue. No save
  or Steam Cloud files were edited. This preparation is excluded from training metrics.
- The repeated owner launched once with `Start-Pure.cmd --initialize` into a fresh
  `runs/pure-v4`. The training launcher then verified `Continue` on file 2.
- Contract `b26db425729a40fa632b66a3967cf403f708bc10f89edb13500e09cd4e47b4de`;
  observation 8 / 9762 inputs, action 2, reward pure-v9, projection 512, n_steps 1024,
  ent_coef 0.005, gamma 0.998, stall 40 s. Source, configuration and mod remain frozen.
- Hour owner start: 10:39:41.881 UTC (11:39:41.881 CET), October 29.
  Stop deadline: 11:39:41.881 UTC (12:39:41.881 CET). A local timer writes stop.forever.
  Disk cap 20,480,000,000 bytes; normal supervisor fault cap 5. No further manual
  retry or initialization is authorized by this receipt.
- The owned game window is maintained in foreground by the local owner. Its guard
  stops the run if the first two completed pause_ok measurements are both zero.
- Initial live evidence: state training, 272 successful steps, 1200 snapshots,
  maximum 5960 bytes, zero decode errors, 273 acknowledgements and zero rejections.
  No optimizer update had completed at that sample; pause remains unverified.

## Qualification and conditional continuation

At the hour stop, verify learner exit 0, no fault, empty cleanup errors and actual
stopped game/worker/owner/listener/owned approval, with stop.forever retained.
Review snapshot size/validation, rejected-command share and steps/hour against
schema 7; require update_seconds median <12 s, pause_ok >=90%, populated pause_seconds
and no mass pause/resume failures. Verify actual door/minimap/enemy identity values,
enemy_kinds >1, and report each kind's maximum and overflow share. Disclose unencountered
trapdoors/interactables. The prepared assessor is an aggregator, not acceptance.

Only a genuinely passed evidence review permits continuation without initialization
until 2026-10-31 08:00 UTC (09:00 CET). If pause does not work or qualification fails,
stop and report without fixes or another attempt. Native task 2.2 remains unchecked
while evidence is pending; no task 2.3 or frozen-evaluation acceptance is claimed.

The final committed report must include approximately 30k-step windows and compare
schema 7 on equal steps, without extrapolation beyond its final t204800. Local
evidence and prepared finite owners are in
`reports/local/pure-v9-schema8-retry-20261029/`; raw logs/models are excluded from Git.
The finite follow-up monitors this qualification and conditional continuation and
is removed when the authorized work ends. Healthy pending states remain silent.
