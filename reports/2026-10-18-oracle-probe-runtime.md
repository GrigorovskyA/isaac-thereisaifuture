# Evidence: passive oracle probe runtime, partial coverage

- Date/time and timezone: 2026-10-18, Europe/Amsterdam.
- Git revision: 30adaa3; no code changes during recording. Unrelated errors.txt preserved.
- Scope: one bounded read-only callback probe; subsequent user-requested read-only entity recording does not renew the diagnostic budget.
- Game/mod: manually launched J460, PID 24956; observer 0.4.2-dev, oracle_probe=true, callback_trace=false, no private action approval.
- Runtime: existing CPython 3.12.14 and validated ObservationClient; no dependency changes.
- Configuration: accept 8 s, handshake/message 3 s, no reconnect, at most 600 samples and 120 s from client start (one bounded receive may finish after the loop deadline).

## Results

| Requirement/check | Command/scenario | Exit code | Status | Evidence |
|---|---|---|---|---|
| Compatible read-only attach | ObservationClient(ObserverConfig(accept_timeout=8, handshake_timeout=3, message_timeout=3)); accept; receive loop; context close | 0 | passed | 0.4.2-dev hello, 596 active snapshots, 120.125 s |
| Bounded diagnostic sequence | Filter current-session OracleProbe lines, check contiguous IDs/byte limits | 0 | passed | 599 records: attach 1, post_update 597, stop 1; maximum 214 bytes |
| Stop on client disconnect | Read-only context closes without reconnect | 0 | passed | Final diagnostic stop reason=disconnect |
| Damage/kill/clear/death/revival/transition ordering | Actual callbacks during manual play | N/A | not_run | No such candidate callbacks occurred in the diagnostic window |
| Additional bounded entity recording | Second 120 s read loop, entity_observations=True, no reconnect | 0 | passed | 595 validated entity snapshots; details below |
| Diagnostic reconnect exhaustion | Filter second-session OracleProbe records | 0 | passed | Zero records after reconnect; first window was not renewed |
| Cleanup to default-off | User normal exit, restore source hashes; Start-Isaac.cmd --preflight-only | 0 | passed | Both source/installed hashes match; no process launched |
| Strict project validation | ./scripts/OpenSpec.ps1 validate --all --strict | 0 | passed | 24/24 items; implementation code unchanged from the 894-test gate |

## Real game

The operator reported being in a room after the manual file-2/Continue procedure.
Automatic active-slot attestation remains unavailable. This read-only run did not
establish isolation or exercise action authority. No movement, shooting, reset,
restart or launch command was sent by the agent. The game remained running
through both captures and was later closed normally by the operator.

Session: 1cba23bb42104d6c940361b696fe0ff3, epoch 1, room visit 0.
Snapshots advanced from frame 402367 to 405949. One unique player position and
one health state were recorded; no pause/unavailable snapshot was observed.
Diagnostic records ran from frame 402366/update 1402 to frame 405950/update 4986;
their timestamp span was 119471 ms. IDs 1..599 were contiguous. Every sampled
dead value was false. This validates basic attach/read/stop behavior only.

No damage, NPC init/update/kill/remove/death, clean-award, game-end or transition
callback appeared in that window. Do not count their absence as callback support
or event correctness. No policy transition or native step completion was accepted.

Private evidence (ignored, not committed):
reports/local/oracle-runtime-20261018-24956.jsonl,
reports/local/oracle-diagnostic-20261018-24956.log and
reports/local/oracle-summary-20261018-24956.json.
Only current-session diagnostic lines were extracted; the whole game log stays private.

### User-requested additional two minutes

Session 25a194e56bf646c88a7ad33d4df77ee8, same process and epoch 1. An explicit
read-only entity attach captured 595 snapshots in 120.110 s: 563 active and 32
paused, none unavailable. Frames 407456..410836 covered 21 room visits (11..31),
574 unique player positions and ten raw health states. All four visible kinds
were present. Repeated entity appearances across frames totalled 552 enemy,
523 projectile, 439 pickup and 7140 obstacle observations; these are not counts
of distinct enemies, kills, spawns or reward events. At most 32 entities appeared
per frame; all 595 frames reported source overflow, so coverage is a bounded
subset, not a complete world inventory.

The client validated each EntitySnapshot through the existing strict decoder.
Zero OracleProbe records used this second session ID: reconnect did not renew
the exhausted callback window. Position/health/room changes and visible combat
do not establish attempted-versus-applied damage, death/revival, callback order,
terminal steps or outcome attribution. Do not substitute this second recording
for the missing diagnostic scenario coverage.

Additional ignored evidence: reports/local/oracle-followup-entities-20261018-24956.jsonl
and reports/local/oracle-followup-summary-20261018-24956.json.

### Final cleanup

The operator confirmed normal closure. Process absence and the installed
diagnostic hash were checked before copying only reviewed main.lua/metadata.xml.
No action approval existed. Restored hashes:

- main.lua: c20f8164b0b621510011139baa86bc429872c94bc8fb2db25a4c46073e54b2a3.
- metadata.xml: 05a108ceb4149fb80c55a2b32e21a47c4f186b61092dee7c2a9d5b37ab449262.

Both match source (oracle_probe=false, callback_trace=false). Launcher preflight
returned 0 without launching anything. Saves, Cloud, other mods, options, restart
limits and action authority were unchanged. Private backups are preserved.

## RL evaluation

Not applicable; no training, model, reward or achievement evaluation.

## Limitations and continuation

Item 05 remains 12/19; no runtime task or archive acceptance is claimed. The
nonrenewable probe is exhausted in this mod load. A later socket can read normal
state/entities but cannot collect more callback diagnostics, as the explicit
second capture above confirms. No whole runtime task is newly marked complete.

Default-off cleanup and preflight passed. A future callback-ordering run requires
manual normal restart and a newly reviewed bounded window; never force scenarios/reset
or silently extend the diagnostic lease. Self-review distinguishes active frame
progress from event coverage and keeps all absent scenarios unaccepted.
