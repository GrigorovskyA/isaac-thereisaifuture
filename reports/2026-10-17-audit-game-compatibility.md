# Evidence: audit-game-compatibility

- Date/time/timezone: 2026-10-17, approximately 11:24–11:35 CEST (Europe/Amsterdam, UTC+02:00).
- Starting Git revision: `b95358b7eb5ad066c788c072f6b5abd2b5cc7001`,
  initially clean; audit docs/OpenSpec dirty during checks. Final revision is the
  commit containing this report.
- Scope/acceptance: read-only compatibility/source/isolation audit; five acceptance
  criteria in the proposal, mapped below. No implementation or game-support claim.
- Versions: initially Repentance v1.7.9b.J835 / build 10102354; finally
  Repentance+ v1.9.7.17.J460 / build 22878971. REPENTOGON not detected in
  installed game; no bridge installed. Candidate commits pinned in the audit.
- Python/packages/config: Python 3.12.14; existing requirements-lock.txt and
  package.json/pnpm-lock.yaml unchanged. Experiment config/hash: N/A.
- Scenario/split/seeds/budget: audit only; no episodes, splits, seeds, training
  budget or policy. Stop conditions: no game input/reset/mod activation/save edits.

## Results

Commands use the discovered sanitized aliases from COMPATIBILITY_AUDIT. Source
checkouts are scratch data outside the project. Shell inspection success does not
establish runtime API support. A few initial exploratory rg paths did not exist;
listing the actual source tree resolved them. Failed searches supply no evidence.

| Check/requirement | Command/scenario | Exit code | Status | Evidence |
|---|---|---|---|---|
| Steam libraries and installed DLC | Get-ItemProperty HKCU:\Software\Valve\Steam; Get-Content "<Steam>/steamapps/libraryfolders.vdf"; Get-Content "<Steam>/steamapps/appmanifest_250900.acf" | 0 | passed | Audit L1–L3: one registered library; final installed depots, target 0, download/stage totals complete |
| Edition/version | Get-Process isaac*; Get-Content "<Repentance+>/log.txt" -TotalCount 28; Get-FileHash "<Game>/isaac-ng.exe" | 0 | passed | L3/L5: v1.9.7.17 title, fresh J460 log, executable SHA-256 |
| Config/mods/runtime | Get-Content "<Game>/savedatapath.txt"; Get-ChildItem "<Game>" -Force; Get-ChildItem "<Game>/mods"; Select-String "<Repentance+>/options.ini" -Pattern "SteamCloud\|EnableMods\|EnableDebug\|PauseOn\|SaveCommand" | 0 | passed | L6/L7/L9/L10; no detected REPENTOGON version; public mod/disabled-marker table |
| Saves/Cloud | Get-ChildItem "<Documents>/My Games" -Directory; Get-ChildItem "<account-app>/remote" -Name; Get-Content "<account-app>/remotecache.vdf" -TotalCount 28 | 0 | passed | L8; filenames/config only, no private save contents committed |
| Source provenance | git clone --depth 1 <candidate-url> <scratch-path>; git -C <scratch-path> log -1 --format="%H %cI"; git ls-tree -r --name-only HEAD | 0 | passed | Four candidates + REPENTOGON + Launcher, commits/licenses in audit; no downloaded code executed |
| Source behavior | Get-Content/rg main.lua, connection/server.py, action_handler.lua, isaac_env.py, SaveSyncing.cpp, REPENTOGONOptions.h | 0 on resolved files | passed | Transport/blocking/protocol/save findings in audit |
| Primary documentation | Official Steam DLC, Valve Steamworks, LuaSocket maintainers, REPENTOGON docs and installed game LuaDocs/enums | N/A | passed | Primary links/pinned sources in audit; community API pages supplementary |
| Offline quality gates | .\scripts\Check.ps1 | 0 | passed | Ruff, format 4 files, mypy 2 source files, pytest 2/2, pip consistency; 3 specs + 1 change strict |
| Change validation | .\scripts\OpenSpec.ps1 validate audit-game-compatibility --strict | 0 | passed | Valid before archive |
| Main spec synchronization | .\scripts\OpenSpec.ps1 validate --specs --strict; Python comparison of both delta requirement blocks with main spec | 0 | passed | Both complete blocks match; original Purpose and unrelated requirements retained |
| Archive | .\scripts\OpenSpec.ps1 archive audit-game-compatibility --yes | 0 | passed | Complete tasks, specs already synchronized; archived as 2026-10-17-audit-game-compatibility |
| Post-archive strict validation | .\scripts\OpenSpec.ps1 validate --all --strict; .\scripts\OpenSpec.ps1 list --json | 0 | passed | All 3 main specs valid; no active changes |
| Module/bridge probe | Observer installation and optional --luadebug on approved profile | N/A | blocked | Profile isolation and mod/launch-option changes not authorized/verified |
| Real observation soak | Correlated snapshots, pause/reconnect, ten minutes | N/A | not_run | No adapter implemented; next milestone |
| Actions/release/endings/reset | Controlled sequences, disconnect/deadline and new episode | N/A | not_run | Later milestones; no authorized isolated profile |
| Isolation/restoration | Disposable-copy restore and write-set/main-profile hash verification | N/A | blocked | Options/paths inspected only; backup/restore not executed |
| RL smoke/evaluation | Smoke-RL.ps1, training, evaluation | N/A | not_run | No dependency/RL changes; synthetic smoke does not establish Isaac support |

## Real game

No controlled game test; session/episode/frame IDs: N/A. Game was closed at first
inventory. User subsequently requested Repentance+ installation. Steam completed
it and an already queued launch started the game. The assistant navigated Steam
and attempted to cancel that launch, without initiating a game test. The user
stopped Computer Use with Escape; no further UI automation followed.

Fresh version/configuration/log and save-cache filenames were read afterwards.
Startup created Repentance+ options/backups/Cloud-cache files and loaded existing
mods. These observations do not verify bridge behavior or an isolated profile.
No assistant command edited saves/options/Cloud/mod activation, reset, or applied
game input. Main-save byte preservation across the user's launch is **not verified**:
no prelaunch private hash baseline exists. Save backup/restore was not performed.

## Acceptance mapping

| Criterion | Evidence | Result |
|---|---|---|
| Installed/source/isolation matrix | Audit L1–L10, edition/mod tables, candidate/capability matrices | passed |
| Unknown runtime capabilities explicit | Capability matrix and separately blocked/not_run probes | passed |
| One bridge recommendation | Original minimal adapter; source-backed reuse/adapt trade-offs | passed |
| Exact gated actions and next task | Audit final numbered handoff, profile/Cloud/artifact gates | passed |
| Checks and separate self-review | Results above and review below | passed |

Runtime tests were outside the audit acceptance criteria from the proposal;
none was counted as completed integration work.

## OpenSpec verification and separate self-review

The implementing agent made a separate review pass over proposal, delta, design,
tasks, audit, evidence, STATUS and all documentation diffs. This is **self-review**,
not independent review.

| Dimension | Result |
|---|---|
| Completeness | Five research/delivery tasks verified by audit; two checks/handoff tasks completed after report/STATUS/diff review, final 7/7 |
| Correctness | Two modified requirements mapped to evidence levels and isolation; all four process/documentation scenarios inspected |
| Coherence | Minimal original adapter matches design; no game bridge/dependency implementation implied |
| Pattern consistency | Existing Markdown/OpenSpec/template conventions, English only, no redundant document-existence tests |

Scenario mapping:

- Candidate claims support: README retained as claim; source/runtime gaps explicit.
- Audit completes with gated probes: exact destination, launch option, profile gate
  and failure handling documented; no runtime support claimed.
- Reset without isolation: no reset performed; future destructive test blocked.
- Shared slot: shared options, mods/data, Steam account/Cloud, REPENTOGON vanilla
  synchronization and game state identified; restoration still required.

Review corrections: retain pre/post-install distinction; preserve M0's runtime
gate despite item 01 completion; identify incomplete isaac-rl-agent license grant;
do not equate content-load lines with mod activation or startup with a game probe.
No remaining critical issues, warnings or suggestions in audit scope. All applicable
audit checks passed; real-game compatibility and isolation remain unverified.

## RL evaluation

Not applicable; no policy, checkpoint, learning result or episode produced.

## Limitations and continuation

Named branch, present Cloud/server state, write isolation/restoration, socket
loadability, callback timing, control/release, endings and reset determinism remain
unknown. User gameplay can change local files independently of this audit.

Next: implement bridge-handshake-and-observation locally, then obtain authorization
for the finished artifact, isolated profile and required launch option before a
runtime probe. REPENTOGON is not required by the recommended observation slice.

Commit/push only audit/docs/OpenSpec. Exclude saves, private logs, credentials,
raw local manifests, machine identities and downloaded source checkouts.
