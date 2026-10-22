## Decisions
Installed SB3 collect_rollouts invokes on_rollout_end after return/advantage
computation and before optimizer training. Release gated input at this callback;
do not modify completed rollout observations, values, rewards or terminal flags.
After optimization and checkpoint work, before the next learn chunk, use public
model.set_env(existing_vec_env, force_reset=True). SB3 setup then calls the actual
VecNormalize.reset once, refreshes original/normalized caches and sets all next
episode_starts true. Recurrent state is reset by the normal policy episode-start
mask; do not rewrite private LSTM/cache fields or silently normalize cached data.

Reset here starts a software collection segment, not a new native game run. Gate
reset reacquires live combat eligibility and backend.start_episode drains to the
latest playable frame, rebases event accounting, and refreshes trace provenance.
Persist physical-room reward records and no-progress history as already designed.
The previous rollout keeps its valid end-observation bootstrap; the unknown idle
gap is not connected to the next rollout's recurrent episode or rewarded action.

Record collector contract live-segment-refresh-v1, segment-end old identity,
steps/return, and the next segment's old/new frame identities and gap duration.
Gaps are neither transitions nor successful/dead episodes. Do not update any
step/death/clear counter for the gap. Existing TTL expiry remains a second guard.
Deadline, gate, release and reset failures stop normally without fallback inference.
Use a training opt-in wired on for gated live training, off for generic/synthetic
training. Frozen native checks must explicitly invoke the same boundary mechanism;
no new model, optimizer update or automatic duration escalation is authorized.

## Validation and limitations
Use installed actual PPO/RecurrentPPO with a changing synthetic environment to
verify first post-update actor input, normalized/original buffer equality, exact
RMS counts, episode-start mask/LSTM behavior and unchanged cumulative samples.
Test queued live movement/HP/room changes during an idle gap through the real gate
stack, honest reward baselines, trace identity, failure/deadline and release.
A finite native frozen-delay check qualifies collection boundaries only; optimizer
latency and play quality cannot be claimed from frozen or synthetic evidence.
Extra software segment resets bound LSTM memory to rollout lengths intentionally.
Within-rollout inference latency is not eliminated by this boundary remedy.
