# Evidence: reward v3 / pure-v2 Windows startup

- Date: 2026-10-22, Europe/Amsterdam. User requested launch of the updated pure v3.
  Code names: reward contract `pure-v3`, model lineage `pure-v2`, seed 1,
  `configs/training-pure-v2.yaml`, run root `runs/pure-v2`.
- Base Git revision `d728ab4`, with the user's uncommitted reward/metrics/dashboard
  implementation preserved. No pure-v1 resume or checkpoint migration.
- OpenSpec: `reward-v3-and-training-metrics` and pending native acceptance 4.3 of
  `pure-self-learning-v1`. Primary verification is self-review, not independent review.

## Offline verification

`scripts/Check.ps1` passed, exit 0: 1061 tests without skips, lint/format/mypy,
pip check and strict OpenSpec 12/12. Test process used a dedicated TEMP/TMP,
the previously isolated optional Lua 5.3 runtime, and the installed game's
`resources/scripts/json.lua`. Full log: `reports/local/pure-v3-20261022/check.log`.

`scripts/Smoke-RL.ps1` passed, exit 0: 16 CPU steps, 1837 observations,
action space `[5,5,4]`. This is synthetic plumbing evidence only.
Tasks 2.1 and 2.2 are complete; hours-of-native-evidence task 2.3 remains open.

The reward-v3, pure-training, training-metrics and dashboard tests cover the declared
offline scenarios. The active paths use RewardLedgerV3 and contract pure-v3, refuse
the reward-v2 contract, record optimizer statistics/action shares and retain the
bounded supervisor. No Lua/observation/action protocol change in this update.
Deployed observer preflight passed; source and deployed Lua hashes match.

## Native plan

First launch: `Start-Pure.cmd <installed game> <native log> --initialize`, only when
no pure-v2 checkpoint exists. First 15 minutes are bounded qualification; stop file
requests cooperative stop, normal owned-game close and exact owned-approval removal.
All retries share one 30-minute qualification deadline. No bypass of focus, file2,
identity, frozen-source, lineage or resource guards. Disk cap 20,480 MB, consecutive
infrastructure-fault cap 5; death/stall New Run unlimited within the session lease.

Verify fresh file2/Isaac evidence, pure-v3 checkpoints, negative stall term, new
episode fields and train.csv rows, death/watchdog transitions, checkpoint reload,
unchanged frozen source and complete cleanup. Prior native schema3/use effects are
scoped evidence for the unchanged deployed Lua, not proof of learning improvement.
Only after qualification passes, run the same command without --initialize for
continuous training. Hours and policy comparison remain separate future evidence.

## Startup precondition

A previous pure-v2 attempt at 16:52 left an approval but no running game/learner or
listener. Its worker timed out before connecting. The deployed approval's SHA256
matches that attempt's approval-identity receipt:
`7edc5f166c05e159fb22d81e75d375539f268e696f66ebaa55cb0d84b1e24686`.
The user explicitly authorized removing this exact unchanged approval. It was
rehashed, backed up locally and removed while no game/runner was active. A new
session then launched through Start-Pure/Steam; no save, Cloud, options or other
mod settings were changed.

## Native qualification

- Session: `runs/pure-v2/supervisor/session-20261022-165844-0001`, started
  16:58:44 CEST, learner active at 16:59:05. Seven guarded menu keys; fresh
  `[Continue, 2]`, active character type 0, schema3/actions2 and pure-v3.
- Config contract hash:
  `d9b939847544687899d97490a6deff29f60ee0392d275d12cd96e4e3637a4c76`.
- A finite timer will request stop after 900 seconds from the session clock;
  it also checks all frozen source/config/mod hashes every two seconds and
  requests stop if any change. No continuous-run acceptance before cleanup.
- First real checkpoint `d9b93984-s1-t512` loaded through CheckpointPolicy with
  its real weights and VecNormalize, expected config hash/seed, reward pure-v3.
  Model SHA256 `56970da2786abb6e9355b27c1cffd7012d1d1a6dcaf85f78f7a4a04090799eaa`;
  normalizer SHA256 `ebef19160dcba529696288eaabdd20ff8516d313cd9e8489977412829fe3fc69`.
- Native death and command/watchdog restarts confirmed increasing epochs. First
  stall return -4.5985, novelty 0.88, stall -5 once; next stall return -6.7093,
  novelty 0.76, stall -5 once. Death rows carry stall 0. First death episode
  visited two rooms, damaged enemies and returned +2.6882. These are descriptive
  observations, not a controlled comparison or evidence of learning improvement.
- New episode fields include use counts, health lost and first exit/damage steps;
  absent first exits/damage stay blank. Optimizer rows carry losses, entropy, KL,
  learning rate and action shares. The first three native rows passed sum-to-one
  checks for each action head and had nonempty loss/entropy/KL values.
- Prior 40-frame schema3 acquisition and user-confirmed use effect in
  `2026-10-22-pure-windows-acceptance.md` concern the identical deployed Lua
  (`edf4eff22eb785c6b9a24cc511f65b075af23da67c3b5aa7df19d1340ee7c1c8`).
  They do not establish every use variant, nonzero inventory diversity or worst-case
  snapshot/collectible load. Current Python validation and training use schema3.
- In this reward-v3 qualification session the user separately confirmed seeing an
  actual bomb/item/card effect. This is operator evidence of at least one use
  effect, not a claim that all variants were exercised.

Full logs/readbacks: `reports/local/pure-v3-20261022/` and `runs/pure-v2/` (ignored).
Qualification passed after 901.922 seconds: learner exit 0, state user_cancelled
(the deliberate timer stop), no fault and no cleanup errors. Frozen source/config/
mod hashes matched; owned game closed, port 9528 had no listener and approval was
absent. Readback: `qualification-readback.json` in the local evidence folder.

Saved checkpoint `d9b93984-s1-t7168`, 14 optimizer rows, 10 completed episodes:
3 deaths, 7 stalls, 5 start-room exits, 0 clears. Mean return by recorded outcome:
deaths -2.7947, stalls -5.6002. All stall rows have -5 once, death rows have 0;
all action-share sums passed. Last partial rollout was not saved. Old pure-v1's
latest remains `c5532096-s1-t7168`.

The pending native bridge acceptance task 4.3 is complete at its declared scope:
current schema3 validation, current operator-confirmed use effect, native death/
watchdog transitions, real checkpoint load and clean frozen-source shutdown.
Retained full-frame plausibility evidence is from the identical unchanged Lua.
This does not establish all item variants, worst-case capture cost, improved play
or the new change's hours-of-training task 2.3. No OpenSpec change is archived.

Continuous resume started at 17:14:57 CEST through Start-Pure without
--initialize, hidden console PID 44652. Session
`runs/pure-v2/supervisor/session-20261022-171457-0001` records resume=True,
parent `d9b93984-s1-t7168`, fresh `[Continue, 2]`, active Isaac and pure-v3.
The structured bridge connected at 17:15:18. No initialization or new lineage.
First resumed checkpoint `d9b93984-s1-t7680` verified at 17:16:20: parent is
`d9b93984-s1-t7168`, same seed/config/reward contract; all frozen input hashes
still match. The optimizer reports n_updates 60 after the previous 56, and the
new metrics row uses rollout_index 14. Training remains running under the native
forever supervisor; no agent heartbeat or scheduled agent supervisor was created.

## Verification limitation

Self-review found that episode `use_*` counters increment the policy-selected use
in `env._note_facts`; they do not inspect the command acknowledgement. Treat these
as requested-use counts, not proof of an accepted command or physical item effect.
This does not alter actions or rewards; it is a metrics interpretation warning
against the design's wording "accepted actions". No source was edited during the
native session to change it. Training improvement and hours acceptance remain open.
