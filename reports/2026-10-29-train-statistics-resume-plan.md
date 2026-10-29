# Logger statistics repair: finite native resume

Date: 2026-10-29, Europe/Amsterdam. Native statistics verification pending.

## Verified software

Commit `fc80cd5`, pushed to existing origin/main with the exact requested message:
`Read train statistics before the next learn() resets the logger`.

The two-file fix captures all nine SB3 train statistics in _on_training_end,
before a subsequent learn() replaces the logger. The row keeps those captured
values while waiting for the pause result. The regression test replaces the
logger before each next rollout and verifies retained n_updates/loss and pauses.
Windows Check passed1428 including Lua/no skips, lint/format/mypy/pip clean,
strict OpenSpec25/25. One existing synthetic All-NaN warning remains. No new
synthetic smoke or native gameplay acceptance is inferred from the gate.

Contract remains `b26db425729a40fa632b66a3967cf403f708bc10f89edb13500e09cd4e47b4de`:
observation8/9762, action2, pure-v9, projection512, n_steps1024, ent_coef0.005,
gamma0.998, stall40. Mod unchanged, source/deployed main.lua and metadata hashes
matched before launch. No deployment, dependency, model migration or save/Cloud edit.

## Exact run plan

- Resume exact compatible `b26db425-s1-t31744`, without --initialize or a New Run fallback.
  The parent checkpoint, 138 episode rows, 31 train rows and configuration were copied
  before launch under `reports/local/schema8-train-stats-20261029/`.
- Hidden finite owner started2026-10-29 15:58:40.334 UTC (16:58:40.334 CET).
  Fixed inclusive deadline: **2026-10-30 08:00 UTC (09:00 CET)**. stop.forever timer
  receipt: runs/pure-v4/supervisor/until-20261030-0900-timer.json.
- Session session-20261029-165840-0001 verified file2 Continue and entered training
  without a fault; fresh completed episodes confirm progress. Pause remains enabled.
- No PC console/browser/Codex panel or other window is opened/activated during
  training. Monitoring reads saved files only. Native guarded keyboard handles game focus.
- Runtime inputs remain frozen; disk cap20,480,000,000 bytes, supervisor fault cap5.
  A file-only guard requests stop on new faulted sessions. No extra manual retry,
  initialization or hidden fallback is authorized.

## Checks and first-hour decision

At12min, 16:10:40 UTC (17:10:40 CET), inspect only newly added train rows. Verify
entropy_loss and explained_variance, plus learning_rate, policy_gradient_loss,
value_loss, loss, approx_kl, clip_fraction and n_updates. Empty required fields or
no new rows cause stop/report, without repair/retry. Report pause_ok as measured;
pause failures alone do not stop training. Existing blank historical rows are
retained unchanged, never backfilled or included in repair acceptance.

At60min, 16:58:40 UTC (17:58:40 CET), evaluate all first-hour measured pause rows.
At >=70% continue unchanged. Below70%, make one controlled session boundary,
verify native cleanup, change only live.pause_during_updates:true->false, verify
unchanged contract hash and exact flag-only diff, then resume compatible latest
without initialization under the same absolute deadline. This is a configuration
handoff, not termination of the authorized training. The owner records its decision
and each phase; the flag change is separately reviewable for the final commit.

Human stop uses both local user-stop.request and stop.forever so a simultaneous
configuration handoff cannot restart the run. Training crashes/faults, missing
required statistics, deadline and explicit user stop terminate the run.

## Final report

After verified process/listener/approval shutdown, retain stop.forever and commit
the October30 report. Include approximately30k-step outcome windows versus schema7
(exit start, rooms, kills/clears per1k, stage>=2, stalls/deaths), pause share, new
entropy_loss/explained_variance trends, all col_* means and stall context by clear
flag/type, dead-end proxy, uncleared enemy means and top10 kinds. Use explicit
denominators, exclude missing legacy context and disabled-pause blank rows.

Observed cumulative episode steps include prior unsaved rollout tails and differ
from model/checkpoint steps; label the comparison method honestly. Logger trend
windows use saved model-step anchors separately. No extrapolation beyond schema7
t204800, frozen-evaluation, gameplay-improvement or task2.3 acceptance claim.
Raw logs/models/local helpers/unrelated tools remain outside Git. Finite follow-up
is quiet while healthy/pending and removed when the authorized work ends.
