# Evidence: offline batch review

- Date/time and timezone: 2026-10-17 21:39 Europe/Amsterdam.
- Git revision and dirty status: HEAD a6296ab; user-modified tracked files and
  substantial untracked offline modules/specifications/tests preserved.
- Scope: current offline quality gates, strict OpenSpec validation and targeted
  self-review; no acceptance of later real-game milestones.
- Game/mod/bridge versions: not probed in this review; earlier runtime evidence
  records J460 and observer 0.3.1.
- Python: 3.12.14, existing D:\isaac\.venv; dependencies unchanged.
- Scenario/budget: finite offline checks; no training or game actions.

## Results

| Check | Command/scenario | Exit code | Status | Evidence |
|---|---|---|---|---|
| Initial strict validation | `.\scripts\OpenSpec.ps1 validate --all --strict` | 1 | failed | 23/25; two main requirement bodies exceeded 500 characters |
| Spec repair | Reorganize profile-isolation and negotiation detail into scenarios; mirror active deltas | 0 | passed | Same restrictions retained, main/delta blocks agree |
| Initial full check | `.\scripts\Check.ps1` with isolated Lua runtime | 1 | failed | Test bodies completed; pytest shared-temp cleanup raised WinError 5 |
| Full check retry | Same command with process-local TEMP/TMP under ignored reports/local | 0 | passed | Ruff; 59 files formatted; mypy 31 sources; 426 tests with no skips; pip; strict validation 25/25 |
| Entity ordering | Player-relative offsets compared against design/entities.py/sim.py | 0 | passed | Prior finding withdrawn: offsets were mistakenly treated as room coordinates; offset zero is nearest to the player |
| Later game integration | Real entities/backend/episodes/training | n/a | not_run | Synthetic backends are not Isaac evidence |

Lua tests used PYTHONPATH pointing to the existing isolated lua-test-runtime and
ISAAC_JSON_LUA pointing to installed resources/scripts/json.lua. TEMP/TMP were
changed only in the check process; no system settings or dependencies changed.

## Real game

No live game session, input, launch, reset or save selection occurred in this
review. Earlier reports already establish item-03 50/50 acceptance and release;
this review does not rerun or independently reverify that runtime evidence.
The ordinary-profile exception does not permit training or establish isolation.

## RL evaluation

Not run. training.main requires an environment factory and explicitly fails
without one. env.py depends on a GameBackend protocol; the offline simulator
cannot establish an Isaac-connected training environment.

## Limitations and continuation

This was a targeted self-review by one agent, not an exhaustive audit or
independent review. The earlier ordering finding was incorrect: Entity.position
is explicitly a player-relative offset. Subtracting player_position would break
the contract. A new translation regression test confirms ordering does not
change when only the player's room-local position changes.
Then verify native entity APIs, implement bounded export and record real fixtures
for item 04. Finish the already accepted item-03 archival separately. Do not
archive later changes based on structural validation or synthetic tests alone.
The user subsequently authorized committing the offline batch and continuing
item 04. Synthetic item knowledge is explicitly fake data. errors.txt is a local
check transcript and is excluded from the commit along with ignored private data.
