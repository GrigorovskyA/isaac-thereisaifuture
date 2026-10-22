# Live reward diagnosis after the t8960 experiment

## Outcome

Read-only diagnosis found two reward-accounting defects that must be addressed
before the next learning experiment. No production fix or new game/training run
was performed. The t8960 checkpoint remains intact as development history; its
successful updates establish learning execution, not valid reward labels or policy
quality. Do not discard it or silently overwrite its lineage.

## Evidence and limits

Source session: runs/live/sessions/20261020-110829-df9a80. Source hashes and full
audit output are in ignored reports/local/five-death-20261020-105504/reward-audit.json.
The files contain derived oracle events and episode summaries, not raw oracle
snapshots or individual actions. They cannot establish enemy species, healing or
revival mechanics, a geometric obstruction, or why the policy failed to finish.

The surviving epoch3/visit1 continued through six approximately1800-update
segments and an unfinished final segment. The game frame continued advancing;
the sixty-second software boundaries did not restart the native run. An unknown
outcome is the existing conservative terminal-coverage result, not a new death.
No frozen-game diagnosis follows from remaining in the same room.

### Disappearance is being treated as a kill

Within session d4590ba74cfb41f5b6b7cd4ecb12c73d,epoch3,visit1,entity45,generation0:
derived enemy_killed at frame7223 is followed by enemy_spawned at7225,only two
frames later. This is the same full identity, not a different game restart.
The trace has31 spawn labels,29 damage labels and6 kill labels; these are derived
labels, not31 unique actual enemies or6 independently verified kills.

EventDeriver.update in live.py emits remaining-HP damage and a kill whenever a
previous identity disappears from a complete list. Lua's oracle list requires
Exists(),not IsDead(),and IsActiveEnemy(false); an entity can remain in the room's
identity map while being excluded from that active-enemy list. Exact cause in this
fight is unknown. Removing the visible-only condition alone cannot fix this:
oracle capture already includes invisible active enemies.

A synthetic witness through the actual EventDeriver and RewardLedger starts an
enemy at10HP,observes6.5HP,then no membership,then the same6.5HP identity. The
measured loss pays0.7; absence alone pays an additional1.8 (1.3 inferred remaining
HP plus0.5 inferred kill). Reappearance does not retract that reward. This
reproduces unsafe inference; it does not establish a real native death.

### Software truncation renews the HP reward allowance

IsaacCombatEnv.reset unconditionally calls accountant.reset(episode_id).
LiveBackend.start_episode calls EventDeriver.begin,which clears enemy history.
LIVE_SCENARIO truncates after1800 game updates even when the native room/run
continues. Thus both the reward allowance and HP comparison baseline restart at
software segment boundaries. The existing healed-HP cap only protects one segment.

Synthetic witness: eight software resets in the same native room,each observing
10->6.5HP on the same identity,earn5.6 damage reward against the intended total2.0
per-enemy HP allowance. Native repeated3.5 damage labels alone do not prove that
healing occurred in this fight; the reproducible accounting defect is separate.

## Checks and delegation verification

User-authorized gpt-6-luna/high executed only the supplied offline commands:

- `.venv/Scripts/python.exe reports/local/audit-last-combat.py`: exit0. Assertions
  confirm the current defects; this is not a passing regression for a fix.
- `.venv/Scripts/python.exe -m pytest tests/test_live.py tests/test_rewards.py tests/test_env.py -q`:
  exit0,38 passed,0 failed,0 skipped,in2.41s. Existing tests do not catch the
  cross-segment issue and currently expect disappearance-based kills.

Primary read the logs and compared before/after/current SHA256 for the diagnostic,
live.py,rewards.py,env.py,and all three test files: unchanged. Logs:
reports/local/reward-diagnosis-audit.txt and reward-diagnosis-tests.txt; manifests
reward-diagnosis-hashes-before.json and reward-diagnosis-hashes-after.json.
The current t8960 manifest/model/normalizer hashes and latest pointer still match
the prior full checkpoint verification. Full Windows suite not rerun: no production
or test source changed. No synthetic RL smoke or native acceptance claimed.

## Next implementation boundary

Prioritize a small OpenSpec reward-provenance/continuity change before resuming
training. The current live-training-loop specification explicitly requires
disappearance-derived kills,so change that requirement deliberately rather than
silently contradicting it or merely changing test expectations.

Required acceptance:

1. Absence/inactive membership alone cannot pay remaining HP or a kill; distinguish
   confirmed native death from unknown disappearance. Audit installed lifecycle
   APIs before depending on new callback evidence. Missing evidence must fail
   conservatively,including overflow and disconnects.
2. Damage allowances survive software truncation in the same actual encounter;
   healing/reappearance and repeated segment resets cannot renew them. Scope
   identities explicitly and bound retained state. Do not carry allowances across
   foreign session/epoch identities or silently equate a new visit with a new enemy.
3. Rebaseline observation gaps without awarding fabricated damage. Preserve health,
   death,terminal-coverage and infrastructure-fault distinctions. Keep all oracle
   information outside policy observations,normalization and recurrent inputs.
4. Record the changed reward contract/version and checkpoint lineage explicitly.
   Preserve t8960; determine explicit development warm-start versus a separate clean
   baseline without silently resuming incompatible training or resetting the model.
5. Add behavioral regressions for absence/reappearance,confirmed death,healed HP
   across multiple truncations,overflow,context changes and bounded cleanup. Run
   targeted/full Windows checks via the bounded test worker,then primary review.
6. Native reward acceptance remains separate: obtain structured evidence for one
   genuine kill and one continuing encounter across a software boundary before
   claiming the correction works in Isaac.

The navigation change remains17/18 with its post-clear/checkpointed sequence
pending; this finding does not satisfy that condition. Shapes2/3/5 remain deferred.
