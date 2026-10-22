## Context

Combat policy v1 has no weapon range. Missing enemies are not verified kills.
Management navigation is excluded from learning. Preserve those boundaries and
the stopped t21760 checkpoint; do not launch training for this change.

## Goals / Non-Goals

Capture the actual encoder vector returned by the environment and its matching raw snapshot,
plus the selected action and resulting vector/snapshot. Detect sustained absence
of conservatively registered damage without pretending it proves zero real damage.
Do not implement a scripted combat controller or modify rewards/normalization.

## Decisions

The gate owns optional diagnostic state across Gym resets. A version-1 policy
JSONL contains only encoded observations, selected actions, identity, clipping,
overflow, fault labels and transition flags. These are pre-VecNormalize inputs,
not the network's normalized vector or recurrent state. A separate oracle JSONL
contains raw snapshots.
They share monotonically increasing record IDs; incomplete pairs after I/O failure
are unusable. Exclusive creation prevents overwriting evidence. Combined bytes
are capped explicitly; capacity exhaustion arms a clean stop before another action.
Never silently continue with incomplete requested diagnostics. Weapon range is
explicitly unavailable in diagnostic metadata, rather than guessed.

The progress monitor uses the existing conservative EventDeriver at captured
endpoints. It retains HP floors and accumulated active frame deltas across software
resets; resets rebaseline membership without renewing the accumulated window.
Only same-visit eligible combat action spans count, never management waits/reset
frame gaps. Namespace/room changes start a new window. Damage below the historical
floor or a verified clear resets it; healing, disappearance, empty shooting,
movement and spawn baselines do not. Endpoints are partial coverage. The stop
reason says registered progress, not zero actual damage or a gameplay outcome.

An armed stop is checked before reset/step, releases input and raises a distinct
LiveBudgetExpired subtype through existing orderly run cleanup. The last real
transition returns normally from the gate. SB3 auto-reset may raise before storing
that sample; decision/checkpoint/unsaved accounting includes it as unsaved.
No fake death, clear, fault, terminal transition, restart or new run is generated.
Options default off and are explicit in the finite session plan. Byte limits and
window do not replace wall-time/resource/focus/fault/lineage guards.

## Risks / Trade-offs

Partial HP coverage can stop a genuinely active fight. Therefore the window is an
explicit experiment setting and native qualification must precede reliance on it.
Encoded policy inputs can reference an earlier frame than the backend's eventual
command after queue draining; the trace labels selected actions, not accepted
actions. It does not claim action acknowledgements or full trajectory equivalence.
Trace I/O errors fail the run; a trailing unpaired record is rejected by consumers.

## Validation

Behavioral tests cover byte caps, oracle isolation, same-frame pairing, software
resets, HP healing/disappearance/overflow, room changes, stop-before-next-action,
real transition preservation and explicit option plumbing. Run the full Windows
gate. A later bounded native five-minute capture qualifies identity and cleanup;
15-30 minutes and longer training require separate experiment evidence.
