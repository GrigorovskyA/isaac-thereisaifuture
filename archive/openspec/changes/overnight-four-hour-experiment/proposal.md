## Why
The user requested a diagnostic damage baseline followed by four hours of continued learning, with no practical step/death/restart count stop. Preserve the existing algorithm, reward and learned state.

## What Changes
- Add an explicitly scripted, observation-only obstacle-aware comparator for a finite native damage check.
- Add a budget-only four-hour continuation configuration and explicit artifact lineage migration from t6912.
- Prepare one time-bounded native training command with no death limit, a nonbinding step/restart sentinel, checkpoint evidence and cleanup.

## Capabilities
### New Capabilities
- `timed-continuation`: explicit budget lineage and time-dominant continued learning.
### Modified Capabilities
None.

## Impact
No learning/reward/observation/transport behavior changes. All new diagnostic comparator behavior is separate from the learned policy. No save edits or artificial unlocks. Runtime evidence remains incomplete until executed.
