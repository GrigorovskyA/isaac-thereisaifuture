# Full-batch structured learner: Windows offline verification

October31,2026. Change full-batch-structured-learner. Self-review, not independent
review. User authorized publication, archive and one fresh native launch.

| Dimension | Result / limit |
|---|---|
| Completeness | 10/13 tasks complete; native tasks2.2/2.3/2.4 remain open |
| Correctness | All6 added requirements mapped to implementation and offline scenario tests; native performance/gameplay not verified |
| Coherence | Structured slots/grids/scalars, variance floor, pure contract fields and save/load match design; historical InputProjection retained |

Windows Check.ps1 exit0: ruff lint/format101files,mypy36sourcefiles,1583tests passed,
no skips,pipcheckclean,strictOpenSpec31/31. Includes isolated test-only Lua runtime
from prior local evidence and installed json.lua; process-local TEMP/TMP under
reports/local/full-batch-structured-20261031/check-temp. No dependency/globalPATH
changes. One existing synthetic AllNaN warning in test_compare_eval.
Smoke-RL.ps1 exit0:16syntheticsteps,CPUtorch2.14.1,11691inputs,MultiDiscrete[5,5,4],
structured extractor/continuous-only normalizer save/load passed. Synthetic smoke
uses small dimensions/rollouts; it is not a native full1024step speed benchmark.
Strict validation repeated after report/plan edits:31/31.

Evidence E=reports/local/full-batch-structured-20261031:check.log,smoke.log.
Exact config hash ee4f65999d3a8cf0c85dabd5d887e360fd0823a164814bd20753d6dca91ac703
was loaded independently before launch. Rewardv12/observation9/action2 unchanged.

Implementation/scenario mapping:

- Full batch: training-pure-v4.yaml1024/1024,10epochs,targetKL.03; config validation
  refuses batch>n_steps. test_full_batch_recurrent_ppo_learns_with_structured_features
  counts one minibatch per epoch across a real synthetic RecurrentPPO learn call.
- Feature kinds: encoding.FEATURE_BLOCKS anchors and continuous_mask; coverage/layout
  and encoded binary/one-hot tests cover all indices,rich synthetic entity/item/map frames.
- Normalization: ContinuousVecNormalize preserves binary/one-hot bits,variancefloor.1;
  rare-bit,rare-continuous and save/load/class/mask tests pass.
- Saved contract: check_continuous_only is used by training resume and CheckpointPolicy;
  plain/stale normalizer rejection tests pass; frozen input/normalizer tests remain.
- Structured features: shared per-kind masked mean/max/presentfraction,gridCNNs,
  scalarMLP and512head. Partition,empty finite gradients,slot permutation tests pass;
  use-head prior and fresh/resume tests pass.
- Lineage: required policy_features/observation_normalization fields bind the hash;
  old contract/missing fields refused. Existing older runs are preserved, not resumed.

Installed sb3-contrib train increments n_updates once per entered epoch, including
an early-KL-rejected final attempt. Delta n_updates will report entered epochs;
with fullbatch each attempted epoch has one minibatch. It does not by itself count
successful optimizer.step calls. Native update_seconds/KL/clip/explained_variance,
20minute artifact/menu evidence and75k/150k gameplay comparisons remain not_run.

Three incomplete native tasks are archive blockers; they are expected future scope,
not a reason to substitute synthetic results for native evidence. No archive or
native acceptance. Follow the [finite plan](2026-10-31-full-batch-structured-native-plan.md).
