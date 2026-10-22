# Evidence: native oracle API audit

- Date/time and timezone: 2026-10-17, Europe/Amsterdam.
- Git revision and dirty status: based on 22360fb; solo continuation and outbox changes uncommitted during audit.
- Scope: distinguish native callback facts from the existing OracleEvent semantics; no event emitter deployment.
- Game/mod/bridge: installed J460 enum source; observer 0.4.1-dev unchanged by this work.
- Python/package versions: Python 3.12.14; no package/configuration changes required for source inspection.
- Scenario/budget: local enum inspection and bounded primary documentation review; no game run.

## Sources and findings

Installed resources/scripts/enums.lua SHA256:
9737fc06f15ea26f397f8abe4ade01af105bdae1bec54b7ffbeacedd549dadb0.
Local lines 26/35/47/49/88/90 establish callback numbers 11/16/27/29/68/70.
Names in a shipped enum establish availability of identifiers, not runtime order.

The following callback facts come from the community-maintained API reference,
read 2026-10-17. They are primary API documentation, not a J460 runtime probe.

| Existing event | Documented candidate fact | Engineering assessment |
|---|---|---|
| enemy_spawned | NPC init also occurs on Delirium morph; early attributes may be incomplete. | Stable generation and initial HP still need verification. |
| enemy_damaged | Damage callback runs before application and supplies amount, flags, source and countdown. | Requested damage is not verified HP removed. |
| enemy_killed | Entity kill precedes death animation; NPC death follows it. Removal also includes unload. | Choose one verified identity/timing path; removal is insufficient. |
| player_damaged | Same pre-damage callback. | Actual half-heart loss and source classification remain unverified. |
| player_healed | No suitable heal callback established by this audit. | Net snapshot changes cannot attribute healing and damage separately. |
| room_cleared | Clean-award callback covers clearable rooms even without rewards. | Candidate signal only; never infer clear from an empty entity list. |
| player_died | Game-end boolean distinguishes death/game over from winning ending. | Extra-life timing and delivery before disconnect need probes. |

Source: [ModCallbacks reference](https://wofsauge.github.io/IsaacDocs/rep/enums/ModCallbacks.html).
An observer must return nil from damage and clean-award callbacks: non-nil may
suppress later callbacks; true in clean-award can suppress completion marks and
endings. The observer must not modify callback arguments or outcomes.

[Room.IsClear](https://wofsauge.github.io/IsaacDocs/rep/Room.html#isclear) exposes
a boolean. Any use of its transitions still requires native timing evidence.

## Decisions from this audit

These are engineering conclusions, not further claims about undocumented APIs:

- Do not translate attempted damage directly into realized damage. Cancellation,
  clamping or multiple effects can invalidate that interpretation; a net health
  delta alone cannot recover separate simultaneous damage and healing.
- Do not fabricate existing required amount/source fields when their meaning is
  unavailable. A later capability must negotiate supported semantics or remain
  unsupported. The current observer emits none of these native oracle envelopes.
- Do not credit a morph as a fresh reward-bearing spawn or unloading as a kill.
- Terminal event delivery with a shortened step needs an explicit contract:
  the existing receipt reader currently rejects non-completed steps. A death
  signal alone does not resolve this boundary.
- Capture after an explicit attach baseline, including neutral time before the
  first command. A bounded outbox may preserve these facts and enforce delivery
  ordering, but cannot establish when engine callbacks have all completed.

## Results

| Check/requirement | Command/scenario | Exit code | Status | Evidence |
|---|---|---|---|---|
| Shipped identifiers | Get-FileHash resources/scripts/enums.lua; rg callback names | 0 | passed | Hash and line numbers above |
| Semantic audit | Read linked API reference sections | N/A | passed | Candidate matrix and explicit unsupported semantics |
| Runtime oracle export | Native callback/outcome probe | N/A | not_run | No emitter or combined capability installed |

## Real game

No game launch, input, save selection, deployment or reset occurred. The earlier
callback trace is separate evidence; it does not verify oracle outcomes. Current
instance identity was not inspected because this work is offline.

## RL evaluation

Not applicable; no training or outcome/reward evaluation.

## Limitations and continuation

Keep episode-lifecycle open (12/19 whole tasks accepted). Next: offline producer
bookkeeping and end-to-end delivery tests, followed by a reviewed passive probe
design for actual damage/kill/clear/death ordering. Live outcome semantics,
exact input application, training isolation, start/reset authority and 100 real
episodes remain unfinished. Self-review checked that enum presence and reference
documentation were not presented as installed-game behavioral acceptance.
