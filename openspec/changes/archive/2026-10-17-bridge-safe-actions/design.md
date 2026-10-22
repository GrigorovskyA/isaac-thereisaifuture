# Design

## Context

See proposal.md. Observer 0.2.0 has bounded transport and an accepted opt-in death
restart. No active-slot API or verified isolated profile is established. The new
adapter is 0.3.0. Following user-confirmed normal exit and installation approval,
it was passively deployed with the action gate nil; previous 0.2.0 bytes were
backed up. Runtime acceptance remains pending.

## Goals / Non-Goals

Implement only the bounded native command slice and offline evidence. No launch,
selection, save writes, reset extension, controller policy or supervision.

## Decisions

- Extend protocol/schema 1 with optional safe_actions_v1 and action-specific
  command/ack models. Old default peers retain identical snapshot fields. Lua
  denies post-hello requests unless actions were negotiated and the ack fully sent.
- Use MC_INPUT_ACTION with native ButtonAction/InputHook enums, for player 0 only.
  GET_ACTION_VALUE returns 0/1; IS_ACTION_PRESSED returns boolean; TRIGGERED is false
  (continuous movement/shooting need no edge actions). Other inputs/entities return
  nil. Release returns nil for all hooks, preserving manual control. Neutral
  overrides the eight action buttons with zero for a bounded action interval.
- Local Config.action_authorization is nil in committed source. An eventual
  reviewed record must provide profile_id, isolation_evidence, slot_evidence,
  runtime_authorization, slot=2 and game_epoch. Python requests capability but
  cannot populate that record. This is an operator evidence gate, not automatic
  proof of save isolation or slot identity. Epoch change invalidates it.
- Require exact canonical JSON field order from the Python serializer, using the
  existing conservative strategy for the shipped permissive decoder. Bound command
  lines to 1024 bytes, process at most one per render callback, disconnect on excess
  backlog, unknown fields, stale/replayed/incompatible commands. Close clears holds.
- Each command binds fresh session, increasing sequence, epoch, room visit and
  last sent snapshot frame; current frame must be within [frame, frame+15]. Limit
  action lifetime to 1..15 frames, hard 250 ms; heartbeat lease 500 ms. Heartbeat
  refresh does not refresh a hold. No automatic heartbeat thread or action replay.
- Ack reports acceptance frame and command identity, not physical application.
  A dedicated Python ActionClient serializes transactions, validates snapshots and
  ack identities, and closes on errors. No action CLI or launcher mode while live
  prerequisites remain blocked. Use the attach-only API after authorization.
- Watchdog runs on render, update and input callbacks; pcall failure returns nil
  and closes. Clear on pause/death/co-op/unavailable state and every transition.
  Clock expiry is checked before an input override, including after callback gaps.
  Under a suspended game process no code executes; wall time limits mean no stale
  override on the next callback, not a hard OS scheduling guarantee.

## Risks / Trade-offs

Native callback semantics and real effects remain unverified on J460. Documentation
and the shipped enum/source inspection establish API shape only. Actual shots
need a runtime evidence extension/probe, not inferred success from input values.
Strict framing/order sacrifices generic JSON clients for unambiguous rejection.
15-frame freshness can reject slow consumers; fail closed instead of widening it.
Separate profile/slot authorization cannot be fabricated from a second save slot,
a backup, file timestamps, a seed, or the current observer handshake.

## Migration Plan

Passive deployment with the action gate disabled is recorded in the deployment
evidence; it does not authorize control. For enabling actions, after approved
isolation/restore/write-set verification and
slot/instance evidence, prepare exact artifact hashes and local authorization;
obtain specific runtime permission, normally close game, back up adapter only,
deploy reviewed bytes, launch/select manually and attach without resetting.
Rollback with game closed restores previous adapter bytes only. Never overwrite
saves/options or alter Cloud to perform this change. Existing restart caps remain
three attempts/ten minutes. Keep change active until every declared live test passes.

## Approved ordinary-profile amendment (2026-10-17)

The latest direct user instruction permits bounded movement/shooting tests on
the ordinary profile and persistent permission for future checks. Use an explicit
ordinary_profile_exception mode and profile_evidence reference; never fabricate
isolation evidence. Keep slot/instance confirmation manual and required before
live control. Source authority remains nil; an optional private JSON record in
the installed observer directory is loaded once with bounded size, 30-minute
wall expiry and a nonrenewable 120-second action lease per mod load. Default
observer peers still cannot act. Native diagnostics correlate commands, release
and actual player tears. No runtime arbitrary code endpoint is introduced.

## Accepted runtime command pattern

The real J460 preliminary combined probe verified actual movement and player tears.
Because three refreshed movement holds displaced ~150 room units, the accepted
50-case probe uses one two-frame movement pulse. Additional shooting refreshes
use movement none. Each case ends neutral/release and preserves room/epoch/health.
All 50 physical cases and three cleanup faults passed; operator manual control
was confirmed. See reports/2026-10-17-safe-actions-runtime.md for exact evidence.
