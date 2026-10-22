## 1. Implementation (offline)

- [x] 1.1 Add `checkpoints.py` (manifest, save/load, compatibility rejection, RNG capture).
- [x] 1.2 Add `training.py` (config, bounded train, CLI, selection rule, multi-seed driver).
- [x] 1.3 Write tests/test_training_manifest.py (config, incompatibility, resume-missing, selection math).
- [x] 1.4 Wrap training envs in SB3 `Monitor`: the env's `info["episode"]` summary crashed rollout
      logging (`KeyError: 'r'`) after a finished episode; regression test added (fixed under
      `frozen-policy-evaluation-v1`).

## 2. Checks (run on Windows)

- [ ] 2.1 Run the new tests.
- [ ] 2.2 `./scripts/OpenSpec.ps1 validate combat-ppo-training --strict`.
- [ ] 2.3 `./scripts/Check.ps1` passes.
- [ ] 2.4 Short synthetic train/resume run via `./scripts/Smoke-RL.ps1`-style check.

## 3. Real-game evidence (blocked)

- [ ] 3.1 Wire the scenario environment factory and evaluation callbacks (needs items 06/07 on real data).
- [ ] 3.2 Several seeds trained on an agreed budget; model beats random on validation; evidence report; archive.
