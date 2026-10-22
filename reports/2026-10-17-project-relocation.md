# Evidence: project relocation to D:\isaac

- Date/time and timezone: 2026-10-17, Europe/Amsterdam (CEST).
- Git revision and dirty status: clean main at 6bc7ab8 before migration; only this documentation follow-up dirty after verification. Git history, origin and active OpenSpec state preserved.
- Change scope and acceptance criteria: user requested relocation to D:\isaac. Copy all project/local/private artifacts without overwriting unrelated destination data, verify contents, repair local runtime paths and run checks from D. Keep game installation/saves/settings unchanged.
- Game/mod/bridge versions: no game launch or deployment. Existing installed observer 0.3.1 untouched; bridge-safe-actions remains active with runtime acceptance incomplete.
- Python/package versions and configuration hash: Python 3.12.14; all 45 installed distribution versions match the retained source copy. Editable source resolves to D:\isaac\src; virtual environment prefix is D:\isaac\.venv. Torch 2.14.1+cpu, Gymnasium 1.4.0, NumPy 2.5.4 imported successfully.
- Scenario, split, seeds, budget and stop conditions: filesystem relocation/offline checks only. Refuse a nonempty destination, stop on copy/hash/runtime/check failure. No training, game seed, controlled input, reset or launch.

## Results

| Check/requirement | Command/scenario | Exit code | Status | Evidence |
|---|---|---|---|---|
| Destination and source | Path/type, free space and Git checks | 0 | passed | D:\isaac existed but was empty; source was a real clean checkout; sufficient D space |
| Complete copy | robocopy /E /COPY:DAT /DCOPY:DAT /R:1 /W:1 /SL /SJ | 1 expected success | passed | 32,523 files, 1,083,742,154 bytes; zero copy failures; private logs/backups and .git retained locally |
| Full verification | SHA-256/size comparison of every regular file plus reparse target comparison | 0 | passed | All 32,523 files and 144 package junctions match before environment repairs; private manifest under ignored reports/local/migration-20261017 |
| Environment relocation | Base Python -m venv --without-pip; editable .pth/direct_url and console-launcher repair | 0 | passed | Existing packages reused; activation/config paths regenerated; 22 console-launcher files rebound; affected local RECORD entries updated |
| Dependency metadata | Compare importlib.metadata distribution names/versions | 0 | passed | All 45 package versions identical; no dependency upgrade/download |
| Direct commands | .venv\Scripts\pytest.exe --version; pip.exe --version | 0 | passed | Pytest 9.1.1 and pip 25.0.1 launch through D environment |
| Source identity | Python sys.prefix and package __file__ | 0 | passed | D environment and D source path, not the retained rollback copy |
| OpenSpec root | scripts/OpenSpec.ps1 list --json | 0 | passed | Root D:\isaac; bridge-safe-actions still 6/8 tasks complete |
| Offline gates | .\scripts\Check.ps1 with isolated Lua test runtime and installed JSON source | 0 | passed | 241 tests, no skips; Ruff/format/strict mypy/pip consistency and seven strict OpenSpec items |
| Native dependencies | Python import torch,gymnasium,numpy | 0 | passed | Compiled/native package imports work after relocation; no RL training |
| Privacy/diff | git diff --check and explicit staged-path review | 0 | passed | Only README, STATUS and this report committed; no environment, private manifests/logs/backups/saves |
| Real-game behavior | Manual launch/current slot/50 action sequences | N/A | not_run | Relocation does not verify the game or resolve the earlier memory-related launch failure |

## Real game

No launch, save selection, observer deployment, controller input, reset, Steam
setting, Cloud option, game option or save operation was performed. The installed
observer remains as before relocation. Standing ordinary-profile action-test
permission is unchanged; current runtime/slot confirmation and actual evidence
are still required.

## RL evaluation

Not applicable. Importing the installed RL libraries is an environment check,
not training, environment integration or progression evidence.

## Self-review and limitations

Full copy verification completed before changing environment bindings or replacing
the old working location. A first serial read-only hash helper was stopped to
parallelize verification; the completed check verified all files and identified
144 existing pnpm junctions. An attempted direct replacement of those junctions
was rejected by automatic approval review (reported only as blocked by policy).
No junction-replacement operation was executed. The safe completed approach
preserves them through the old-path compatibility alias instead.

The original directory was renamed to a distinct pre-move rollback directory;
its data was not deleted. The old working path is now a junction to D:\isaac.
This keeps legacy shortcuts, existing chat references and package junctions valid.
The active project and Python source are on D. Do not remove the old compatibility
junction while the package graph still uses that alias. The rollback copy is a
separate local duplicate, not the active checkout, and remains excluded from Git.
No claim is made that all absolute legacy references were eliminated.

Only project-local environment metadata and launchers were repaired; the bundled
base Python outside the repository remains an external runtime prerequisite.
Dependency versions, source code, reset limits and OpenSpec acceptance scope did
not change. This is a documentation-only project change, so no new behavioral
OpenSpec proposal is needed. Continue work from D:\isaac; live action acceptance
remains unfinished and the active change must not be archived.
