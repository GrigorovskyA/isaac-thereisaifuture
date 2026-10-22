# Evidence: passive oracle probe during manual combat

- Date/time and timezone: 2026-10-18, Europe/Amsterdam.
- Git revision: 3b00630; implementation unchanged during the run; unrelated errors.txt preserved.
- Scope: raw native callback ordering during normal manual combat; no accepted OracleEvent or native step.
- Game/mod: manually launched J460, PID 27468; reviewed observer 0.4.2-dev diagnostic hash verified before attach, no action approval.
- Python/packages: existing CPython 3.12.14, unchanged dependencies.
- Configuration/budget: read-only EntitySnapshot negotiation; accept 8 s, handshake/message 3 s; one client, zero reconnects, at most 600 samples and 120 s from client start. One in-progress receive remains bounded to 3 s.

## Results

| Check/requirement | Command/scenario | Exit code | Status | Evidence |
|---|---|---|---|---|
| Real read-only entity capture | ObservationClient(ObserverConfig(accept_timeout=8, handshake_timeout=3, message_timeout=3, entity_observations=True)); accept/receive/context close | 0 | passed | 592 validated snapshots in 120.094 s; 562 active, 30 paused |
| Diagnostic record bound | Filter this session; compare IDs and line lengths | 0 | passed | IDs 1..1024 contiguous; maximum 268 bytes; final stop reason=count |
| Combat callback occurrence/order | Manual play, local-label groups and ordered raw records | 0 | passed | Counts and narrow observed sequences below, not universal semantics |
| Damage realization/attribution | Compare attempted amount with later samples | N/A | not_run | Existing NPC-update sample is insufficient; concrete counterexample below |
| Player death/revival/floor transitions | Natural scenarios within diagnostic window | N/A | not_run | No game_end/game_started/new_level; all 515 dead samples false |
| Default-off cleanup | Normal operator exit, process absence, restore two source files and compare hashes | 0 | passed | Both hashes match source; no approval exists |
| Launcher cleanup | Start-Isaac.cmd --preflight-only | 0 | passed | No game launch or guard relaxation |
| Strict project validation | ./scripts/OpenSpec.ps1 validate --all --strict | 0 | passed | 24/24 items; no implementation changes or new test run |

## Real game

The operator manually selected the run and confirmed combat readiness before
attach. Session f3ca899a282a4b12a72969ae34f30de4, epoch 1. Automatic save-slot
attestation/isolation remains unavailable; no training/reset authority was used.
Only read-only hello and state reads were sent. Movement, shooting and progression
were manual; the agent never launched/stopped/reset the game or supplied input.

The 592 entity snapshots covered frames 413181..416563, room visits 5..25 (21
visits), 558 unique player positions and 13 raw health states. All four visible
kinds appeared: across repeated frame observations, enemy 797, projectile 225,
pickup 373, obstacle 7104. These are appearances, not distinct actors or outcomes.
Every entity frame reported source overflow; the maximum was 27 entities/frame.
This remains a bounded visible subset, not complete world/outcome coverage.

### Bounded diagnostic window

Diagnostics ended at the 1024-record count limit after 71629 ms, while ordinary
read-only snapshots continued to the requested two-minute endpoint. No budget
was extended or renewed. First/last contexts:

- Record 1: frame 413181, update 640, room 5, attach.
- Record 1024: frame 415226, update 2684, room 16, stop reason=count.

| Raw record label | Count |
|---|---:|
| attach | 1 |
| post_update | 515 |
| damage_attempt | 153 |
| npc_update_hp | 185 |
| entity_kill | 33 |
| entity_remove | 41 |
| npc_death | 33 |
| clean_award | 7 |
| npc_init | 44 |
| new_room | 11 |
| stop | 1 |

Seven damage_attempt records targeted entity type 1. No applied player-damage or
healing amount/source is inferred from these attempts or raw health changes.

### Observed HP timing counterexample

Room 5, diagnostic label 1, entity type 26 (numeric values rounded here):

| ID | Callback fact | Frame/update | Current raw HP | Requested damage |
|---|---|---|---:|---:|
| 3 | damage_attempt | 413183 / 641 | 3.128148 | 5.191339 |
| 5 | npc_update_hp | 413184 / 642 | 3.128148 | N/A |
| 6 | entity_kill | 413184 / 642 | -2.063191 | N/A |
| 8 | entity_remove | 413185 / 643 | -2.063191 | N/A |
| 9 | npc_death | 413185 / 643 | -2.063191 | N/A |

Thus the next observed NPC-update callback still exposed the previous HP before
a later callback exposed a different value. It cannot be used as a generic
post-damage barrier or an applied-damage amount. Raw HP may be negative during
death; it cannot be copied into the existing nonnegative entity-HP field.
This observation does not establish whether every requested hit applies, how
simultaneous effects are attributed, or the correct clamping/reward semantics.

All 33 matched local-label kill groups in this window had raw order
entity_kill -> entity_remove -> npc_death. Eight other entity_remove records
were not paired with an entity_kill in those groups. Removal alone is not a kill.
Labels are diagnostic and room-local, not verified spawn generations or proof
that all lifecycle events were captured. Do not generalize the observed order to
all entities, animations, game versions or callback priorities.

Each of seven clean_award candidates was followed by a post_update reading
clear=true. Example: ID 36 at frame 413227/update 685; ID 37 at the same frame,
update 686, reads clear=true. These are corroborated raw facts for this run,
not a complete accepted room-clear event contract or achievement evidence.

## Cleanup and private data

The operator confirmed normal exit. No Isaac process remained before restoring
only main.lua/metadata.xml. Source/installed hashes:

- main.lua: c20f8164b0b621510011139baa86bc429872c94bc8fb2db25a4c46073e54b2a3.
- metadata.xml: 05a108ceb4149fb80c55a2b32e21a47c4f186b61092dee7c2a9d5b37ab449262.

Both oracle_probe and callback_trace are false; no action approval exists.
Launcher preflight passed. Private deployment backups were retained. No saves,
Cloud, other mods, options or executable files changed. Original action/restart
limits and manual startup/selection remain unchanged.

Ignored evidence (never committed): reports/local/oracle-combat-20261018-27468.jsonl,
oracle-combat-diagnostic-20261018-27468.log, oracle-combat-diagnostic-summary-20261018-27468.json
and oracle-combat-summary-20261018-27468.json, all under reports/local/.
Only bounded current-session diagnostic lines were extracted from the game log.

## RL evaluation

Not applicable. No model, training, reward, terminal transition or achievement claim.

## Limitations, self-review and continuation

Item 05 remains 12/19; do not mark task 4.1 complete: death, revival and floor
transition ordering were not encountered. Native completion/application and
attach/event delivery barriers remain unresolved. The count-limited diagnostic
covered less than the full capture; later snapshots do not fill that event gap.

Self-review separates attempts, raw samples and realized outcomes, checks the
counterexample against ordered record IDs, and preserves negative raw HP only
as diagnostics. No event model, reader rule or runtime budget was weakened.
Implementation code remains unchanged from the 894-test offline gate; strict
project validation is rerun for these evidence/design updates.

Next: specify a bounded end-of-update HP observation experiment before implementing
damage realization. Preserve explicit unknowns for cancellation, concurrent
damage/healing, death clamps and attribution. NPC-update must not seal a damage
event. A later observation-only death/revival/floor probe still needs naturally
available scenarios; never force death/reset or call incomplete steps successful.
