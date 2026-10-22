# Evidence: oracle-event-contract-review-20261019-01-f2 (feedback 2)

- Date/time and timezone: 2026-10-19, Europe/Amsterdam.
- Git revision and dirty status: baseline `ae18e03` (HEAD). Pre-existing uncommitted
  edits to `AGENTS.md`, `docs/AGENT_WORKFLOW.md`, `subagent.md`, `subagent_report.md`,
  `reports/2026-10-19-oracle-probe-live-runtime.md` and untracked `errors.txt`,
  `scripts/Wait-Change.ps1`, `scripts/wait-change.sh` were preserved untouched.
- Change scope and acceptance criteria: offline design/evidence review for episode-lifecycle
  task 3.6. Decide aggregate versus per-kind OracleEvent capability negotiation, fail-closed
  rules and per-kind export eligibility. No Lua, Python, wire, reward, test or training change.
- Game/mod/bridge versions: not applicable; no game access. The only runtime input is the
  committed `reports/2026-10-19-oracle-probe-live-runtime.md` at `ae18e03` (observer
  0.5.0-dev, protocol/schema 1, as recorded there).
- Python/package versions and configuration hash: not applicable; no Python executed.
  Validation used Node with the pinned OpenSpec 1.14.3.
- Scenario, split, seeds, budget, and stop conditions: source/spec/report reading only.

Runtime-input note: the worktree copy of the live-runtime report carries an uncommitted
two-line wording edit (scenario and movement-attribution wording). This review used the
committed text (`git show HEAD:reports/2026-10-19-oracle-probe-live-runtime.md`); none of
the facts used below differ between the two. No `reports/local`, game log, `errors.txt`,
save, model or other private runtime file was opened.

## 1. Existing OracleEvent contract (production types and specs)

Source: `src/isaac_threrisaifuture/entities.py` (`OracleKind`, `OracleEvent`).

Common required fields: `type="oracle_event"`, `observation_schema_version=1`,
`provenance` (`synthetic` | `game_api`), `session_id`, `game_epoch`, `room_visit`,
`frame_id`, `kind`. Optional payload: `entity_id` + `spawn_generation` (both or neither),
`amount` (0..1e6, never negative), `damage_source` (`enemy` | `self` | `environment`).

| Kind | Required payload (validator) | Current production producers | Current consumers |
|---|---|---|---|
| `enemy_spawned` | entity_id, spawn_generation, amount | sim (synthetic); live `EventDeriver` (amount = max_hp, generation 0) | `RewardFunction` initial HP; episode summary count |
| `enemy_damaged` | entity_id, spawn_generation, amount | sim; `EventDeriver` (HP delta; vanished enemy's remaining HP) | reward (ignored without known initial HP); summary HP removed |
| `enemy_killed` | entity_id, spawn_generation | sim; `EventDeriver` (enemy vanished with complete coverage) | reward kill term; summary count |
| `player_damaged` | amount, damage_source | sim; `EventDeriver` (all HP loss attributed to `enemy`) | reward (enemy source only); summary damage taken |
| `player_healed` | amount | `EventDeriver` only (net HP gain); sim emits none | none in reward/summary |
| `room_cleared` | none | sim; `EventDeriver` (oracle room_clear rising edge) | `EpisodeController` outcome `cleared`; reward first-clear term |
| `player_died` | none | sim; `EventDeriver` (oracle player_dead rising edge) | `EpisodeController` outcome `death` (wins a same-interval tie); reward death term |

Native transport (no producer exists): `native_events.py` `NativeOracleEvent` adds
`type="native_oracle_event"`, `protocol_version=1`, envelope session/epoch/room/frame and
`event_id` (1..2^53-1); requires `event.provenance == "game_api"` and exact identity
agreement. `NativeEventCursor` keeps one session/epoch, suppresses IDs <= last, faults on gaps
and on frames outside `(start, end]`. `native_receipts.py` accepts events only after the ack,
requires the command's session/epoch/room_visit, yields receipts only for `completed` steps
and checks the completion watermark (`validate_event_barrier`). `recording.py` keeps
`native_oracle_events` a separate stream. Specs: episode-lifecycle delta spec requirements
"Separated native outcome events" and "Explicit native event completion barrier";
`openspec/specs/observation-encoding/spec.md` "Oracle separation".

Handshake: `observation.py` `CAPABILITIES = (snapshot_v1, availability, raw_health_v1)`;
`observer_client.py` adds exact mode names (`death_restart_v1`, `safe_actions_v1`,
`entity_observation_v1`, `entity_action_v1`, `oracle_probe_v1`, live-loop set) and requires
`set(required) <= set(ack.capabilities)`. `HelloAck.capabilities` is capped at 16 entries.
Read-only inspection of `mod/observer/main.lua` shows at most eight names advertised today
(four base, `entity_observation_v1`, `oracle_probe_v1`, `safe_actions_v1`, `live_loop_v1`),
no `entity_action_v1` and no oracle-kind name; unsupported or duplicate required names fail.

Findings relevant to negotiation (observations, no change made):

- F1 `episodes.py` `_outcome` treats absence of `player_died`/`room_cleared` as "not
  terminal" and then reports `timeout`; `EpisodeSummary` defaults `died=False`,
  `room_cleared=False` and zero counts. With incomplete kind coverage these become false
  negatives, not unknowns.
- F2 The approved live-loop `EventDeriver` (`live.py`) emits approximate events labelled
  `provenance="game_api"` with `spawn_generation=0`. The `OracleEvent` record alone cannot
  distinguish them from a future native callback producer; separation depends on the
  `NativeOracleEvent` envelope and `native_oracle_events` stream. They must never be merged.
- F3 `rewards.py` ignores `enemy_damaged` without a prior `enemy_spawned` initial HP for the
  same `(entity_id, spawn_generation)`; enemy kinds are consumer-linked.
- F4 `OracleEvent.amount` is non-negative, while the probe recorded negative raw HP at a kill;
  any damage amount needs an explicit overkill/clamping rule rather than raw deltas.
- F5 Receipt context requires the command's `room_visit` and only completed steps yield
  receipts, so a death or transition inside a short step cannot be delivered yet (already
  recorded as the design's terminal/short-step decision).

## 2. Committed runtime evidence used

From the committed `reports/2026-10-19-oracle-probe-live-runtime.md`:

- Results, "Candidate callback coverage" (status partial): damage_attempt 72, npc_update_hp
  102, post_update_hp 68, post_update_hp_later 132, npc_init 35, entity_kill 19,
  entity_remove 28, npc_death 16, clean_award 3, new_room 9; room visits 1..10.
- Results, "Bounded diagnostic output": 1024 contiguous records, stopped with reason=count
  after 109861 ms; the window cannot be renewed in that mod load ("Limitations").
- Results, "Player terminal/floor/exit scenarios" (not_run): game_end, pre_game_exit,
  pre_mod_unload and new_level not observed; player death/revival untested.
- Results, "Export eligibility" (not_run): no stable spawn identity, universal ordering,
  clear/reward semantics, delivery or completion barrier; no OracleEvent emitted.
- "Real game": frame 7847, label 1 (type 217, HP 4.0), damage_attempt requested 3.5; first
  post_update_hp in that frame 4.0; next-frame NPC-update 4.0; a later-frame sample 0.5.
  Separate sequence: entity_kill at 7882 with HP -3.0, then entity_remove and npc_death at
  7883. Labels are local diagnostic labels, not spawn generations. Clean-award and new-room
  records do not prove clear or reward.

The report does not split damage_attempt by player versus NPC target and does not enumerate
player health samples, so neither is used as player evidence here. The 4.0 - 3.5 = 0.5
numeric match is one observation across frames with possible coalescing; the report does not
attribute it and neither does this review.

## 3. Per-kind matrix

| Oracle kind | Candidate callback source(s) | Committed probe observed | Still unverified | Evidence needed before export | Export now |
|---|---|---|---|---|---|
| `enemy_spawned` | `MC_POST_NPC_INIT` | npc_init 35 with local labels | Stable spawn generation (morph/re-init relabel), enemy classification, initial HP completeness at init, attach-time baseline for pre-existing enemies, room re-entry | Bounded run with morph/split and re-entered rooms showing one identity per spawn matching `EntityFrame` identity, verified initial HP, explicit attach baseline rule | No |
| `enemy_damaged` | `MC_ENTITY_TAKE_DMG` plus later HP samples | 72 attempts; NPC-update/post-update/later samples; old HP persisted after an attempt, changed HP only later | Applied amount, cancellation, clamping/overkill (negative HP seen), coalesced/concurrent hits, enemy healing, settlement point inside a step | Defined realization rule and settlement point, per-hit or explicitly aggregated attribution, non-negative amount rule, identity linked to `enemy_spawned` | No |
| `enemy_killed` | `MC_POST_ENTITY_KILL` or `MC_POST_NPC_DEATH` | kill 19, NPC death 16, removal 28; one kill -> remove + NPC death across frames 7882/7883 | Which callback is authoritative, exactly-once per identity, timing across a step boundary, exclusion of removal-only (unload/room exit); counts are not one-to-one in this window | One chosen path with identity across kill/remove/death, room unload and morph; step-boundary placement rule | No |
| `player_damaged` | `MC_ENTITY_TAKE_DMG` on the player plus player samples | Not separately reported | Realized half-heart loss by heart type, blocked/invulnerable hits, source classification enemy/self/environment | Bounded scenarios for each source class with realized loss and attribution | No |
| `player_healed` | None established | Nothing | Any attributable source; net gain conflates healing, max-HP and pickups | A verified heal source distinct from damage and max-HP change | No (unsupported) |
| `room_cleared` | `MC_PRE_SPAWN_CLEAN_AWARD` (candidate), room clear flag transitions | clean_award 3 across 9 new_room records | Clear semantics per room class (boss, waves/ambush, pre-cleared, enemy-free), exactly-once per visit, ordering before transition | Per-class runs correlating award with verified clear and delivery; never an empty enemy list | No |
| `player_died` | `MC_POST_GAME_END` game-over flag; player dead fact | game_end not observed; death/revival untested | Extra-life revival (must not be terminal), victory versus death, delivery before disconnect/exit, short-step terminal envelope | Death with and without revival, delivery ahead of disconnect, terminal envelope contract | No |

Semantically distinct facts that must not be merged into an oracle kind:

| Fact | Committed observation | Is | Is not |
|---|---|---|---|
| damage_attempt | 72 | Pre-application request (amount/flags/countdown) | Applied damage, attribution or reward |
| Raw HP samples (npc_update_hp, post_update_hp, post_update_hp_later) | 102 / 68 / 132 | Raw readings at observer callback positions | Settlement, realized amount or barrier |
| NPC death (`npc_death`) | 16 | NPC death callback | Same event as kill or removal |
| Entity kill (`entity_kill`) | 19 | Kill callback, raw HP may be negative | Death animation end, removal, reward |
| Entity removal (`entity_remove`) | 28 | Object removal, including non-kill removal | A kill |
| clean_award | 3 | Award-spawn callback candidate | Proven room clear or reward |
| Room transition (`new_room`) | 9 (visits 1..10) | Context/room_visit change; by design it cancels a native step and clears probe pending references | Clear, death or oracle kind |
| Floor transition (`new_level`) | Not observed | Context change | Oracle kind |
| game_end | Not observed | Game-ended context with a boolean | Player death by itself |
| Player death/revival | Untested | Candidate terminal, revival non-terminal | Inferable from zero HP or disconnect |

## 4. Capability negotiation decision

Recommendation: per-kind negotiation; no aggregate all-kinds capability.

Rationale: no kind is currently eligible and `player_healed` has no candidate source, so an
aggregate name could never be advertised honestly. Consumers depend on different kinds
(outcomes need `player_died`/`room_cleared`; rewards need enemy kinds), and the existing
exact-name subset check already supports listing kinds without a wire shape change.

Contract (frozen in `openspec/changes/episode-lifecycle/design.md`, task 3.6 gate subsection):

- One exact versioned name per kind (working form `oracle_<kind>_v1`); semantic changes need a
  new version; no prefix or version fallback.
- Kind names are valid only with the exact existing native episode capability
  `entity_action_v1` (Python constant `NATIVE_EPISODE_CAPABILITY`), which owns envelope,
  cursor and barrier transport. It is the already-defined native-step transport gate; no
  additional aggregate all-kinds or transport-mode capability is introduced, and each of the
  seven `oracle_<kind>_v1` names is a new advertised per-kind capability entry. Any other
  combination (default, live loop, probe, actions, restart) fails negotiation, and a
  required kind without `entity_action_v1` in the same ack fails, which gives a future
  negotiation test an exact target.
- The producer advertises a kind only while its verified source and per-load resources are
  available. Python requires exactly the kinds its consumers use.
- HelloAck cap: the worst-case list is eight other currently advertised names +
  `entity_action_v1` + seven per-kind names = 16, exactly the existing 16-entry limit;
  implementation must stay within it and the limit must not be raised.

Fail-closed behavior:

| Producer state | Required behavior |
|---|---|
| Old (no kind names, e.g. 0.5.0-dev) | Any required kind fails the hello before snapshot/command; no fallback |
| Partial (subset advertised) | Hello fails if any required kind is missing; the consumer must not proceed with a reduced set |
| Exhausted before hello (required source/resource unavailable) | Omit the kind; a client requiring it fails the hello |
| Exhausted after `hello_ack` (per-load resource used) | The negotiated capability cannot be withdrawn from that ack: fault and close the active session/transaction (Python treats it as an infrastructure fault) and omit the kind from later handshakes; never keep the session running silently while events stop |
| Unsupported kind | Never advertised (currently all seven) |
| Envelope with a non-negotiated kind | Protocol fault, connection closed, no transition |

Missing kinds are not negative events:

- Absence means "none occurred" only for a negotiated kind, in a completed transaction whose
  watermark matched, inside that producer's coverage window (after the attach baseline,
  before exhaustion). Faulted, cancelled or expired steps yield no negative facts.
- For a non-negotiated kind, absence is unknown: no zero counts, `died=False`,
  `room_cleared=False`, reward terms or `timeout` claim (F1). A native backend lacking a
  terminal kind its scenario needs refuses to start.
- Consumers require identity-linked kinds together (F3) and receive the negotiated set with
  the session and any native recording.
- Never fill gaps with `EventDeriver` frame deltas (F2), diagnostic probe records,
  disconnects, zero health or empty enemy lists.

## 5. Export eligibility now

No `OracleEvent` kind is eligible for Lua export. The single committed probe does not
establish universal callback ordering, spawn identity, applied damage, room clear, reward,
terminal outcome, event delivery or a transaction barrier, and this review infers none of
them. Tasks 3.6 and 3.8 remain open and unchecked.

## Results

| Check/requirement | Command/scenario | Exit code | Status | Evidence |
|---|---|---:|---|---|
| Baseline identity | `git --no-pager log --oneline -3` | 0 | passed | HEAD `ae18e03` |
| Baseline strict validation (before edit) | `XDG_CONFIG_HOME="$PWD/.tooling" OPENSPEC_TELEMETRY=0 node "$HOME/.cache/isaac-openspec/node_modules/@fission-ai/openspec/bin/openspec.js" validate episode-lifecycle --strict` | 0 | passed | "Change 'episode-lifecycle' is valid" |
| Strict validation (after edit) | same command | 0 | passed | "Change 'episode-lifecycle' is valid" |
| All-items strict validation (after edit) | same CLI, `validate --all --strict` | 0 | passed | "Totals: 30 passed, 0 failed (30 items)" |
| Whitespace/conflict check | `git diff --check` | 0 | passed | No whitespace errors; only existing CRLF normalization warnings |
| New untracked report whitespace | `git --no-pager diff --no-index --check -- /dev/null reports/2026-10-19-oracle-event-contract-review.md` | 1 | passed | Exit 1 only signals that the files differ; no whitespace error was printed; LF-only, no tabs/CR, no trailing spaces |
| Design line endings preserved | Python CRLF/LF count on design.md | 0 | passed | CRLF file, zero lone LF after edit |
| Feedback 2 whitespace check | `git diff --check` | 0 | passed | No whitespace errors; only CRLF normalization warnings |
| Feedback 2 strict validation | same pinned OpenSpec 1.14.3 CLI command as above (`pwsh` unavailable on this Mac, so `./scripts/OpenSpec.ps1` was not run) | 0 | passed | "Change 'episode-lifecycle' is valid" |
| Feedback 2 line endings | Python CRLF/LF count on design.md; CR/tab count on this report | 0 | passed | design.md 857 CRLF of 857 lines (no lone LF); report has no CR or tab |
| Windows quality gate, default temp (coordinator) | `./scripts/Check.ps1` with default `%TEMP%` | 1 | failed | 1117 tests passed, 14 skipped; pytest session cleanup then raised `PermissionError [WinError 5]` resolving `%TEMP%\pytest-of-<user>\pytest-current`. Environmental temp-directory failure; this run did not pass |
| Windows quality gate, isolated temp (coordinator) | `./scripts/Check.ps1` with `TEMP` and `TMP` set to `C:\Users\<user>\AppData\Local\Temp\isaac-oracle-review-check-20261019-01` | 0 | passed | 1117 passed, 14 optional isolated-Lua tests skipped; Ruff, format, mypy, dependency check and embedded strict OpenSpec passed |
| Windows all-items strict validation (coordinator) | `./scripts/OpenSpec.ps1 validate --all --strict` | 0 | passed | 30/30 passed |
| Windows whitespace check (coordinator) | `git diff --check` | 0 | passed | No whitespace errors |
| Real game / Lua 5.3 runtime | Not run | N/A | not_run | No real game or Lua 5.3 runtime checks were run |
| Native event export | Runtime probe | N/A | not_run | No authority; no emitter added |

The Windows rows are results supplied by the Windows coordinator; they were not run on this
Mac, where `pwsh` is unavailable and the pinned cache CLI used by `scripts/check.sh` replaced
`./scripts/OpenSpec.ps1`. The 14 skipped tests are optional isolated-Lua tests, so no Lua
behavior is exercised by this evidence.

## Real game

No game launch, connection, input, deployment, save/Cloud access, approval or private-log
access occurred. Runtime facts come only from the committed live-runtime report.

## RL evaluation

Not applicable. No training, reward change or model evaluation.

## Limitations and continuation

Changed project files: `openspec/changes/episode-lifecycle/design.md` (task 3.6 gate
subsection only) and this report. The worker also prepended the f2 summary to
`subagent_report.md` and published matching `agent-status.json` states as required by the
handoff workflow. `tasks.md`, specs, code and tests were not edited.

Index note: while preparing the whitespace check, `git add -N` was briefly run on this
report (intent-to-add). It was immediately undone with
`git reset -q -- reports/2026-10-19-oracle-event-contract-review.md` (exit 0); `git diff
--cached` is empty and the report is untracked again. No commit, stash or other Git write.

Self-review: the matrix keeps attempts, raw samples, kill, removal, NPC death, clean award,
transitions, game end and death/revival distinct; every runtime claim cites the committed
report; no kind is marked eligible; no implementation task, wire field or checklist change
was added. `entity_action_v1` is the exact existing native-step transport gate and adds no
aggregate or transport-mode capability; the seven per-kind names are new advertised entries
and remain working names for task 3.6 implementation, and the worst-case list of 16 stays
within the existing `HelloAck` limit. HelloAck capacity enforcement and
consumer tri-state summaries remain future implementation concerns. Earlier runtime reports
cited by the design were not re-evaluated.

Next action: a separately authorized, bounded runtime scenario for one candidate kind (for
example enemy identity through kill/remove/death with morphing enemies), or offline
specification of the native-step terminal envelope that `player_died` requires.
