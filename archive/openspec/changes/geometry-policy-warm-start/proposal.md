## Why
Qualified723-input geometry cannot be used by preserved649-input checkpoints.
The user requested launch; require an explicit separate compatible lineage before
one finite five-minute pilot, retaining all original artifacts.
## What Changes
- Explicit conservative-v2 t21760 -> geometry schema2/live-firing-v4 warm start.
- Copy existing parameters and Adam moments; zero74 new input columns/moments.
- Preserve prefix observation statistics/count and reward statistics; new feature
  mean0/variance1 is an explicit neutral prior sharing inherited RMS count.
- Verify recurrent action/value equivalence before learning, preserve RNG/update
  counters and save lineage; no automatic conversion on ordinary resume.
- One Continue/file2 pilot,300s inclusive startup,2GiB,128MiB trace,zero retries or
  infrastructure faults,max10 natural death restarts,first9000 no-progress updates
  stop. No New Run or longer-stage escalation. Report damage/taken/clears separately.
## Capabilities
### New Capabilities
- `geometry-policy-warm-start`: explicit shape migration with lineage/equivalence.
### Modified Capabilities
None.
## Impact
Small offline migration primitives,tests,new configuration,local explicit transfer
and finite runtime assignment. No other reward/observation/optimizer tuning.
