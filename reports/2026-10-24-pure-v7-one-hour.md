# Evidence: pure-v7 one-hour native qualification

- Date/time: 2026-10-24, 15:13:48.975-16:13:34.684 Europe/Amsterdam (13:13:48.975-14:13:34.684 UTC).
- Revision: `ede6f2dc0ec2d3f2f70321e5fd5ba25b275afe31`; only unrelated `tools/` untracked.
- Scope: stagnation-cost-reward-v7 task 2.2, fresh reward-v7 lineage; no claim of improved play.
- Runtime: native Windows, Steam Repentance+, save file 2, structured observer bridge.
- Python: project Python 3.12 virtual environment; RecurrentPPO, seed 1, observation 5 (3499 inputs), action 2, reward contract `pure-v7`.
- Configuration hash: `d62dc21baf19941b0484e857f2124e8fbffb3d564ab9763a2e13619230c63bc4`.
- Hyperparameters unchanged: gamma 0.998, gae_lambda 0.98, ent_coef 0.005.
- Budget: one 3600-second session, five consecutive infrastructure faults maximum, 20,480,000,000-byte disk cap, unlimited death/stall restarts under pure-profile authority.

## Results

| Check/requirement | Command/scenario | Exit code | Status | Evidence |
|---|---|---|---|---|
| Windows gate including Lua | `scripts/Check.ps1` on final source | 0 | passed | 1233 tests, no skips, mypy 31 files, lint/format/pip clean, strict OpenSpec 18/18; local `check-final.log` |
| Preserve reward v6 | Rename old root to `runs/pure-v4-reward-v6` | 0 | passed | All 77 archived file hashes match preflight |
| Fresh native reward v7 | `Run-OneHour.py --initialize` | 0 | passed | Session `session-20261024-151348-v7-one-hour`, state completed, learner_exit 0 |
| Idle grace | Compare native per-step audit with episode CSV | 0 | passed | All 29 episodes with negative stagnation have idle beyond 20 seconds; no charged step inside grace or on a clock reset |
| Episode-wide cap | Sum audit cost per completed episode | 0 | passed | Minimum -7.0; 25 episodes reached the cap; all 36 row totals match audit |
| Stall penalty | All rows with truncation_reason=stall | 0 | passed | 25/25 have col_stall=-5 |
| Frozen inputs and cleanup | Hash readback, result and process/listener checks | 0 | passed | 832 tracked files unchanged; cleanup_errors empty, fault null; game/training processes and bridge listener absent |
| Eight-hour policy acceptance | Later frozen evaluation, task 2.3 | N/A | not_run | Remains open |

Local evidence is under `reports/local/pure-v7-one-hour-20261024/`: `preflight.json`, `check-final.log`, `launch-result.json`, `verification.json`, and the prepared launcher/passive audit. Native artifacts are under `runs/pure-v4/supervisor/session-20261024-151348-v7-one-hour/` and `runs/pure-v4/native-audit/`. These raw artifacts are not committed.

## Real game

The launcher used the existing `SessionPlan` and `supervise` API once, with `forever=True` for pure-profile unlimited New Runs, `resume=False`, empty parent, and a 3600-second deadline. It deliberately omitted the outer forever loop, so completion could not launch another session. This was the bounded initialization equivalent, rather than invoking the unbounded `Start-Pure.cmd --initialize` wrapper. Guarded Steam/menu entry confirmed file 2 and Isaac; gameplay used only the bridge.

Elapsed time was 3585.704 seconds: the worker cooperatively stopped within the 15-second deadline margin. The final partial rollout was not published; result reason was `Live wall-time budget exhausted; unfinished rollout has no new checkpoint`. The last valid checkpoint is `d62dc21b-s1-t14848`, parent `d62dc21b-s1-t14336`, with model SHA256 `2de0ec818b22b1e49e672781be7a2683f2b94085a37345e8088acb6ae91cf5c4` and normalizer SHA256 `4e6f386008036a8d01d354b391a525d808274bfca48854dc69741d85c5c8626d`. There were 29 completed rollout/update publications (116 PPO epochs reported in n_updates).

The passive step audit returned the original step result unchanged and observed idle clocks and reward columns only. It recorded 15,094 steps across 37 episode IDs, including the final unfinished episode; the 36 completed CSV rows are the metric denominator. It recorded 126 clock decreases after progress. All completed-episode stagnation sums match CSV and remain within [-7, 0]. Negative costs occur only when idle increases past 20 seconds. This validates the reward accounting, not a visible gameplay skill.

Before initialization, the supplied implementation exposed an overshoot/repeated-idle cap defect. The user explicitly selected a hard -7 limit for the entire episode. Four regression tests cover overshoot, repeated idle intervals, same-run/new-epoch reset behavior and alternate watchdog limits. The final gate includes this fix. Initial pytest cleanup hit Windows access denial with the default temporary directory; a process-local fresh TEMP/TMP resolved it. An intermediate strict-spec length failure was fixed before the successful final gate.

No Lua deployment was needed. Source/deployed main.lua SHA256 remains `5e9352154a38ea4ad6b6d219d463993493cb676ba432f04fd2f3372853470315`; metadata.xml remains `00f46cc452c2a4e7809c14501d94de2db1ac94b1dde12b3c25d163922f34b997`. Final cleanup succeeded; stop.forever was retained after this session. The read-only dashboard was left running.

## RL evaluation

| Metric | Completed native episodes |
|---|---:|
| Episodes | 36 |
| Stall restarts | 25/36 (69.44%) |
| Deaths | 11/36 (30.56%) |
| Exited start room | 22/36 (61.11%), nonempty steps_to_first_exit |
| Mean enemy damage fraction | 1.2421 |
| Rooms cleared | 2 total, 0.0556 per episode |
| Enemies killed | 34 total |
| Highest stage | 1 |
| Negative stagnation episodes | 29/36 |
| Episodes at -7 cap | 25/36 |

The unfinished final episode is excluded. This is training, not a frozen evaluation: the policy changes during the sample. These one-hour results do not establish improvement against random or satisfy the eight-hour acceptance criterion.

## Verification and continuation

Self-review: task 2.2 passed. Reward implementation and regression coverage match all three added requirements (stagnation cost, run-wide bound, v7 coefficients); native accounting agrees with recorded rows. Task tracking is 6/7 after marking 2.2. Task 2.3 remains incomplete: do not archive or claim whole-change acceptance.

After this report, the user authorized a separate four-hour continuation from exactly `d62dc21b-s1-t14848`, without initialization or configuration changes. Use the pure forever supervisor with one absolute deadline, retain its result and cleanup evidence, and stop without starting any further session or making post-run commits. The report above covers only the completed one-hour qualification.
