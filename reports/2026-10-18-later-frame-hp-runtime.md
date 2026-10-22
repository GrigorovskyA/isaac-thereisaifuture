# Evidence: later-frame HP diagnostic during manual combat

- Date/time and timezone: 2026-10-18 12:22:02.892-12:24:03.002 Europe/Amsterdam (10:22-10:24 UTC).
- Git revision and dirty status: 6f27864; only unrelated untracked errors.txt before capture, preserved and excluded.
- Scope: verify deployed 0.4.5-dev later-frame raw HP sampling, bounded observation and explicit unavailable facts. No applied-damage, reward or native-step acceptance.
- Game/mod/bridge: existing Repentance+ J460 installation; live handshake observer 0.4.5-dev, Lua 5.3, extender_present=false; game version/build unavailable in handshake.
- Python/packages: existing CPython 3.12 environment; no dependency/lock changes. Installed/source hashes match the reviewed deployment report.
- Configuration: ObserverConfig(accept_timeout=8, handshake_timeout=3, message_timeout=3, entity_observations=True, oracle_probe=True); control/restart/native-step modes disabled.
- Scenario/budget: user manually prepared combat on requested file 2; one attach, zero reconnects, at most 600 snapshots / 120 seconds including accept, receive timeout 3 seconds; unchanged nonrenewable Lua limits.

## Results

| Check/requirement | Command/scenario | Exit code | Status | Evidence |
|---|---|---|---|---|
| Instance/profile preflight | Parse tasklist CSV, installed hash/approval guards; fresh game log | 0 | passed | Exactly one Isaac PID 7224; source-matching 0.4.5-dev; no approval; log Continue, 2 |
| Negotiated attach | ObservationClient.accept() with configuration above | 0 | passed | Session 8f63e395b8664e81be1c1824cad7ddd8 acknowledged oracle_probe_v1 |
| Bounded read | Context-managed receive loop, no reconnect | 0 | passed | 593 snapshots in 120.125 s; 506 active, 87 paused; one final receive overran 120 s by 0.125 s within configured bound |
| Later distinct-frame samples | Compare queued context, sample index and prior_frame | 0 | passed | 99 first and 197 later records; no sampled later record failed strict frame advancement |
| Raw changed HP | Group by session/epoch/room/label/queued frame/update | 0 | passed | 87 of 99 diagnostic windows had a numeric later HP differing from first; 12 did not |
| Removed targets | status=removed records | 0 | passed | 16 records; none contained HP; no zero substitution |
| Global record/line bounds | Current-session extraction capped at 2 MiB; validate IDs and byte lengths | 0 | passed | IDs 1..1024 contiguous; reason=count at 57.825 s; longest diagnostic line 302 bytes |
| Floor callback slice | Manual progression, raw callback context | N/A | passed | One new_level between new_room and subsequent post_update; no old queued-frame HP record observed after boundary |
| Death/revival, same-frame expiry, missing/identity change and overflow | Scenarios absent from diagnostic window | N/A | not_run | No forced scenarios; no diagnostic dead=true; offline coverage remains separate |
| Cleanup/file integrity | Context exit, port readback, installed/source hash comparison | 0 | passed | No live 9528 listener/connection; only TIME_WAIT; unchanged source/installed hashes and no approval |
| Final strict validation | ./scripts/OpenSpec.ps1 validate --all --strict | 0 | passed | 24/24 after evidence updates |

## Real game

This was ordinary-profile manual play, not an isolated training episode. The
user confirmed readiness after instructions to select file 2; the fresh game log
also recorded Continue, 2. This corroborates the slot but does not implement
automatic attestation or training isolation. The agent sent no movement, shooting,
restart, reset or other gameplay command and did not launch or stop the game.

Snapshots: session 8f63e395b8664e81be1c1824cad7ddd8, epoch 1,
sequences 1..593, frames 90701..93751, updates 462..3512, room visits 1..20.
All four native entity kinds appeared. All 593 entity frames reported source
overflow, so entity coverage remains a bounded subset rather than a full census.

Diagnostic counts: attach 1, post_update 427, npc_init 22, npc_update_hp 111,
new_room 8, damage_attempt 97, post_update_hp 99, post_update_hp_later 197,
entity_kill 19, entity_remove 19, npc_death 19, clean_award 3, new_level 1, stop 1.
Of 296 first/later records, 280 were sampled and 16 removed. Nineteen numeric
samples had negative raw HP. No missing, identity_changed or expiry fact occurred.
The maximum coalesced attempt count was two. Ninety-eight windows had three
records; one had two when the global budget stopped further output. An unavailable
third record is not a third HP read. No window exceeded three opportunities.

### Measured phase example

Room 2, local diagnostic label 3, entity type 237 variant 1:

| Record | Callback/sample | Frame/update | Raw HP |
|---|---|---|---|
| 34 | damage_attempt; requested=2 | 90860 / 620 | 60 |
| 35 | first post_update_hp | 90860 / 621 | 60 |
| 37 | npc_update_hp | 90861 / 621 | 60 |
| 38 | post_update_hp_later, sample=2 | 90861 / 622 | 58 |
| 40 | post_update_hp_later, sample=3 | 90862 / 623 | 58 |

This verifies a later raw value after both earlier callbacks showed old HP. It
does not establish universal settlement, per-hit causality or source attribution.
Labels are diagnostic correlations, not verified engine spawn generations.

Removed example: record 274, room 2, label 5, frame 91066/update 827,
sample=3, prior_frame=91065, queued_frame=91064, status=removed with no HP.

Floor slice: new_room record 460 then new_level record 461, both at
frame 91329/update 1090, followed by post_update record 462 at 91330/1091.
No later HP record after that boundary carried queued_frame below 91329. This is
partial room/floor timing evidence, not proof of all transition or pending-target
cleanup cases; death and revival remain absent from this diagnostic window.

The diagnostic stop occurred at time_ms=59139211, 57825 ms after attach; normal
observation continued to the full capture deadline. Context exit closed the socket
and listener. No reconnect was attempted and the exhausted diagnostic budget was
not renewed. No file copying/restoration is needed after negotiated diagnostics.

Ignored private evidence: reports/local/later-frame-hp-runtime-20261018T102202Z-7224.jsonl,
later-frame-hp-20261018-7224-diagnostic.log and later-frame-hp-20261018-7224-summary.json.
Raw snapshots, game logs, saves and backups are not committed.

Post-capture installed/source SHA256:

- main.lua: 10596bb33a8a98c6d0e616700b931b35ec7aca44bb7c5b5cae094ec43ebb7323.
- metadata.xml: cfd4aa96a12d77d1104b69a2fef273f4b8f9a4b0f26b7a6823a0adf274016e65.

## RL evaluation

Not applicable. No reward, model, training, progression or achievement claim.

## Limitations, self-review and continuation

Self-review compared record IDs, grouping context, first/later sample indexes,
frame advancement, explicit unavailable facts, truncation, wire status, file hashes
and transport cleanup against the accepted bounded diagnostic design. New runtime
evidence supports this diagnostic slice only. The prior 983-test Windows gate
remains applicable; source did not change, so it was not repeated for this capture.

Original task acceptance remains 12/19 plus accepted offline subtask 4.4 (current
checklist 13/20). Task 4.1 is still incomplete because death/revival and broader
transition cases are missing. Native steps, completion/event barriers, a real
GameBackend and isolated start/reset remain unfinished. No archive.

Next offline work: define conservative frame/event ordering and terminal/partial-
step semantics using the measured callback phases, without treating a fixed later
sample count as a universal barrier. Missing lifecycle scenarios require separately
prepared operator-directed observation, never forced death, resets or repeated
attaches to renew this mod load's budget.
