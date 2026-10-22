## Decisions
Use preserved v2t21760 rather than v3t24064 trained under the defective objective.
RecurrentPPO input expands649->723 only in actor/critic LSTM weight_ih_l0. Copy
old columns exactly and append zeros. Reject other parameter/layout/shape changes.
Copy Adam groups and scalar step; expand the matching moment columns with zeros.
All other weights/moments/RNG/update/timestep counters stay intact. New feature
columns can learn from nonzero observations after the pilot starts.

Clone VecNormalize with unchanged649 prefix mean/variance,scalar count and reward
statistics. Append mean0/variance1,an explicitly declared neutral prior with the
inherited shared scalar count,not measured historical feature data. Clear transient
raw observation/returns at a new collector boundary. Prefix normalization and
initial actor/value outputs must match for arbitrary74 extensions over recurrent
sequences. No runtime oracle features or migration of hidden state is permitted.

Use a new root/config hash,manifest observation2,reward live-firing-v4 and original
parent ID. Ordinary mismatch resume remains rejected. Save/publish only after
checks and record original file hashes and explicit external objective transition.
Initial policy behavior should remain unchanged; a warm start is not learned use
of geometry. A single seed/five-minute pilot is exploratory,not model selection.

## Validation and risks
Use actual trained synthetic RecurrentPPO with saved optimizer state; compare
weights,moments,prefix normalization,deterministic actions/value distributions and
RNG/counters,then save/load/resume723 and reject649. Native pilot records exact
source/config/lineage/deadline/disk/cleanup and all outcomes. Sparse near-corner
reward support and inherited neutral-prior RMS count may slow adaptation; no
claim of cure. No automatic15-30min/hour/four-hour escalation.
