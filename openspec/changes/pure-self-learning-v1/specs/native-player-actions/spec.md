## REMOVED Requirements

### Requirement: Opt-in firing callback values
**Reason**: Firing diagnostics belonged to the hinted direction and were removed from the Lua observer.
**Migration**: None; the pre-trim mod is preserved in `archive/mod/main.pre-pure.lua`.

### Requirement: Sparse firing diagnostic mode
**Reason**: Firing diagnostics belonged to the hinted direction and were removed from the Lua observer.
**Migration**: None; the pre-trim mod is preserved in `archive/mod/main.pre-pure.lua`.

### Requirement: Diagnostic gameplay independence
**Reason**: No gameplay diagnostics remain in the observer.
**Migration**: None.

### Requirement: Empty-room firing preflight
**Reason**: The firing preflight served the removed combat gate.
**Migration**: None.

### Requirement: Bounded stationary cadence comparison
**Reason**: The cadence comparison served removed firing diagnostics.
**Migration**: None.
