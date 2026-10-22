# Evidence: negotiated post-update HP diagnostic in manual combat

- Date/time and timezone: 2026-10-18, approximately 11:27-11:29, Europe/Amsterdam.
- Git revision and dirty status: 70ba4b3; only unrelated untracked errors.txt before capture, preserved and excluded.
- Scope: verify explicit oracle_probe_v1 activation and raw deferred HP observations; no applied-damage, step-completion or training acceptance.
- Game/mod/bridge: existing Repentance+ J460 installation; live handshake observer 0.4.4-dev, Lua 5.3, extender_present=false; game-version fields unavailable in handshake.
- Python/packages: existing CPython 3.12.14 environment; dependencies and locks unchanged.
- Configuration: ObserverConfig(accept_timeout=8, handshake_timeout=3, message_timeout=3, entity_observations=True, oracle_probe=True). All control modes disabled.
- Budget: one attach, zero reconnects, at most 600 snapshots / 120 seconds including accept; Lua nonrenewable 120000 ms / 1024 records / 128 labels / 16 pending targets / 400 bytes per line.

## Results

| Check/requirement | Command/scenario | Exit code | Status | Evidence |
|---|---|---|---|---|
| Launch and file identity | One previously requested launch, manual Steam confirmation and file-2 Continue | N/A | passed | User confirmed ready; live PID 12236; fresh registration and game log Continue, 2 |
| Explicit negotiated activation | ObservationClient with configuration above, accept() | 0 for handshake | passed | oracle_probe_v1 acknowledged; observer 0.4.4-dev; attach diagnostic in same session |
| Full two-minute observation | Bounded receive loop with context-manager cleanup | 1 | failed | 530 snapshots in 107.375 s; PeerDisconnected before a complete record; no retry |
| Deferred raw HP sampling | Manual combat; current-session log extraction capped at 2 MiB | 0 | passed | 106 post_update_hp records, all sampled; each update minus queued_update equals 1 |
| First post-update as applied-damage barrier | Compare same-room local-label callback facts | N/A | failed | All 103 damage-to-post pairs retained attempted-callback HP; 20 later kill records showed different HP |
| Diagnostic limit | Record IDs and stop fact | 0 | passed | Contiguous IDs 1..1024; reason=count after 91316 ms; maximum diagnostic line 284 bytes; max label 70 |
| File/authority cleanup | SHA256 readback and approval absence | 0 | passed | Installed/source hashes unchanged; no action_authorization.json; no file restoration needed |
| Full offline quality gate | ./scripts/Check.ps1 with environment from preparation report | 0 | passed | 945 passed, zero skips; Ruff, 84 formatted files, mypy 37 sources, pip consistency, strict OpenSpec 24/24 |
| Final strict validation | ./scripts/OpenSpec.ps1 validate --all --strict | 0 | passed | 24/24 after documentation self-review |

## Real game

The user approved the Steam custom-parameters dialog, selected file 2 and prepared
manual combat. The earlier absence of a process was an unresolved launch state,
not evidence of a crash: the pending Steam confirmation explains the delay.
The agent did not automate the dialog or issue another launch. File-2 identity
has user confirmation and a fresh Continue, 2 log entry, not automatic slot attestation.
This remains an ordinary profile, not training isolation.

Session: 14586c2d711547c9b2899efd99c9b98b; game epoch 1.
Snapshots 1..530 cover frames 419963..422765, updates 2462..5264 and room visits
13..28. Status counts: 464 active, 66 paused. All four entity kinds appeared;
all 530 entity frames reported source overflow, so this is a bounded subset.
Last snapshot was paused with zero red/soul/bone health; that alone is not a
validated terminal outcome.

Diagnostic counts: attach 1, post_update 558, damage_attempt 107,
post_update_hp 106, npc_update_hp 124, entity_kill 20, entity_remove 33,
npc_death 19, clean_award 5, npc_init 35, new_room 15, stop 1.
All 106 post samples had status=sampled; three carried init=true, and the largest
coalesced attempt count was two. Removed/missing/identity_changed statuses and
16-target overflow were not observed live; their offline tests remain separate.

### Counterexample: first post-update still precedes changed HP

Room 13, diagnostic label 1, type 254 variant 0:

| Record | Callback | Frame/update | Raw HP |
|---|---|---|---|
| 7 | damage_attempt; requested=3.8935041427612 | 419989 / 2487 | 0.53247833251953 |
| 8 | post_update_hp; queued update=2487 | 419989 / 2488 | 0.53247833251953 |
| 10 | npc_update_hp | 419990 / 2488 | 0.53247833251953 |
| 11 | entity_kill | 419990 / 2488 | -3.3610258102417 |
| 13, 14 | entity_remove, npc_death | 419991 / 2489 | -3.3610258102417 |

The first observer post-update sample can occur in the same game frame as the
attempt and before a later changed-HP fact. The update-counter increment is not
a completed-damage guarantee. Local labels are diagnostic correlations, not
verified spawn generations; no per-hit applied amount or source is inferred.

Diagnostics stopped at their count limit before game over. Subsequently the game
log recorded Game Over, then Game exited; observer closed, then a New, 2 run.
The process remained alive. The client received PeerDisconnected and closed its
socket/listener through its context manager. No action, restart, reset or reconnect
was sent; the origin of the later new-run input is not independently established.
Do not count this as automatic-restart acceptance or diagnostic death coverage.
All 558 diagnostic dead flags were false; the diagnostic window had already ended.

Private evidence, excluded by reports/local/: post-update-hp-runtime-20261018-12236.jsonl,
post-update-hp-diagnostic-20261018-12236.log and post-update-hp-summary-20261018-12236.json.
No raw log, save, backup or approval is committed.

Installed/source SHA256 after capture:

- main.lua: 9e720026da0bea6ddc7e2f51c1d11683e6807c85568ed31fa859f81932ecac45.
- metadata.xml: 085c10c2a14de0ef7600dcd8195621079e9843dcca3572df1902b66ee98e78b1.

## RL evaluation

Not applicable. No model, reward, training, progression or achievement claim.

## Limitations, self-review and continuation

Explicit live negotiation and raw deferred sampling are verified narrowly.
The full observation duration failed; no fault is converted into a transition.
Sampling is useful evidence, not a universal engine/other-mod completion barrier.
Self-review compared saved record IDs, queued context, callback HP, wire snapshots,
budgets and installed hashes against the active specification; no runtime task
was checked off from this partial coverage. No source change or archive.

12/19 whole episode-lifecycle tasks remain accepted. Death/revival/floor coverage,
actual step application and completion, event emitter and isolated start/reset
are unfinished. Next offline work should define and test later-frame bounded
settlement observations and unavailable/transition semantics before another
operator-directed runtime check; do not merely rename first-post-update HP as
realized damage. No further diagnostic attach in this mod load.
