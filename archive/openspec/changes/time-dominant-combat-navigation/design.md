# Design

## Context

See proposal.md and the readiness plan item 2. Current metadata includes current
room index, stage/type, open ordinary doors and measured geometry, without trusted
target room indices. Existing bounded pulses and gate cleanup remain authoritative.

## Goals / Non-Goals

Offer explicit finite-window navigation and stop observed loops. Keep the default
diagnostic mode and learner semantics. Do not implement boss/floor progression,
New Run, model migration, new telemetry, save changes or native qualification.

## Decisions

- Store bounded directed `(current room, door slot) -> observed destination`
  connections only after an accepted pulse and fresh room-visit transition.
  No opposite-door inference, target-index arithmetic or hidden map reads.
- Track the latest actually observed eligible door set per room. Prefer a reachable
  untraversed local door; otherwise breadth-first search confirmed directed edges
  to a room with an observed untraversed exit. Filter the first hop by its current
  measured path. Re-evaluate after each transition; never issue a whole path blind.
  Remember last measured reachable exits in each visited room so two blocked
  frontiers cannot repeatedly attract the search to each other. Actual revisits
  remeasure paths and changed observed door sets invalidate the cached result.
  Apply those measured constraints to intermediate confirmed edges as well, so
  two known blocked routes cannot sustain a cycle toward another frontier.
- When no frontier exists, report observed-component exhaustion. If frontiers
  exist but no confirmed route/current measured path reaches one, report unreachable
  frontier. These statements concern only observed eligible ordinary exits.
- Reset memory on session/epoch/stage/type changes. Retain it across handoffs on
  the same floor, including combat rooms, so returning through cleared rooms works.
- Add an opt-in Boolean to live options, CLI and finite session plan. Reject mixed
  time mode plus scaled diagnostic counters to keep the budget contract explicit.
  Use the declared finite window as gate wait cap, always narrowed by run deadline.
  Retain cumulative counters as telemetry only in this mode.
- Existing bounded mode retains routing behavior and cumulative limits. Both modes
  retain per-pulse <=0.8s, measured <=6-frame actions, release/reconciliation,
  stationary, health, same-instance and fresh-frame guards.

## Risks / Trade-offs

- Directed observations may lack a reverse connection: stop honestly rather than
  inventing one. Dynamic doors are refreshed only on actual revisits.
- Ordinary exits may not lead to further combat: stop without reset. Full-floor
  coverage, unlocks and improved play are not inferred.
- Offline travel and learning-separation tests cannot establish native door timing;
  keep native qualification pending and do not archive this change.
