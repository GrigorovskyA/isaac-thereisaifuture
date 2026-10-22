# Evidence: bounded post-update HP diagnostic

- Date/time and timezone: 2026-10-18, Europe/Amsterdam.
- Git revision: based on b53f21c; source/spec/tests/docs reviewed before commit.
- Scope: raw HP observation at this observer's MC_POST_UPDATE callback, separate from attempted damage and NPC-update samples. No outcome or synchronization guarantee.
- Game/mod: observer 0.4.4-dev source installed while closed; later runtime evidence linked below supersedes the provisional launch observation.
- Python/packages: existing CPython 3.12.14, pytest 9.1.1; dependencies/locks unchanged.
- Scenario/budget: fabricated callback schedules and Lua garbage-collection checks; at most 16 staged targets, existing 120 s / 1024 log attempts / 128 labels / 400 bytes remain unchanged.

## Results

| Check/requirement | Command/scenario | Exit code | Status | Evidence |
|---|---|---|---|---|
| New and existing probe cases | .venv/Scripts/python.exe -m pytest tests/test_lua_post_update_hp.py tests/test_lua_oracle_probe.py -q | 0 | passed | 54 cases: 27 new deferred-sampling and 27 existing probe cases |
| Full Windows gate | ./scripts/Check.ps1 with environment below | 0 | passed | 945 tests, zero skips; Ruff, 84 formatted files, strict mypy 37 sources, pip consistency, OpenSpec 24/24 |
| Closed-game update | Process/approval/old-hash guards; back up two files; copy source; compare hashes | 0 | passed | Source/installed hashes below |
| Launcher preflight | ./Start-Isaac.cmd --preflight-only | 0 | passed | No game launched by preflight |
| One operator-directed launch request | launcher.preflight followed by one Popen([isaac-ng.exe, --luadebug], cwd=game directory) | 0 | passed | Request returned launcher PID 22872; readiness explicitly false |
| Provisional game startup/Lua access | Check process and current registration log after request | N/A | failed | Initially no live process/fresh registration; later resolved by operator confirmation of the pending Steam custom-parameters dialog; no launch retry |
| Native post-update HP ordering | Later actual manual combat with explicit oracle_probe_v1 | N/A | passed | Raw sampling verified in reports/2026-10-18-post-update-hp-runtime.md; first post-update is not an applied-damage barrier |
| Final strict project validation | ./scripts/OpenSpec.ps1 validate --all --strict | 0 | passed | 24/24 items after final spec/design/evidence review |

Full-gate environment:

```powershell
$env:PYTHONPATH='C:\Users\<user>\Documents\Codex\2026-10-17\work-on-isaac-threrisaifuture-in-the\work\lua-test-runtime'
$env:ISAAC_JSON_LUA='C:\Program Files (x86)\Steam\steamapps\common\The Binding of Isaac Rebirth\resources\scripts\json.lua'
$env:TMP=Join-Path (Get-Location) 'reports\local\check-native-protocol'
$env:TEMP=$env:TMP
.\scripts\Check.ps1
```

Two initial Python harness line-length findings were fixed before the full gate.
Strict OpenSpec later rejected a long launch-authority paragraph; its permitted
process-launch case was moved into a scenario without relaxing reset/isolation
requirements. Final strict project validation is recorded below after doc review.

## Sources and design

Read 2026-10-18: [Entity.Exists](https://wofsauge.github.io/IsaacDocs/rep/Entity.html#exists)
documents checking whether an entity remains spawned; [MC_POST_UPDATE](https://wofsauge.github.io/IsaacDocs/rep/enums/ModCallbacks.html#mc_post_update)
documents an after-update callback that is not called while paused. These are
primary API references, not proof of J460 effect ordering or native handle lifetime.

Each diagnostic damage/init callback stages a bounded entry. Repeated labels
coalesce with first queued frame/update, attempt count and init marker. The batch
is detached before sampling at post-update. The older NPC-update marker cannot
consume it. New entries are sampled only once; raw negative/increased/unchanged
HP is preserved without inferring realized damage or attribution.

Removed targets immediately release their reference and retain only a scalar
tombstone. Missing/relabelled targets produce status without HP. Stop/fault,
disconnect/exit/unload, game start/end and room/floor callbacks clear targets.
The seventeenth pending label stops diagnostics with reason=pending rather than
evicting data. Reentrant diagnostic reads invalidate the window; further staged
reads/logs are suppressed and references are released. No game object is mutated.

## Self-review and specification mapping

The four new deferred-sampling scenarios map to behavioral tests for old NPC HP
versus changed post-update HP, repeat coalescing, removed/missing/relabelled
targets, the actual 16/17 boundary and cleanup. Weak Lua tables plus explicit GC
verify reference retention until sampling and release on success, removal,
overflow, nine lifecycle/stop paths, four read/logger failures and reentrancy.
Tests also exercise pointer/context/property reentry during staging and sampling.
Ordinary observation survives diagnostic failure; no native outcome is emitted.

No step reader, action/restart authority, event model or training gate changed.
The user separately authorized one on-demand agent launch for agreed checks;
AGENTS/config/specs now distinguish that from unattended startup/recovery.
Manual save-file selection/Continue and normal exit remain required. The user's
Steam --luadebug setting is reported, not independently verified; this launch
request used the established explicit argument and did not edit Steam settings.

## Deployment and real game

Private backup: reports/local/post-update-hp-deployment-c4ad2e857d9344668021294e6c3d5e7a/.
Installed/source SHA256:

- main.lua: 9e720026da0bea6ddc7e2f51c1d11683e6807c85568ed31fa859f81932ecac45.
- metadata.xml: 085c10c2a14de0ef7600dcd8195621079e9843dcca3572df1902b66ee98e78b1.

The following describes the initial deployment check, before the later runtime
confirmation linked above. Only these two reviewed files were updated, with no private action approval.
Mode activation still needs no file replacement. No save, Cloud, other mod,
options or executable changed. One process launch was requested after preflight;
the process did not remain visible to tasklist and no fresh observer registration
was found. No hang/crash/Steam-parameter cause is inferred from that absence.
No auto-retry, reset, gameplay input, attach or diagnostic budget consumption
occurred. The operator was asked for the observed startup/selection status.

## RL evaluation

Not applicable; no model, reward, training or achievement claim.

## Limitations and continuation

12/19 whole tasks remain accepted. Native sampler ordering, negotiated activation,
death/revival/floor coverage, actual step application, event barrier and isolated
training start/reset remain unfinished. No archive readiness is claimed.

Even a live post-update HP sample will not prove all engine/other-mod effects
finished, assign damage sources or separate simultaneous healing/damage. The
known old-HP NPC-update counterexample remains a reason to keep outcomes gated.
Subsequent result: the operator confirmed the Steam custom-parameters dialog and
file-2/Continue readiness; one attach verified 0.4.4-dev and raw sampling. See
[runtime evidence](2026-10-18-post-update-hp-runtime.md), including the first-
post-update old-HP counterexample and early disconnect. This resolves startup,
not event/step acceptance. Next: bounded later-frame settlement design offline.
