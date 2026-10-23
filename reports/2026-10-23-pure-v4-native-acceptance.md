# Evidence: pure-v4 schema-5 Windows gate and native qualification

- Date: 2026-10-23, Europe/Amsterdam (CEST, UTC+02:00).
- Source revision: `c494aff6774b1fee5a4013f0b543a88943a7cc43`, personal identity
  GrigorovskiiA, pushed to origin/main. Only pure-v4 and the handed-off pure-v3
  report were staged; unrelated untracked `tools/` preserved.
- Scope: OpenSpec `pure-v4-map-hazards-and-stall`, observation schema 5 (3499 floats),
  action v2 [5,5,4] held six updates, reward v5 (stall -10), oracle kill/hit counters,
  and training timing fields. No scripted gameplay or reward shaping added.
- Game: Steam Repentance+ 1.9.7.17, file 2, observer 0.5.0-dev / Lua 5.3.
  Mod deployed with Isaac closed, only main.lua and metadata.xml replaced.
  main.lua SHA256 `38fa156b5bb49e935a987dcdd565cd1cec7edc1420a591a68f15c4ab2b948556`;
  metadata.xml `00f46cc452c2a4e7809c14501d94de2db1ac94b1dde12b3c25d163922f34b997`.
- Python 3.12 project .venv, torch 2.14.1+cpu; `configs/training-pure-v4.yaml`.
  Full config SHA256 `336fe9b4018d419ab6be14816b5005b27617cd51cbea859d2f4a793677bc9969`;
  contract `ec6d76e1bf477884578d243d02beef7de919ce9c4dc8f56f06bd0afa2a59ebbf`.
  Seed 1, gamma 0.995, ent_coef 0.005; fresh lineage runs/pure-v4, --initialize once.
- Budget/plan: one 900-second qualification wrapper timer from launch, stop.forever
  at its absolute deadline, parent PowerShell keeps Start-Job alive. Native sessions
  retain the 28740-second lease ceiling; disk 20480000000 bytes, fault cap 5, unlimited
  authorized death/stall New Runs. Any qualification fault or missing requirement
  is reported; it does not establish acceptance. One-hour resume is conditional on
  successful qualification; no initialization fallback or old-lineage resume.
- Passive audit: ignored helper SHA256
  `c91dd4cf6c52553dfa7860b357fd6aa7fb33343dce9d17fad590af62ee7f2ea9`;
  cap 1000 seconds, 20000 records, 64 MiB per worker. Unchanged transport values
  and actual pre-normalization policy stall scalars are sampled. Diagnostic oracle
  counters are recorded separately and never passed into policy input.

## Results

| Check/requirement | Command/scenario | Exit code | Status | Evidence |
|---|---|---|---|---|
| Windows gate including Lua | scripts/Check.ps1, isolated lupa.lua53 + installed JSON decoder | 0 | passed | reports/local/pure-v4-acceptance-20261023/check.log: 1175 passed, no skips; mypy 31 files; lint/format/pip clean, strict OpenSpec 15/15 |
| CPU RL stack | scripts/Smoke-RL.ps1 | 0 | passed | smoke.log: 16 steps, 3499 inputs, actions [5,5,4]; no game integration claim |
| Closed-game deployment | Copy only main.lua / metadata.xml and compare SHA256 | 0 | passed | deployed-hashes.json; both source and installed hashes match |
| Typed obstacles, room shape, minimap | Native snapshots + UI observation | n/a | not_run | Pending qualification |
| Stall clock | Actual policy scalar rises and resets on progress | n/a | not_run | Pending qualification |
| Kills and own-bomb hits | Native oracle counters and episode CSV | n/a | not_run | Pending qualification |
| Restarts and checkpoint reload | Timer/death New Run, actual checkpoint load | n/a | not_run | Pending qualification |
| Train timing | train.csv rollout_seconds / update_seconds | n/a | not_run | Pending qualification |

## Real game

Pure-v3 is stopped at `03b9c5e3-s1-t257024`; its final learner exit was 0 and
cleanup_errors empty. There was no running Isaac or native learner during deployment.
Fresh pure-v4 gameplay is pending. Guarded Steam/menu startup must confirm file 2;
gameplay stays on the structured bridge. Read-only UI screenshots are used only
to compare visible geometry/map with the structured facts, not as policy inputs.

## RL evaluation

Qualification only, one seed, no improvement or achievement claim. Synthetic smoke
and optimizer updates do not prove better play. The purpose is native correctness.

## Limitations and continuation

Task 2.2 is complete. Task 2.3 stays open until every required native scenario is
verified. Unseen obstacle classes, special maps and other shapes are not assumed
correct. No working-copy edits during an active session; finalize this report and
task/status documentation only after qualification stops and cleanup is checked.
