# Evidence: passive oracle callback diagnostic

- Date/time and timezone: 2026-10-18, Europe/Amsterdam.
- Git revision and dirty status: based on 542e1ec; reviewed diagnostic/spec/test/documentation changes before commit.
- Scope: prepare bounded raw callback-order evidence for episode-lifecycle; preserve unsupported native sender/terminal receipts.
- Game/mod/bridge: J460 installed; observer source and default-off installation 0.4.2-dev. Game not launched or probed.
- Python/packages: CPython 3.12.14, pytest 9.1.1; unchanged environment and locks.
- Scenario/seeds/split/budget: fabricated Lua callback sequences, no training; production probe bounded to 120000 ms, 1024 log attempts, 400-byte lines and 128 diagnostic labels per mod load.

## Results

| Check/requirement | Command/scenario | Exit code | Status | Evidence |
|---|---|---|---|---|
| Targeted Lua behavior | .venv/Scripts/python.exe -m pytest tests/test_lua_oracle_probe.py -q | 0 | passed | 26 cases before the final lifecycle-sampling test; final gate includes all 27 |
| Offline quality gate | ./scripts/Check.ps1 with environment below | 0 | passed | 894 tests, zero skips; Ruff, 81 formatted files, strict mypy on 37 sources, pip consistency |
| Strict OpenSpec | ./scripts/OpenSpec.ps1 validate --all --strict (also in Check.ps1) | 0 | passed | 24/24 items |
| Closed-game default deployment | Guard process/approval absence; back up and copy only main.lua/metadata.xml; compare SHA256 | 0 | passed | Source/installed hashes below; private backup preserved |
| Normal launcher guard | ./Start-Isaac.cmd --preflight-only | 0 | passed | No launch; source/installed default-off hashes match |
| Enabled diagnostic bundle | Replace exactly one private copy flag and hash it | 0 | passed | Prepared privately, NOT installed |
| Live callback semantics | Manual play with read-only diagnostic attach | N/A | not_run | Requires diagnostic deployment, manual launch/Continue and fresh selected-instance confirmation |

Full-gate environment:

```powershell
$env:PYTHONPATH='C:\Users\<user>\Documents\Codex\2026-10-17\work-on-isaac-threrisaifuture-in-the\work\lua-test-runtime'
$env:ISAAC_JSON_LUA='C:\Program Files (x86)\Steam\steamapps\common\The Binding of Isaac Rebirth\resources\scripts\json.lua'
$env:TMP=Join-Path (Get-Location) 'reports\local\check-native-protocol'
$env:TEMP=$env:TMP
.\scripts\Check.ps1
```

An initial targeted run failed on a harness call missing the second mod argument
to unload; this was corrected to match the existing production signature. That
run also encountered the known global pytest temporary-junction cleanup permission
error; subsequent checks used the existing ignored private TMP/TEMP above. No
system temporary directories or junctions were deleted or reconfigured. The first
full gate passed 891 cases; the final 894 includes three self-review additions,
including an immediate next-update sample after game end.

## Configuration and deployment evidence

| Artifact | SHA256 |
|---|---|
| Source/installed main.lua, both diagnostics off | c20f8164b0b621510011139baa86bc429872c94bc8fb2db25a4c46073e54b2a3 |
| Source/installed metadata.xml | 05a108ceb4149fb80c55a2b32e21a47c4f186b61092dee7c2a9d5b37ab449262 |
| Private probe-enabled main.lua, not installed | 3d117f39c0902a53634cb962462256be7eed7ee28ab31a6e8b2b52d664fd9eed |

Private backup and enabled copy: reports/local/oracle-probe-20261018-093952/.
No action approval existed. No save, Cloud, options, other mod or executable was
changed. Both process guards passed immediately before deployment. The normal
launcher remains usable with diagnostics off. The diagnostic copy would correctly
fail its source-hash preflight; use the separate documented manual procedure,
without relaxing the normal guard.

## Self-review and specification mapping

| Dimension | Result |
|---|---|
| Completeness | 12/19 whole tasks accepted; seven unfinished. This is diagnostic preparation only. |
| Correctness of new requirement | Four scenarios covered by new Lua tests plus existing non-completed receipt rejection tests; actual engine callbacks not verified. |
| Coherence | Default-off literal opt-in, read-only attach, independent existing action trace and unchanged action/restart guards. |

Damage/award returns are nil even after logger/read failure; no entities or
callback arguments are mutated. Requested damage and later sampled HP remain
separate facts. Repeated damage samples may coalesce. All diagnostic state is
bounded and maps are cleared on stop; no full entity objects are retained.
Count/time/label/disconnect/exit/unload and reconnect exhaustion are exercised.
Projectile/effect removals are filtered; room transitions discard pending samples
without reusing the lifetime label counter. Missing enum identifiers fail closed
for diagnostics only. Probe failure does not close the observer or grant inputs.

The implementation does not import the producer outbox or passive timing ledger,
advertise a combined capability, emit OracleEvent, accept a terminal receipt or
weaken the existing NativeReceiptAssembler. Existing receipt tests continue to
fault on partial/cancelled completions; terminal short-step semantics remain
explicitly unsupported, not silently mapped to a successful transition.

API source: [ModCallbacks reference](https://wofsauge.github.io/IsaacDocs/rep/enums/ModCallbacks.html),
read 2026-10-18. Damage and award callbacks can affect gameplay through return
values, so this observer returns nil. Candidate hooks and ambiguity are detailed
in the [previous source audit](2026-10-17-native-oracle-api-audit.md). API reference
and enum presence do not establish installed J460 callback order.

## Real game

No runtime session, movement, shooting, death, revival or room transition occurred
in this batch. Process absence was checked for deployment; the game was never
started or stopped by the agent. Default-off deployment and preflight passed;
enabled bundle remains private and uninstalled. Standing ordinary-profile
observation permission is unchanged; launch and save selection remain manual.

## RL evaluation

Not applicable. No training, reset, reward attribution or achievement claim.

## Limitations and continuation

Seven whole tasks block archival: Lua combined capability/export (3.6), full
native multiplexing/attach/sender (3.8), runtime probes (4.1-4.3), real backend and
100 real episodes (5.1-5.2). No archive readiness is claimed. Task 4.1 needs actual
scenario evidence, including revival/transition/death where naturally available.
Training isolation and start/reset authority remain unresolved.

Next: while closed, deploy the reviewed private diagnostic copy; the operator
manually launches and selects file 2/Continue. Attach read-only once, record only
the current-session diagnostic lines and report partial coverage honestly. Then
after normal manual exit restore both default-off source files and verify hashes
and preflight. See [procedure](../docs/ORACLE_PROBE.md). No forced scenario or
unattended loop is authorized or needed.

## Subsequent diagnostic deployment (runtime still not run)

The user confirmed the game was closed. Process absence was checked again,
installed default-off hashes and prepared diagnostic hashes matched the table,
and no action approval existed. Only main.lua/metadata.xml were copied; installed
hashes were compared with the reviewed bundle after copying (exit 0). Default-off
files are backed up privately at
reports/local/oracle-probe-deployment-66b0039f6443461b86cd75c2dcc1bee0/.
The enabled diagnostic is now installed, superseding the earlier uninstalled
state above. No game launch, attach or gameplay occurred. Manual launch and file
selection are pending; normal launcher preflight is expected to reject this
temporary diagnostic difference until default-off cleanup. No guard was relaxed.
