# Evidence: offline wall-stagnation diagnosis

- Task `wall-stagnation-offline-20261022-01`; OpenSpec change `wall-stagnation-replay`.
- Date: 2026-10-22, Europe/Amsterdam. Host: macOS (Darwin arm64), offline only.
  No game, Steam, approval, save, deployment, training or model write.
- Base revision `ace33ddfb9fd64cf0a884919d76234ede4927fa1` plus uncommitted
  changes listed in [Handoff](#handoff). Captured runtime source:
  `e5264e52fccd308fcf96e874bcb01eb46da816a9`.
- Bundle `wall-stagnation-evidence-20261022.zip`, SHA256
  `e66c0cc9f5482ef27487ef8b70382b24fb47b6a88b98913922a644b801a5390d`; all 12
  `MANIFEST.json` entries matched by size and SHA256. Extracted to the ignored
  `reports/local/wall-stagnation-input/`.
- Traces: `learning-policy.jsonl`
  `62d846283027b239149ffcf4bbdd1c76d92eea83d425c591925fbb2d51e44ad6`,
  `learning-oracle.jsonl`
  `e511db640ebe6eaaaa3a0b279ffbbe567d0b535c944457cba9989d62b82cb195`;
  record IDs 1..1606, frames 79376..84663.
- Config `a0a93c29b588fb2ee4b23e3c19f16c5e4124b97fb312503978a6ada405f13f15`, seed20,
  observation 2/723, reward live-firing-v5, collector live-segment-refresh-v1.
- Checkpoints, read from temporary read-only copies and verified unchanged after load:
  parent `a0a93c29-s20-t26368` (model `6e94cc1f…5d08`, normalizer `2d4e8390…662c`), child
  `a0a93c29-s20-t27904` (model `bb5e3bbd…f089`, normalizer `2ece91f9…c74e`) and the
  five intermediate checkpoints t26624..t27648.

## Reproduction

```sh
PYTHONPATH=src python -m isaac_threrisaifuture.wall_stagnation \
  --bundle reports/local/wall-stagnation-input \
  --output reports/local/wall-stagnation-replay-20261022 \
  --checkpoint <dir>/a0a93c29-s20-t26368 --checkpoint <dir>/a0a93c29-s20-t27904 \
  --config-hash a0a93c29b588fb2ee4b23e3c19f16c5e4124b97fb312503978a6ada405f13f15 --seed 20
```

The run takes about 13 s. Without `--checkpoint`, the frozen audit is recorded as
`not_run`. Two runs produced byte-identical outputs: `rows.jsonl`
`e9156b0c…0d98` (1606 rows) and `summary.json` `a8d08a46…70d0`.

| Baseline item | Published | Replayed |
|---|---|---|
| Paired learning decisions | 1606 | 1606, strict ID pairing, 0 identity errors |
| Refresh segments | 6 refreshes | 7 segments starting at 1, 257, 513, 769, 1025, 1281, 1537 |
| Logged v5 shaping | — | 1606 compared, 0 mismatches, 0 missing |
| Re-encoded 723 inputs | 1606 | 1606 match (atol 1e-6) |
| Target-1 HP | 10→6.5→3 at records 26/30 | same; last listed in record 32's endpoint (record 33's start state) |
| Target switch | — | firing target 1→2 at record 33 |
| Near (70,209.35) within 20 units | 1572/1606 | 1572/1606 |
| Ten-active-second stagnation windows | 7 | 7 |
| Clear-line exposure | 6/1613 | 6/1607 (endpoint sample basis; published adds 6 non-endpoint samples) |
| Enemy HP loss / player loss / clears / deaths | 7 / 2 / 0 / 0 | 7 / 2 / 0 / 0 |

Setup and frozen phases come from `run/phases.json` and are copied unchanged into
`summary.json`. Setup has no learner rows, and the frozen phases have no paired traces
in the bundle.

## Diagnosis

The answer to the stale-state question is no. After record 33 the encoded
observation, target selection, movement execution, shaping and recurrent refresh
all behave as specified. The stagnation is learned behavior that the current feedback
does not correct.

Ranked by evidence:

1. **The left prior is inherited and almost ignores the target.** On the recorded
   inputs, with LSTM state carried from record 1, frozen t26368 (before any pilot
   update) gives the following after the switch (1574 records):
   - P(none, left, right, up, down) = 0.081, 0.651, 0.038, 0.061, 0.170;
   - argmax move left in 1574/1574 records;
   - P(left) = 0.683 before the switch.

   Across t26624, t26880, t27136, t27392 and t27648, post-switch P(left) is
   0.687, 0.689, 0.594, 0.612 and 0.635. It reaches 0.674 at t27904, where
   P(right) = 0.033. Labeled counterfactual probes do not move it toward the target:
   - mirroring every visible enemy x raises P(left) to 0.76/0.74;
   - an all-unknown movement mask lowers it only to 0.48/0.58;
   - P(right) stays ≤0.083 in every probe.
2. **Feedback toward target 2 is nearly flat and zero-sum for short deviations.**
   - At (70,210) the v4 interior potential is unknown (grid row 3, columns 0–5 are rock).
   - v5 links to boundary patch 17 at (120,200) with a clear same-frame support.
   - Target-2 phi_v5 stays between 0.3821 and 0.3965 over all 1574 records, about
     396 path units from a firing cell.
   - Target-2 shaping totals +0.0957 / −0.0962 over 500 nonzero records.
   - The first deviation (records 35–38: right, none, then left back) earns
     +0.00067 and +0.00100, then gives back −0.00022 and −0.00144. Net ≈ −5e-7,
     because novelty is capped and the retreat charge is refunded on return.
   - A right step gains about 7.5e-4 against a time penalty of about 5e-4.
   - Reaching tear range (260) needs roughly 77 consecutive productive steps, with no
     intermediate damage.

   This is the specified anti-farming behavior, not a defect. It still means the
   shaping cannot outweigh a strong prior.
3. **The only reward in the trace reinforced pressing left at the wall.** Both
   target-1 hits (+7.0 enemy HP for 2.0 per HP) happened from the wall at about x=70
   while moving left, and target 1 was 10 units from the wall at (80,200). Player
   damage (−8 per half-heart) occurred at records 13 and 23, before both hits.
4. **No route is observable.**
   - Lua sends the nearest 12 obstacles, including `GRID_WALL` (`entity_caps`,
     `mod/observer/main.lua:546`); 41 overflowed, so 12 of 53 were sent.
   - The opening near x≈280 is not in the policy inputs at the wall.
   - The movement mask is a 40-unit `CheckLine` probe. It reports left/up/down
     blocked at the wall even though short vertical steps succeed. That is its
     defined meaning, so it is not a defect.

Hypotheses rejected by measurement:
- **Stale target or ID:** the switch is exact and target 2 is encoded each record.
- **Encoding drift:** 1606/1606 records re-encode exactly.
- **Blocked execution:** right moved the player in 47/47 records (mean dx +5.24);
  left gives mean dx −0.29.
- **Recurrent or cache carryover at refresh:** refresh starts a shaping segment
  without an env reset by design; segment boundaries replay exactly.
- **Debt binding the cap:**
  - final room debt is 0.0695, of which 0.0668 is stale from vanished target 1;
  - room `_paid` is 0.0023, so the 0.25 cap never bound.

  The stale debt is latent and worth a regression later. It did not cause this run.

Executed movement after the switch:

| Move | Count | Displaced >0.5 | Mean dx |
|---|---:|---:|---:|
| left | 1029 | 236 | −0.29 |
| down | 277 | 111 | −0.03 |
| none | 137 | 31 | +0.21 |
| up | 84 | 75 | +0.31 |
| right | 47 | 47 | +5.24 |

Maximum x after the switch was 85.7.

## Decision and proposal

No source, reward, observation or Lua patch is justified.

- Changing shaping weights would be arbitrary coefficient tuning against an
  inherited prior.
- Removing the zero-sum refund would reopen oscillation farming.
- A scripted escape would be hand-coded gameplay.

The delivered change is reproducible offline audit tooling plus regressions.
The smallest proposal that addresses causes 1 and 4 needs its own OpenSpec change:

1. **Observation 3**: send a policy-visible coarse walkability summary built from
   already visible grid entities, or a larger obstacle cap, so a route away from
   the wall is observable.
   - Version the contract (723 → new size) and keep live-firing-v5 unchanged.
   - Migrate t27904 with zero-initialized new input columns, as in
     `geometry_migration.py` (649→723).
   - Prove output equivalence on these 1606 recorded inputs before any learning.
2. **Offline gate before native time**: rerun this tool's frozen audit on every
   candidate. Require post-switch argmax-left < 0.9 and P(right) above the t26368
   baseline of 0.038 on the recorded inputs. This is a necessary screen only, not
   evidence of better play.
3. **Curriculum**: include post-switch states (remaining distant target and the
   wall start) in the exposed-start pool, so the prior is challenged where it fails.

## Validation

| Check | Command | Exit | Status | Result |
|---|---|---:|---|---|
| Focused tests | `pytest -p no:cacheprovider -q tests/test_wall_stagnation.py` | 0 | passed | 15 passed |
| Lint | `ruff check --no-cache src tests scripts/smoke_rl.py` | 0 | passed | ruff 0.17.1 |
| Format | `ruff format --no-cache --check …` | 0 | passed | 156 files |
| Types | `mypy --platform win32` | 0 | passed | 67 source files, mypy 1.20.2 |
| Offline suite | `pytest -p no:cacheprovider -m "not game"` | 1 | failed (platform) | 1827 passed, 21 skipped, 2 failed |
| Dependencies | `uv pip check` | 0 | passed | 44 packages |
| Specs | `node openspec.js validate --all --strict` (1.14.3) | 0 | passed | 57/57 |
| Windows gate | `.\scripts\Check.ps1` | — | not_run | Windows only |
| Native gameplay | — | — | not_run | not authorized |

The commands ran through `scripts/check.sh` with `PYTHONPATH=src` and `ISAAC_JSON_LUA` unset.

- Python 3.12.13, torch 2.14.1, SB3/sb3-contrib 2.9.0, numpy 2.5.4, Node 26.4.0.
- The Lua observer suites were skipped because no JSON shim was supplied.
- The two failures are Windows-only APIs on macOS: `ctypes.sizeof(_Input)` is
  56 instead of 40 in `test_menu_entry`, and `subprocess.CREATE_NO_WINDOW` is missing
  in `test_session_runner`.
- The two failing tests are unrelated to this change and were not edited.

Tested SHA256:
- `src/isaac_threrisaifuture/wall_stagnation.py`
  `e4c169617bd3801600e95b7c3a1349491322638f5eefbe92e6597e7b26b3a19b`
- `tests/test_wall_stagnation.py`
  `7f71ce8c4acde4fbeb25a5db31050935681a6db196632df067bd6d824a04879a`
- Fixture `policy.jsonl` `317e712b…8573`, `oracle.jsonl` `ca3b5df0…cb9b`.


The tests cover:
- strict pairing, reorder, length and identity rejection;
- invalid action and record-cap rejection;
- manifest tamper detection and output no-overwrite;
- exact replay of logged bonuses through the target 1→2 switch;
- wall-oscillation zero-sum on records 35–38;
- refusal of unclear, unknown or foreign-source boundary support;
- that probes change only the intended inputs;
- on a synthetic project checkpoint, that argmax probabilities equal
  `CheckpointPolicy.act` with carried state, that files stay unchanged, and that
  a wrong config hash is refused.

The fixture is records 30–38, unmodified; see `tests/fixtures/wall_stagnation/README.md`.

## Limits

- The evidence is one room, one seed and one 176-second phase.
- Probabilities are on recorded inputs only, never closed-loop.
- Counterfactual probes are not game states.
- Frozen-phase traces are absent from the bundle.
- Oracle labels are used only for diagnosis and never reach policy inputs.
- No claim of improved or worse native play.

## Handoff

Changed files, uncommitted at the user's request; a separate agent commits:
- `src/isaac_threrisaifuture/wall_stagnation.py`
- `tests/test_wall_stagnation.py`
- `tests/fixtures/wall_stagnation/{README.md,policy.jsonl,oracle.jsonl}`
- `openspec/changes/wall-stagnation-replay/` (proposal, design, delta spec, tasks)
- this report
- `docs/STATUS.md`

Exclude `errors.txt`, `tools/` and `reports/local/`.

Windows verification (step 1 only is requested now; later steps are a proposal,
not execution authority):

1. At the committed revision, from the repo root:
   - run `.\scripts\Check.ps1`, expecting the previous count plus 15 new tests,
     zero failures and 57 strict items;
   - then run the reproduction command above against the extracted bundle and the
     real `runs/…/checkpoints` directories, read-only;
   - expect 0 mismatches, 1606 encoding matches, 7 segments, and `rows.jsonl` hash
     `e9156b0c…0d98`; probabilities may differ in the last digits on another
     torch/CPU.
2. No native run of t27904 or its parent is proposed: the diagnosis predicts the
   same wall behavior.
3. Only after the observation-3 change passes offline gates and the frozen-direction
   screen, run one 5-minute native pilot:
   - **Model:** migrated child of `a0a93c29-s20-t27904` in a new run directory,
     with all ancestors untouched.
   - **Entry:** Continue on file 2 via guarded menu keys, same ready-setup room;
     no New Run.
   - **Caps:** ≤2048 learner steps, ≤300 s wall time from startup to cleanup,
     trace ≤128 MiB, terminal output ≤2 GiB.
   - **Stop:** first fault, death or restart need; no retry.
   - **Cleanup:** native shutdown, observer close, no game/listener/approval left.
   - **Assessment:** damage dealt/taken, clears/deaths and stagnation windows
     against the t27904 frozen condition on the same entry state.
   - Keep the 5 min → 15–30 min → 1 h → 4 h stages, each separately authorized.
