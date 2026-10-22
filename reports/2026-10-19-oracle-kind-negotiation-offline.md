# Evidence: oracle-kind-negotiation-20261019-01 (episode-lifecycle, offline Python negotiation)

- Date/time and timezone: 2026-10-19, Europe/Amsterdam (macOS worker, shared SMB checkout).
- Git revision and dirty status: 69700b3 (Freeze per-kind oracle export gate). The worktree already held unrelated edits to AGENTS.md, docs/AGENT_WORKFLOW.md, reports/2026-10-19-oracle-probe-live-runtime.md, subagent.md and subagent_report.md plus untracked errors.txt and wait scripts; all were preserved and none was touched. No commit, push or archive.
- Change scope and acceptance criteria: Python-only opt-in for requiring per-kind native OracleEvent capabilities, per the frozen contract in openspec/changes/episode-lifecycle/design.md. Handshake groundwork only: no Lua advertisement, no OracleEvent creation or emission, no event semantics, reward or training change, and no kind is marked runtime-eligible. Tasks 3.6 and 3.8 stay open.
- Game/mod/bridge versions: not applicable. No game, deployment, approval, training, save, Steam Cloud, private log or model was used.
- Python/package versions and configuration hash: Python 3.12.13 (~/.venvs/isaac), repository-pinned ruff, mypy, pytest and OpenSpec. No model or configuration hash.
- Scenario, split, seeds, budget, and stop conditions: simulated loopback peers (tests/test_native_negotiation.py `SimulatedPeers`), no seeds, no learner.

## Changes

| Path | Change |
|---|---|
| src/isaac_threrisaifuture/observer_client.py | New `ORACLE_KINDS` (from `OracleKind`), `oracle_kind_capability(kind)` returning `oracle_<kind>_v1`, and `ObserverConfig.native_oracle_kinds: tuple[OracleKind, ...] | None = None` appended as the last field. `accept()` appends the per-kind names after `entity_action_v1` in native mode only. |
| tests/test_oracle_negotiation.py | 59 new cases (73 in the file; the 14 pre-existing probe cases are unchanged). |
| openspec/changes/episode-lifecycle/specs/episode-lifecycle/spec.md | New requirement "Per-kind oracle capability negotiation is explicit and fail-closed" with six scenarios. |
| openspec/changes/episode-lifecycle/design.md | New subsection "Python per-kind negotiation groundwork (offline, 2026-10-19)" at the end of the task 3.6 gate section. |
| openspec/changes/episode-lifecycle/tasks.md | New offline subtask 3.12 (accepted after Windows checks). Tasks 3.6 and 3.8 remain unchecked. |
| reports/2026-10-19-oracle-kind-negotiation-offline.md | This report. |

`observation.py` was not needed: the existing `HelloAck.capabilities` limit of 16 and the existing
`set(required) <= set(ack.capabilities)` check already provide the fail-closed behavior. `agent-status.json`
and `subagent_report.md` were not modified (coordinator-owned this task).

## Behavior

- `native_oracle_kinds=None` (default) requests nothing, so every existing mode sends exactly the previous list.
- A non-`None` value must be an actual nonempty `tuple` of unique, exact `OracleKind` strings (no `str` subclasses, lists, sets or strings) and requires `native_episode_steps=True`. Violations raise `ValueError` in `__post_init__`, before a listener opens or a hello is sent. Native mode already rejects action, restart and entity-observation modes, the probe and the live loop, so every incompatible combination is rejected locally.
- Hello: base capabilities, `entity_action_v1`, then the requested `oracle_<kind>_v1` names in request order.
- Peer fail-closed: any omitted required name (old peer, partial peer, missing `entity_action_v1`, `_v2`/prefix/aggregate/other-kind names) raises `ProtocolError`, closes the peer and leaves no negotiated state, so no snapshot or command is read or sent.
- Boundary: eight other advertised names (`CAPABILITIES`, `LIVE_LOOP_CAPABILITIES`, `oracle_probe_v1`; each appears in mod/observer/main.lua), `entity_action_v1` and seven kind names total exactly 16 and are accepted; a seventeenth entry is rejected as an invalid `HelloAck` even if every required name is present. The limit is unchanged.

## Results

| Check/requirement | Command/scenario | Exit code | Status | Evidence |
|---|---|---:|---|---|
| Baseline focused tests before edits | `~/.venvs/isaac/bin/python -m pytest -p no:cacheprovider -q tests/test_oracle_negotiation.py tests/test_native_negotiation.py` | 0 | passed | 30 passed. |
| Focused tests after edits | same command | 0 | passed | 89 passed (73 in test_oracle_negotiation.py, 16 in test_native_negotiation.py). |
| Mutation check | Temporarily emptied the per-kind `required.extend` | 1 | passed (tests fail as intended) | 21 failed; restored and re-ran: 73 passed in test_oracle_negotiation.py. |
| Full offline suite | `ISAAC_JSON_LUA=~/.cache/isaac-json/json.lua ~/.venvs/isaac/bin/python -m pytest -p no:cacheprovider -m "not game" -q -x` | 0 | passed | 1703 passed (macOS, non-game JSON shim; Windows Check.ps1 remains authoritative). |
| Lint | `ruff check --no-cache src tests scripts/smoke_rl.py` | 0 | passed | All checks passed. |
| Format | `ruff format --no-cache --check src tests scripts/smoke_rl.py` | 0 | passed | 105 files already formatted. |
| Types | `mypy --platform win32 --cache-dir ~/.cache/isaac-mypy` | 0 | passed | No issues in 44 source files. |
| Whitespace | `git diff --check -- <changed paths>` | 0 | passed | No whitespace errors (only CRLF autocrlf warnings). |
| OpenSpec strict | `XDG_CONFIG_HOME=$PWD/.tooling OPENSPEC_TELEMETRY=0 node ~/.cache/isaac-openspec/node_modules/@fission-ai/openspec/bin/openspec.js validate episode-lifecycle --strict` (the pinned CLI that scripts/check.sh uses; `./scripts/OpenSpec.ps1` is PowerShell/Windows-only) | 0 | passed | "Change 'episode-lifecycle' is valid". The first attempt failed the strict warning that a requirement exceeded 500 characters; the requirement was shortened and details moved to scenarios. |
| Focused Windows tests | `./.venv/Scripts/python.exe -m pytest -m 'not game' -q tests/test_oracle_negotiation.py tests/test_native_negotiation.py` with `TEMP`/`TMP` set to `C:\Users\<user>\AppData\Local\Temp\isaac-oracle-kind-focused-20261019-01` | 0 | passed | 89 passed. |
| Windows quality gate | `./scripts/Check.ps1` with `TEMP`/`TMP` set to `C:\Users\<user>\AppData\Local\Temp\isaac-oracle-kind-check-20261019-01` | 0 | passed | 1176 passed, 14 optional isolated-Lua tests skipped; Ruff, format, mypy, pip consistency and embedded strict OpenSpec passed. |
| Windows all-items strict | `./scripts/OpenSpec.ps1 validate --all --strict` | 0 | passed | 30/30 passed. |
| Real-game negotiation | Any Lua peer or Isaac session | N/A | not_run | Out of scope; the current Lua producer advertises none of these names. |

## Test coverage map

- Defaults unchanged: all seven existing modes (default, actions, restart, entity, probe, native-step, live loop) keep their exact required lists even when the peer advertises every per-kind name; positional construction of the eleven existing fields is unchanged.
- Valid requests: each of the seven kinds alone; a two-kind non-canonical order subset requiring only those names; all seven kinds.
- Old or partial peers: nothing advertised, transport without kinds, kind without transport, each of the seven kinds missing in turn, `_v2`/prefix/aggregate/other-kind lookalikes, and a reconnect whose next handshake omits a previously offered kind. All fail before any snapshot.
- Local rejection: empty, list, set, frozenset and string inputs; unknown, wrong-case, capability-name, `None`, integer, nested, list and `str`-subclass entries; duplicates including an eight-entry request; every mode without native-step mode; native-step mode combined with each other opt-in.
- Boundary: 16-entry acceptance with all seven kinds and the native transport name, and 17-entry rejection.

## Real game

Not run. No runtime authority was used or implied.

## Limitations and continuation

- Negotiation proves only that a peer offers the names. It does not establish producer coverage, event identity, delivery, a transaction barrier or runtime eligibility; the export eligibility gate in design.md is unchanged and no kind is eligible.
- The "eight other advertised names" are derived from Python constants (`CAPABILITIES`, `LIVE_LOOP_CAPABILITIES`, `oracle_probe_v1`) and confirmed by a quoted-name presence check against mod/observer/main.lua. The test cannot detect a ninth Lua name being added later; that would be caught only when a real producer exceeds 16 entries.
- No CLI flag exposes the option, and no consumer uses `native_oracle_kinds` yet. Python does not record the negotiated kind set with the session or recording; the contract requires that in a later slice.
- The 1703-test run used the macOS JSON shim and is not a replacement for the Windows `Check.ps1` gate.
- Self-review against the diff: no unrelated changes, `ObserverConfig` positional order preserved, existing mode lists unchanged. The primary review and Windows acceptance checks passed; runtime export remains unaccepted.
- Next action: tasks 3.6 (Lua capability and event export) and 3.8 (native transaction multiplexing) stay open until the runtime gates in design.md are satisfied.
