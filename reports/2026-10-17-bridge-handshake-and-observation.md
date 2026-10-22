# Evidence: bridge-handshake-and-observation

- Date/time/timezone: 2026-10-17, Europe/Amsterdam (CEST, UTC+02:00).
- Starting Git revision: 6028415dada2d46ab4f0e1a3566a1f9c0453ae8a, clean.
  Local implementation/docs/OpenSpec dirty during validation. Final revision is
  the commit containing this report; no game artifacts are included in it.
- Scope/acceptance: item 02; proposal criteria 1–2 are offline implementation/
  verification; criteria 3–4 require real observations/soak. Do not archive early.
- Game/mod versions: last audit identified Repentance+ v1.9.7.17.J460 /
  Steam build 22878971; current manifest/log still match. Observer 0.1.0 is
  project-local only. No real observer handshake or session exists.
- Python/packages: Python 3.12.14; existing production dependencies and locks
  unchanged. Test-only Lupa 2.6 installed to isolated scratch path with --no-deps;
  explicitly selected lua53, not its default runtime.
- Configuration: protocol/schema 1; loopback:9528; defaults 10/3/3 second
  accept/handshake/message timeouts; Lua 16 KiB messages, 4 KiB I/O/callback,
  5 samples/second maximum. Source hashes in OBSERVATION_PROTOCOL.
- Scenario/split/seeds/budget: offline simulated peers and fake Isaac state only;
  no train/validation/test split, game seed, episode, checkpoint or RL budget.
  No game installation, activation, launch-option, save or Cloud changes.

## Results

All commands run from repository root. Sanitized placeholders denote local
scratch and game roots, not literal reusable paths. No private log/save copied.

| Check/requirement | Command/scenario | Exit code | Status | Evidence |
|---|---|---|---|---|
| Prerequisite refresh | Read appmanifest_250900.acf, fresh-version log header, bundled socket directory and game LuaDocs/enums | 0 | passed | Bundled socket/core.dll present; reference methods and callbacks present, including unload. Loading remains unknown |
| OpenSpec planning | OpenSpec.ps1 new change bridge-handshake-and-observation; instructions proposal/specs/design/tasks/apply | 0 | passed | Proposal, new capability delta, design and 7 tracked tasks |
| Isolated Lua tooling | python -m pip install --target "<scratch>/lua-test-runtime" lupa==2.6 --no-deps | 0 | passed | Separate test-only lua53 runtime; production environment/locks unchanged |
| Direct game Lua DLL experiment | ctypes.CDLL("<Game>/Lua5.3.3f.dll") in 64-bit Python | 1 | failed | WinError 193 architecture mismatch; not a game/mod test. Replaced only test harness runtime with isolated Lupa, not game transport |
| Targeted tests | python -m pytest tests/test_observer.py tests/test_lua_observer.py -q with test-tool PYTHONPATH and ISAAC_JSON_LUA | 0 | passed | Simulated Python TCP peers and Lua 5.3 stubs; full final suite includes all targeted cases |
| Full offline gates | .\scripts\Check.ps1 with isolated Lua prerequisites | 0 | passed | Ruff, format, strict mypy, 63 tests (45 Python bridge, 16 Lua, 2 diagnostics), pip check, 3 specs + active change strict validation; no skipped tests |
| Change strict validation | .\scripts\OpenSpec.ps1 validate bridge-handshake-and-observation --strict | 0 | passed | Active change structurally valid |
| Negative CLI smoke | python -m isaac_threrisaifuture.cli observe --port 0 --accept-timeout 0.05 --samples 1 | 2 expected | passed | Prints loopback listening record, then explicit no-peer timeout and exits; no game peer used |
| Diff/self-review | git diff --check; inspect source, docs, spec and tests; staged privacy review | 0 | passed | Review below; no control/reset/console endpoint or private artifacts |
| Profile/deployment verification | Approved profile/write set, observer activation and optional --luadebug | N/A | blocked | No verified isolated profile or specific artifact deployment/launch authorization |
| Real handshake/state correlation | Actual game peer; user manual movement and health/room comparison | N/A | blocked | Observer not installed; no real session/frame evidence |
| Ten-minute soak/responsiveness | Observe memory/response; disconnect/reconnect and Python shutdown | N/A | not_run | Requires authorized real peer; offline timeouts do not verify game hangs/memory |
| RL evaluation/smoke | Training/evaluation/Smoke-RL.ps1 | N/A | not_run | No RL or production dependency change; outside item 02 |

Initial tests exposed a Windows simulated-peer ConnectionAbortedError during
intentional closure and a test decoder trying to parse a final incomplete Lua
output fragment. Corrected expected Windows teardown handling and made the harness
consume complete LF records only; no production checks were weakened.
Self-review also fixed Lua/XML checkout line endings to LF in .gitattributes
so approved artifact hashes remain reproducible on Windows.

## Offline behavior covered

- Valid handshake, fragmented and combined TCP data, schema/field/type/version
  errors, duplicate JSON keys, missing capabilities and finite number bounds.
- Oversized input, absent peer, stalled handshake, absolute trickle deadline,
  peer EOF, session mismatch and duplicate/regressing sequence/frame/epoch/
  update/visit counters. Equal engine frames are explicitly allowed.
- New session after reconnect; new frame origin after game epoch; paused and
  null unavailable state; real socket cleanup on KeyboardInterrupt; CLI reading
  a simulated peer and exiting after its sample budget.
- Actual Lua adapter source running in isolated Lua 5.3: partial output and input,
  absent/pending/refused server, missing module, malformed/oversized peer,
  handshake/output expiry, rejected post-hello bytes, unavailable/failing reads,
  raw health/position/pause/epoch, reconnect/session and unload/game-exit cleanup.

Lua tests use **fake Isaac and socket objects** plus the installed game's JSON
source. They do not load Isaac, its LuaSocket DLL, a mod runtime or a Steam profile.
Separate interpreter execution is not proof of game ABI/API compatibility.

## Real game

No real-game observer test took place. Session/episode/frame IDs: N/A.
No agent movement/shooting, reset, spawning or console-command endpoint exists.
Game/saves/Cloud/mod list/launch options were not changed. No backup/restoration
or write-isolation test was executed. Ordinary gameplay was not a test episode.

Protocol includes actual Lua runtime/mod data when executed, but game version/
Steam build default to null with explicit provenance. Operator-configured version
metadata requires manual verification; it must not masquerade as runtime detection.
Actual bundled socket loading, callbacks in menus/pause/loading, state correlation
and resource behavior remain unknown.

## Separate OpenSpec verification / self-review

One implementing agent performed a separate pass after implementation; this is
**self-review**, not independent review. Read all change artifacts and reviewed
Python/Lua code, tests, protocol/deployment docs and status/roadmap changes.

| Dimension | Result |
|---|---|
| Completeness | 5/7 local tasks complete; real acceptance 4.1 and 4.2 incomplete |
| Correctness | Local implementations/tests map to requirements 1–4; requirement 5's blocked-evidence behavior is followed, real integration is not verified |
| Coherence | Same audited transport; no REPENTOGON/second transport, control, hidden maps, rewards or RL; current spec delta stays active |
| Pattern consistency | Typed src package, existing Pydantic/stdlib, existing CLI and pytest conventions; no production dependency/lock changes |

Requirement mapping:

1. Negotiated loopback connection: observer_client accept, strict wire models,
   Lua canonical hello; version/capability and simulated CLI tests.
2. Bounded responsive transport: absolute Python deadlines, bounded framing,
   Lua one-read/one-send pump and fixed queues; fragmentation/trickle/slow-reader
   tests. **Actual game callback responsiveness not verified.**
3. Explicit observations: Snapshot availability validator, Lua pcall capture,
   raw health/character fields and protocol units; paused/unavailable/state tests.
   **Actual coordinates/health/room correspondence not verified.**
4. Ordered sessions/cleanup: consumer history checks, explicit accept/close,
   Lua lifecycle callbacks; stale/session/epoch/interrupt/reconnect/unload tests.
   **Actual game disconnect/shutdown behavior not verified.**
5. Honest integration evidence: runtime tasks remain unchecked and STATUS/roadmap
   say item 02 is incomplete. No archival or safe-actions work performed.

Two critical integration blockers remain: complete task 4.1 (approved profile/
deployment + actual correlated state) and task 4.2 (ten-minute real soak/
responsiveness). No additional local code warnings or suggestions found.
The tests that ran passed. Real-game correctness/scenario checks above were
not verified because deployment/profile authorization is missing. **Not ready
for archival as verified integration.**

## RL evaluation

Not applicable; no agent or learning result.

## Limitations and continuation

Review [exact artifact hashes and deployment/rollback](../docs/OBSERVATION_PROTOCOL.md).
Next action is profile/isolation and deployment authorization, then a module probe
and user-manual state correlation/soak. The installation destination is the approved
instance's mods/isaac_threrisaifuture_observer, containing only main.lua and
metadata.xml; --luadebug may be needed. Save/Cloud changes need their own explicit
profile plan and authorization.

Completed project work can be committed/pushed while the change remains active.
Exclude local test tooling, personal paths/config, saves, private logs and caches.
Do not proceed to bridge-safe-actions in this task.
