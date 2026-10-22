# Collection freshness across optimizer/checkpoint work

Gated live training records the `live-segment-refresh-v1` collection contract.
The transport can drain recent snapshots yet still act on an older cached actor
input. Refreshing only the command reference does not fix that mismatch.

At each completed rollout, the SB3 rollout-end callback releases input through
`CombatGateEnv.end_collection_segment`. Returns/advantages have already been
computed from the completed trajectory; they are not modified. The gate blocks
further actions until reset. Optimization and checkpoint publication then run.

Before the next rollout, the trainer calls public
`model.set_env(existing_vec_normalize, force_reset=True)`. SB3's regular setup
resets the gate and VecNormalize, reacquires a current eligible frame, updates
observation statistics once, refreshes raw/normalized caches and sets the next
recurrent episode-start mask. No private cache or LSTM state is rewritten.
The policy uses the same normalized input that is stored in its rollout buffer.

This starts a collection segment within the existing native game run. It does
not request New Run, a death restart, or new model weights. Unobserved game time
is explicitly an unknown gap: no invented action, reward, terminal result or
sample. Previous bootstrap values remain attached to the old end observation;
the next segment's LSTM mask prevents a false recurrent connection across idle
frames. Room novelty/damage identity histories and no-progress history persist.

Logs include `collection_contract`, `collection_segment_suspended`,
`collection_refresh_scheduled`, and gate events `collection_segment_ended` /
`collection_refreshed`. The latter bind old/new frame identities and idle duration.
They are diagnostics and never policy features. Failed/rejected release, gate
reset, deadline or refresh does not fall back to old-input inference.

The trainer's `refresh_between_rollouts` argument defaults to false for generic
synthetic use. Gated live training enables it; ungated live training is outside
this contract. This changes collection segmentation, not reward or observation
schemas. Any future live experiment must record the contract and checkpoint
lineage explicitly. Existing models/normalizers are not migrated here.

Limitations: recurrent memory is intentionally bounded by collection segments,
and within-rollout inference delays remain possible. Frozen-delay native checks
and synthetic optimizer tests do not establish better play or all real optimizer
latencies. Do not automatically resume learning or escalate duration from a pass.

## Qualification

The finite frozen native audit passed three36-frame idle gaps; first post-refresh
commands lagged0/0/1 frame and all278 native action joins were within1 frame.
Actual PPO/RecurrentPPO accounting and setup-journal failure cleanup passed final
149 targeted/2292 full tests,51 strict items and synthetic CPU smoke. Native did
not optimize or learn. See the
[combined evidence](../reports/2026-10-21-native-fresh-rollout-observations.md).
