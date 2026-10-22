# Evidence: native-step-evidence-contract

- Date/time and timezone: 2026-10-19 14:53 Europe/Amsterdam (UTC+02:00)
- Git revision and dirty status: `5c5ba2e`; the checkout also contained unrelated user edits in `AGENTS.md`, `docs/AGENT_WORKFLOW.md`, `subagent.md`, `subagent_report.md`, `errors.txt`, and two wait scripts. Those files were preserved and excluded.
- Change scope and acceptance criteria: Offline specification/design clarification for native-step evidence. Distinguish bridge-held-override removal from physical neutrality, and caller-supplied reducer assertions from evidence provenance. Keep live stepping unsupported until exact interval consumption and endpoint completeness are independently verified for the target build.
- Game/mod/bridge versions (or not applicable): Not applicable; no game or bridge was run.
- Python/package versions and configuration hash: Windows Python 3.12.14; project dependency and configuration files unchanged.
- Scenario, split, seeds, budget, and stop conditions: No runtime scenario, samples, seed or training. Offline documentation/specification validation only.

## Results

| Check/requirement | Command/scenario | Exit code | Status | Evidence |
| --- | --- | --- | --- | --- |
| Active OpenSpec change | `./scripts/OpenSpec.ps1 validate episode-lifecycle --strict` | 0 | passed | Active change valid. |
| Full OpenSpec set | `./scripts/OpenSpec.ps1 validate --all --strict` | 0 | passed | 30 passed, 0 failed. |
| Windows quality gate | `./scripts/Check.ps1` with existing Lua test runtime, game `json.lua`, and private temporary directory | 0 | passed | 1644 tests passed; Ruff, formatting, mypy, Lua checks and OpenSpec gate passed; no broken requirements. |
| Diff whitespace | `git diff --check` | 0 | passed | No whitespace errors in the reviewed diff. |
| Real game | Not run | — | not_run | No launch, connection, action, mod deployment, approval or training. |

## Real game

No game process was started or inspected. No runtime authorization was created or used.

## RL evaluation (if applicable)

Not applicable. No policy, reward, model, normalizer, checkpoint or training data changed.

## Limitations and continuation

`ReleaseFact` means only that this bridge's held override was cleared. The offline reducer validates scalar consistency and ordering of caller-supplied facts; it cannot authenticate that an interval was consumed, that final game input was neutral, or that an event stream is quiescent. Callback trace records, frame deltas, snapshots and HP samples do not provide those proofs. READY remains a local, unverified candidate and no live step is supported.

The installed `resources/scripts/enums.lua` comment defines `MC_INPUT_ACTION` as a callback made when the game or an entity requests action input; nil leaves input unoverridden, and returned values are bool/float according to hook. It describes `MC_POST_UPDATE` as after a game update. The observer source returns bridge overrides from `MC_INPUT_ACTION` and counts/logs its own `MC_POST_UPDATE` callback. These files do not specify the engine's input-consumption point, callback ordering across mods, or a complete endpoint/event-quiescence signal. No engine implementation source is available in the installed script directory to establish those facts.

Self-review confirmed the spec, design, protocol and evidence guide agree on these limits. The local API audit found no documented signal that can prove exact input consumption or endpoint completeness; keep the live step unsupported on this evidence. Further evidence would need an authoritative engine contract or a separately authorized, bounded runtime investigation. No runtime authority is inferred here.
