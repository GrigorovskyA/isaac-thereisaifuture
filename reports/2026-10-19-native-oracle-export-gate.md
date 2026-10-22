# Evidence: native-oracle-export-gate

- Date/time and timezone: 2026-10-19, Europe/Amsterdam.
- Git revision and dirty status: based on `ff7a20d`; pre-existing user edits to agent/workflow files and unrelated `errors.txt`/wait scripts were preserved.
- Change scope and acceptance criteria: clarify the OpenSpec gate for episode-lifecycle task 3.6 without adding Lua event export or claiming runtime acceptance.
- Game/mod/bridge versions: no game connection; local J460 callback identifiers inspected read-only. Prior semantic findings are linked to the native oracle API audit.
- Python/package versions and configuration hash: project `.venv`, CPython 3.12.14; no dependency or configuration changes.
- Scenario, split, seeds, budget, and stop conditions: offline source/spec review only; no runtime budget or training.

## Results

| Check/requirement | Command/scenario | Exit code | Status | Evidence |
|---|---|---:|---|---|
| Installed callback identifiers | `rg` over installed `resources/scripts/enums.lua` for candidate callback names | 0 | passed | Identifiers exist; names alone do not prove event semantics or callback order. |
| Oracle event source audit | Review `reports/2026-10-17-native-oracle-api-audit.md` and active lifecycle design | 0 | passed | Seven-kind eligibility table and explicit export prerequisites added to design. |
| Windows quality gate | Set `TEMP`, `TMP`, and `TMPDIR` to ignored `reports/local/check-tmp-20261019`, then run `./scripts/Check.ps1` | 0 | passed | 1117 passed; 14 optional isolated Lua 5.3 tests skipped because `lupa.lua53` is absent; Ruff, format, mypy, pip consistency and strict OpenSpec passed. |
| Pinned OpenSpec strict validation | `./scripts/OpenSpec.ps1 validate --all --strict` | 0 | passed | 30 changes/specs passed. |
| Parser regression suite reviewed in the same checkout | `./.venv/Scripts/python.exe -m pytest tests/test_firing_trace.py -q -p no:cacheprovider` | 0 | passed | 150 passed. |
| Whitespace/conflict check | `git diff --check` | 0 | passed | No whitespace errors. Existing line-ending warnings concern untouched user files. |
| Native event export | No runtime probe authorized or run | N/A | not_run | No Lua `native_oracle_event` emitter or capability was added; task 3.6 stays open. |

The first full-check attempt used the system pytest temp directory and reached
100% test completion, then failed during pytest teardown with `WinError 5` on
`C:\Users\<user>\AppData\Local\Temp\pytest-current`. Re-running with the
private ignored temp directory above completed successfully. No dependency was
installed to enable the optional Lua 5.3 harness.

## Real game

No game launch, connection, control, deployment, save selection, reset, approval
change or private-log access occurred. The local enum inspection establishes only
that callback identifiers are present in the installed script source.

## RL evaluation

Not applicable. No training or model evaluation occurred.

## Limitations and continuation

The candidate callbacks do not yet support every required `OracleEvent` field or
prove event timing and delivery. The hello protocol also needs a frozen decision
about aggregate versus per-kind capability negotiation before a partial event
export can be represented honestly. Task 3.6 and dependent transaction task 3.8
remain open. Next runtime evidence requires a separately scoped, finite operator
authorization and verified current instance/readiness. This offline work did not
read, create, or renew an approval. Self-review confirmed raw callback/HP
diagnostics remain separate from policy and reward events.
