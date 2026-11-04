## 1. Implementation

- [x] 1.1 `main.lua`: capability `demo_record_v1` (with `entity_observation_v1` only), oracle block
  and live sample rate in demo mode, per-update human input masks in snapshots.
- [x] 1.2 `live_wire.py`: `HumanInput`, `DemoSnapshot`, `HUMAN_INPUT_BITS`;
  `observer_client.py`: `ObserverConfig.demo_record`.
- [x] 1.3 `demo_recorder.py`, `Record-Demo.cmd`: gzip JSON lines per session in `runs/demos`.
- [x] 1.4 `demo_dataset.py`: decision points, labels, live-identical observations, cache, summary.
- [x] 1.5 `demo_learning.py`: `DemoLearner` (normalizer fit, pretraining, regulariser, holdout
  accuracy); `learner.py`: demo phase after each update.
- [x] 1.6 `training.py`: contract `pretraining`, `demo` section, pretraining of a fresh lineage with
  `pretraining.json` and a step-0 checkpoint; shipped config `pretraining: demo_bc_v1`.
- [x] 1.7 Tests: Lua demo mode, recorder, dataset fidelity against the live env, BC learner,
  training integration; hash pins.
- [x] 1.8 Docs: STATUS, TRAINING_SESSION, RUNTIME_AUTHORITY, README, RL_DESIGN.

## 2. Verification

- [x] 2.1 Offline gate and strict OpenSpec validation; `scripts/smoke_rl.py`.
- [ ] 2.2 Windows `scripts/Check.ps1`; mod redeploy; a 5-minute native recording smoke test
  (masks follow the keys, oracle present, dataset summary sane).
- [ ] 2.3 2-5 hours of recordings; `--initialize` of the new lineage; pretraining report (holdout
  accuracy per head against the majority class); 20-minute audit; 75k-step comparison with the
  E3B and reward v13 lineages at equal steps.

## 3. Recording gaps and continuation

- [x] 3.1 Preserve the demo peer and buffer across short timeouts; close at a bounded idle limit.
- [x] 3.2 Record run-seed metadata and stitch continuation groups under the agreed boundary rule;
  invalidate caches.
- [x] 3.3 Test silent gaps, split/unsplit fidelity and different run identities and boundaries.
- [x] 3.4 Pass the Windows quality gate and strict validation; document the native floor-change
  and two-minute alt-tab recording check, without changing existing recordings.

## 4. Character filter

- [x] 4.1 Record `character_type` per decision point in sequences and caches (labeler version 5).
- [x] 4.2 `demo.characters` (default: characters that play like Isaac) filters after the cache;
  a dropped character splits a sequence, a switch between kept ones does not.
- [x] 4.3 Dataset CLI prints kept steps per character, recorded characters and dropped steps;
  `--characters` option.
- [x] 4.4 Tests: per-step characters, split and keep rules, cache round trip, CLI, config default.
- [ ] 4.5 Windows `scripts/Check.ps1`; the current recordings keep 36154 steps in 19 sequences.
