## Context

See reports/2026-10-20-live-reward-diagnosis.md. Current Lua gives bounded current
active membership,not reliable lifetime death events. No new native API is assumed.

## Goals / Non-Goals

Correct absence rewards and software-reset farming in the Python live adapter.
No native death callback, campaign-wide accounting, warm-start conversion or new
training. Keep t8960 and navigation work unchanged. Native acceptance is separate.

## Decisions

- EventDeriver keeps current membership plus at most4096 (max_hp,lowest_hp) records
  scoped by session/epoch. Room/software boundaries rebaseline membership; a reset
  still emits spawn baselines for the segment-local RewardLedger. Only new lows in
  continuous complete membership emit damage. Rebaselines silently lower floors;
  max-HP mutation closes further credit. Do not infer kills from absent enemies.
- Do not evict history to make room; exhaustion raises a bounded explicit fault.
  New namespaces clear history. Player health/death and clear handling retain their
  existing conservative coverage semantics. No oracle floor enters observations.
- Add manifest reward_contract literal with legacy default combat-v1. Training
  always checks its expected contract before environment construction and saves it.
  Live passes live-conservative-v2; synthetic/default training remains combat-v1.
  Existing wire reward_schema_version stays1 because event payloads are unchanged;
  the additional contract versions accounting semantics. Frozen loading can read
  either declared contract because it does not calculate reward.

## Risks / Trade-offs

Kill bonuses are intentionally unavailable without evidence; fewer HP credits are
possible across gaps. Identity continuity depends on the bridge namespace. Room
re-entry may assign new IDs; cross-visit physical lineage is not established and
must not be advertised as campaign-wide anti-farming. No clean-baseline or warm-
start decision is made here. A separate explicit migration would be needed for
t8960; failing resume cannot silently initialize another model.

## Migration Plan

No artifacts are rewritten. Old checkpoints remain readable for frozen diagnosis.
Live resume fails with the two contract names. Native verification needs a newly
budgeted check after offline acceptance; keep this change unarchived until required
runtime evidence is recorded or explicitly accepted as an offline-only contract.
