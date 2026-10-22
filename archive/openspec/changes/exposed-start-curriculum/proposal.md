# Proposal

## Why

The latest v5 pilot spent 97.16% of its decisions near a corner and supplied
almost no clear firing experience. A scripted control has now established a
reachable exposed position, three-frame firing and actual target damage without
player health loss; this makes a small curriculum experiment worth testing.

## What Changes

- Add an opt-in, unscored positioning phase before the first learning sample.
  Use the qualified short movement/braking controller, then require a fresh,
  visible clear, aligned, in-range ordinary-tear opportunity before handoff.
  Allow a command-free initial visibility wait, bounded inside setup, when
  compatible oracle combat is available before visible enemies appear.
- Create a separate child run from exact checkpoint a0a93c29-s20-t26368 while
  preserving its model, Adam state, normalizer, RNG and immutable parents.
- Prepare one five-minute total pilot: up to 180 seconds of learning, followed
  when feasible by bounded frozen-parent and frozen-child observations.
- Report damage dealt/taken, clears, deaths, exposure and stagnation per phase.
  Continue does not restore identical world states: native comparisons here are
  observational, not paired causal or held-out improvement evidence.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `combat-experience-gate`: explicit unscored setup and fresh collector handoff.
- `rl-evaluation`: phase-separated curriculum evidence and honest comparability.

## Impact

Expected implementation: a bounded setup helper and opt-in runner/factory seam
around `live._train_run`, `LiveBackend`, `train`, `CheckpointPolicy` and the combat
gate; focused tests and an experiment plan. Existing default modes, Lua/wire,
schema 2/723, three-frame learned actions, live-firing-v5 reward coefficients and
PPO hyperparameters remain unchanged. No new dependencies or hidden policy data.

Dependencies: accepted mixed-control evidence at 743a655, current runtime authority,
fresh file-2 Continue and a compatible room. No new Isaac APIs are needed;
unverified facts are runtime state availability, phase handoff freshness and
whether learned actions actually exploit the exposed start.

Acceptance requires zero setup samples/normalizer updates/reward credit; correct
stale/death/deadline refusal; exact child readback; and native learner damage plus
at least one completed optimizer update and reloadable checkpoint. If the bounded
pilot cannot supply those facts, its native task remains unfinished. Better-play
promotion additionally needs future controlled multi-seed evaluation.

Non-goals: reward tuning, action masks, imitation training, save/Cloud changes,
New Run, death resets, automatic duration escalation or claiming that setup
success proves learned improvement. This change is a prepared proposal only.
